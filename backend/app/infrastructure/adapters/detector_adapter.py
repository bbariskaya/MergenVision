"""SCRFD batched face detector adapter using TensorRT and torch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings
from app.core.errors import EngineNotFoundError
from app.infrastructure.adapters.base import Detection, DetectionBatch
from app.infrastructure.adapters.trt_session import TrtInferenceSession
from app.infrastructure.model_registry import ModelRegistry, get_model_registry

if TYPE_CHECKING:
    import torch


class DetectorAdapter:
    """SCRFD detector wrapping a TensorRT engine and decoding outputs on GPU."""

    _STRIDES = (8, 16, 32)
    _NUM_ANCHORS = 2
    _NUM_KEYPOINTS = 5
    _INPUT_SIZE = 320

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._registry = registry or get_model_registry(self._settings)
        self._model_info = self._registry.get_detector()
        self._sessions: dict[int, TrtInferenceSession] = {}
        self._confidence_threshold = self._settings.detector_confidence_threshold
        self._nms_threshold = self._settings.detector_nms_threshold

    @property
    def name(self) -> str:
        return self._model_info.name

    @property
    def version(self) -> str:
        return self._model_info.version

    @property
    def input_size(self) -> int:
        return self._model_info.input_size or self._INPUT_SIZE

    def _select_batch_size(self, n: int) -> int:
        for size in self._settings.trt_batch_profiles:
            if size >= n:
                return size
        return max(self._settings.trt_batch_profiles)

    def _get_session(self, batch_size: int) -> TrtInferenceSession:
        if batch_size not in self._sessions:
            try:
                path = self._registry.trt_engine_path(self._model_info, batch_size)
            except EngineNotFoundError:
                available = sorted(
                    int(p.stem.split("_batch_")[-1])
                    for p in self._settings.trt_engine_dir.glob("*.plan")
                    if self._model_info.name in p.name
                )
                if not available:
                    raise
                fallback = min(s for s in available if s >= batch_size)
                path = self._registry.trt_engine_path(self._model_info, fallback)
            self._sessions[batch_size] = TrtInferenceSession(path)
        return self._sessions[batch_size]

    def detect_batch(
        self,
        images: torch.Tensor,
        original_sizes: list[tuple[int, int]] | None = None,
    ) -> DetectionBatch:
        """Detect faces in a [N,3,H,W] tensor.

        Bboxes/landmarks are returned in the original image coordinate space when
        ``original_sizes`` is provided; otherwise in the 320x320 model space.
        """
        import torch

        n = images.shape[0]
        if n == 0:
            return DetectionBatch(image_count=0)

        if images.shape[2] != self.input_size or images.shape[3] != self.input_size:
            raise ValueError(
                f"Detector expects {self.input_size}x{self.input_size} input, "
                f"got {images.shape[2]}x{images.shape[3]}"
            )

        batch_size = self._select_batch_size(n)
        session = self._get_session(batch_size)

        if n < batch_size:
            padding = torch.zeros(
                (batch_size - n, *images.shape[1:]),
                dtype=images.dtype,
                device=images.device,
            )
            padded = torch.cat([images, padding], dim=0)
        else:
            padded = images

        outputs = session.infer(padded)
        return self._decode_outputs(outputs, n, original_sizes)

    def _decode_outputs(
        self,
        outputs: list,
        batch_count: int,
        original_sizes: list[tuple[int, int]] | None,
    ) -> DetectionBatch:
        import torch
        import torchvision

        device = outputs[0].device if hasattr(outputs[0], "device") else torch.device("cpu")
        num_strides = len(self._STRIDES)
        image_detections: list[list[Detection]] = [[] for _ in range(batch_count)]

        for stride_index, stride in enumerate(self._STRIDES):
            scores_t = self._reshape_stride_output(outputs[stride_index], 1, stride, batch_count)
            bbox_t = self._reshape_stride_output(
                outputs[stride_index + num_strides], 4, stride, batch_count
            )
            kps_t = self._reshape_stride_output(
                outputs[stride_index + 2 * num_strides], 10, stride, batch_count
            )

            total_anchors = scores_t.shape[1]
            scores = scores_t.reshape(batch_count, total_anchors, -1)
            bboxes = bbox_t.reshape(batch_count, total_anchors, 4)
            kps = kps_t.reshape(batch_count, total_anchors, 10)

            centers = self._anchor_centers(stride, total_anchors, device)

            for image_index in range(batch_count):
                image_scores = scores[image_index, :, 0]
                positive = image_scores >= self._confidence_threshold
                if not positive.any():
                    continue

                indices = torch.nonzero(positive, as_tuple=False).view(-1)
                pos_scores = image_scores[indices]
                pos_bboxes = bboxes[image_index, indices] * stride
                pos_kps = kps[image_index, indices] * stride

                proposals = self._distance2bbox(centers[indices], pos_bboxes)
                landmarks = self._distance2kps(centers[indices], pos_kps).reshape(
                    -1, self._NUM_KEYPOINTS, 2
                )

                # Clamp to model input size BEFORE scaling back.
                proposals = torch.clamp(proposals, 0, self.input_size)
                landmarks = torch.clamp(landmarks, 0, self.input_size)

                # Scale back to original image size if requested.
                if original_sizes:
                    orig_h, orig_w = original_sizes[image_index]
                    scale = min(self.input_size / orig_h, self.input_size / orig_w)
                    proposals = proposals / scale
                    landmarks = landmarks / scale

                k = min(5000, indices.shape[0])
                if indices.shape[0] > k:
                    topk_scores, topk_idx = torch.topk(pos_scores, k)
                    proposals = proposals[topk_idx]
                    landmarks = landmarks[topk_idx]
                    pos_scores = topk_scores

                keep = torchvision.ops.nms(proposals, pos_scores, self._nms_threshold)
                for ki in keep:
                    bbox = tuple(float(v) for v in proposals[ki].tolist())
                    lms = [tuple(float(v) for v in lm) for lm in landmarks[ki].tolist()]
                    image_detections[image_index].append(
                        Detection(
                            image_index=image_index,
                            bbox=bbox,
                            score=float(pos_scores[ki].item()),
                            landmarks=lms,
                        )
                    )

        all_detections = [det for image_dets in image_detections for det in image_dets]
        return DetectionBatch(
            detections=tuple(all_detections),
            image_count=batch_count,
        )

    def _reshape_stride_output(
        self,
        tensor: torch.Tensor,
        channels_per_anchor: int,
        stride: int,
        batch_count: int,
    ) -> torch.Tensor:
        """Normalize a SCRFD stride output to [B, total_anchors, C]."""
        import torch

        if not isinstance(tensor, torch.Tensor):
            tensor = torch.from_numpy(tensor)

        grid_size = self.input_size // stride
        expected_total = grid_size * grid_size * self._NUM_ANCHORS
        expected_channels = self._NUM_ANCHORS * channels_per_anchor

        if tensor.dim() == 3:
            # Most common for batched ONNX: [B, total_anchors, C] or [B, total_anchors*C].
            if tensor.shape[1] == expected_total and tensor.shape[2] == channels_per_anchor:
                return tensor[:batch_count]
            if tensor.shape[2] == expected_total * channels_per_anchor:
                return tensor[:batch_count].reshape(
                    batch_count, expected_total, channels_per_anchor
                )
            if tensor.shape[1] == expected_total:
                return tensor[:batch_count].reshape(batch_count, expected_total, -1)
            raise ValueError(
                f"Unexpected 3D SCRFD output shape {tuple(tensor.shape)} for stride {stride}"
            )

        if tensor.dim() == 4:
            # [B, expected_channels, H, W] -> [B, A, C, H, W] -> [B, total, C].
            if (
                tensor.shape[2] == grid_size
                and tensor.shape[3] == grid_size
                and tensor.shape[1] == expected_channels
            ):
                t = tensor[:batch_count].reshape(
                    batch_count,
                    self._NUM_ANCHORS,
                    channels_per_anchor,
                    grid_size,
                    grid_size,
                )
                return t.permute(0, 3, 4, 1, 2).reshape(
                    batch_count, expected_total, channels_per_anchor
                )
            # [B, H, W, expected_channels] -> similar reshape.
            if (
                tensor.shape[1] == grid_size
                and tensor.shape[2] == grid_size
                and tensor.shape[3] == expected_channels
            ):
                t = tensor[:batch_count].reshape(
                    batch_count,
                    grid_size,
                    grid_size,
                    self._NUM_ANCHORS,
                    channels_per_anchor,
                )
                return t.reshape(batch_count, expected_total, channels_per_anchor)
            raise ValueError(
                f"Unexpected 4D SCRFD output shape {tuple(tensor.shape)} for stride {stride}"
            )

        raise ValueError(f"SCRFD output must be 3D or 4D, got {tensor.dim()}D")

    def _anchor_centers(
        self,
        stride: int,
        total_anchors: int,
        device: torch.device,
    ) -> torch.Tensor:
        import torch

        grid_size = self.input_size // stride
        expected = grid_size * grid_size * self._NUM_ANCHORS
        if total_anchors != expected:
            raise ValueError(
                f"Anchor count mismatch for stride {stride}: "
                f"expected {expected}, got {total_anchors}"
            )

        y = torch.arange(grid_size, dtype=torch.float32, device=device) * stride
        x = torch.arange(grid_size, dtype=torch.float32, device=device) * stride
        yy, xx = torch.meshgrid(y, x, indexing="ij")
        centers = torch.stack([xx, yy], dim=-1).reshape(-1, 2)
        if self._NUM_ANCHORS > 1:
            centers = centers.unsqueeze(1).expand(-1, self._NUM_ANCHORS, -1).reshape(-1, 2)
        return centers

    def _distance2bbox(
        self,
        centers: torch.Tensor,
        distances: torch.Tensor,
    ) -> torch.Tensor:
        import torch

        x1 = centers[:, 0] - distances[:, 0]
        y1 = centers[:, 1] - distances[:, 1]
        x2 = centers[:, 0] + distances[:, 2]
        y2 = centers[:, 1] + distances[:, 3]
        return torch.stack([x1, y1, x2, y2], dim=-1)

    def _distance2kps(
        self,
        centers: torch.Tensor,
        distances: torch.Tensor,
    ) -> torch.Tensor:
        import torch

        xs = centers[:, 0:1] + distances[:, 0::2]
        ys = centers[:, 1:2] + distances[:, 1::2]
        return torch.stack([xs, ys], dim=-1).reshape(centers.shape[0], -1)
