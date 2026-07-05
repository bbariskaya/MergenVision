"""GPU DALI-based batched image decoder with PIL fallback trigger."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


class GpuDaliDecoder:
    """Decode JPEG/PNG bytes on GPU using ``nvidia.dali``.

    Falls back via ``RuntimeError`` so callers can use ``GpuPilDecoder`` when
    DALI is unavailable or CUDA is not present.
    """

    def __init__(self, device_id: int = 0, input_size: int = 320) -> None:
        self._device_id = device_id
        self._input_size = input_size
        self._pipelines: dict[int, object] = {}

    def decode_batch(
        self,
        image_bytes_list: list[bytes],
    ) -> tuple[list[torch.Tensor], torch.Tensor]:
        """Decode a batch and return ``(originals, model_input)``.

        ``originals`` is a list of ``[3, H, W]`` float32 GPU tensors; each
        entry preserves its own decoded dimensions so variable-shape inputs do
        not collapse into a single stacked tensor. ``model_input`` is a uniform
        ``[N, 3, input_size, input_size]`` detector-ready tensor produced by
        DALI's resize + crop_mirror_normalize. If DALI cannot decode the batch,
        a ``RuntimeError`` is raised and ``FacePipeline`` falls back to the PIL
        path.
        """
        import torch

        if not image_bytes_list:
            empty_model = torch.empty(
                (0, 3, self._input_size, self._input_size),
                dtype=torch.float32,
            )
            return [], empty_model

        try:
            pipeline = self._get_pipeline(len(image_bytes_list))
        except Exception as exc:
            raise RuntimeError(f"DALI pipeline unavailable: {exc}") from exc

        try:
            import numpy as np

            source = [np.frombuffer(data, dtype=np.uint8) for data in image_bytes_list]
            pipeline.feed_input("source", source)
            original, model_input = pipeline.run()
            raw_originals = self._to_torch_list(original)
            originals = [t.permute(2, 0, 1).float() for t in raw_originals]
            model_input_t = self._to_torch(model_input)
        except Exception as exc:
            raise RuntimeError(f"DALI decode failed: {exc}") from exc

        return originals, model_input_t

    def _get_pipeline(self, batch_size: int) -> object:
        if batch_size not in self._pipelines:
            pipeline = self._build_pipeline(batch_size)
            pipeline.build()
            self._pipelines[batch_size] = pipeline
        return self._pipelines[batch_size]

    def _build_pipeline(self, batch_size: int) -> object:
        try:
            from nvidia.dali import fn, pipeline_def, types
        except Exception as exc:
            raise RuntimeError(f"nvidia.dali not installed: {exc}") from exc

        mean = [127.5, 127.5, 127.5]
        std = [128.0, 128.0, 128.0]

        @pipeline_def(
            batch_size=batch_size,
            num_threads=4,
            device_id=self._device_id,
            prefetch_queue_depth=1,
        )
        def pipe():
            source = fn.external_source(
                name="source",
                dtype=types.UINT8,
                parallel=False,
            )
            images = fn.decoders.image(
                source,
                device="mixed",
                output_type=types.RGB,
            )

            # `images` is returned as a list of [H, W, 3] uint8 GPU tensors.
            # The conversion to [3, H, W] float is done in torch so
            # variable-shape batches never need to be stacked.
            original = images

            resized = fn.resize(
                images,
                resize_x=self._input_size,
                resize_y=self._input_size,
            )
            model_input = fn.crop_mirror_normalize(
                resized,
                device="gpu",
                dtype=types.FLOAT,
                mean=mean,
                std=std,
            )

            return original, model_input

        return pipe()

    @staticmethod
    def _to_torch(tensor_list: object) -> torch.Tensor:
        """Convert a dense, uniform DALI TensorList to a torch tensor."""
        import torch.utils.dlpack as torch_dlpack

        # Dense TensorListGPU -> TensorGPU via ``as_tensor()``; the resulting
        # TensorGPU exposes the (standard) ``__dlpack__`` capsule.
        dense = tensor_list.as_tensor()
        return torch_dlpack.from_dlpack(dense.__dlpack__())

    @staticmethod
    def _to_torch_list(tensor_list: object) -> list[torch.Tensor]:
        """Convert a possibly variable-shape DALI TensorList to a list of tensors."""
        import torch
        import torch.utils.dlpack as torch_dlpack

        result = []
        for i in range(len(tensor_list)):
            sample = tensor_list[i]
            if hasattr(sample, "__dlpack__"):
                result.append(torch_dlpack.from_dlpack(sample.__dlpack__()))
            elif hasattr(sample, "__cuda_array_interface__"):
                result.append(torch.as_tensor(sample))
            else:
                dlpack_capsule = sample.toDlpack()
                result.append(torch_dlpack.from_dlpack(dlpack_capsule))
        return result
