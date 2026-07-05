"""TensorRT engine inference session with torch CUDA I/O bindings."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

try:
    import tensorrt as trt
except Exception:  # pragma: no cover - TensorRT may not be installed on CPU-only hosts.
    trt = None

if TYPE_CHECKING:
    import torch


class TrtInferenceSession:
    """Wrap a serialized TensorRT engine for a fixed batch size."""

    def __init__(self, engine_path: Path | str) -> None:
        self._engine_path = Path(engine_path)
        if not self._engine_path.exists():
            raise RuntimeError(f"TensorRT engine not found: {self._engine_path}")
        self._context = None
        self._stream = None
        self._engine = None
        self._input_name: str | None = None
        self._output_names: list[str] = []

    def load(self) -> None:
        """Load the engine. Must be called before inference."""
        import torch

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is not available. TensorRT engines must be loaded on a "
                "CUDA-capable device with NVIDIA drivers installed."
            )

        if trt is None:
            raise RuntimeError(
                "TensorRT is not installed. Install tensorrt and run on a CUDA-capable machine."
            )

        logger = trt.Logger(trt.Logger.WARNING)
        with open(self._engine_path, "rb") as f:
            runtime = trt.Runtime(logger)
            self._engine = runtime.deserialize_cuda_engine(f.read())
        if self._engine is None:
            raise RuntimeError(f"Failed to deserialize engine {self._engine_path}")

        self._context = self._engine.create_execution_context()
        self._stream = torch.cuda.Stream(device=torch.device("cuda"))

        for i in range(self._engine.num_io_tensors):
            name = self._engine.get_tensor_name(i)
            mode = self._engine.get_tensor_mode(name)
            if mode == trt.TensorIOMode.INPUT:
                self._input_name = name
            else:
                self._output_names.append(name)

        if self._input_name is None:
            raise RuntimeError("Engine has no input tensor")

    def infer(self, input_tensor: torch.Tensor) -> list[NDArray[np.float32]]:
        """Run inference and return CPU numpy outputs."""
        import torch

        context = self._context
        if context is None:
            self.load()
            context = self._context
        if context is None or self._stream is None or self._input_name is None:
            raise RuntimeError("TensorRT session is not loaded")

        input_tensor = input_tensor.contiguous()
        context.set_input_shape(self._input_name, tuple(input_tensor.shape))
        if not context.all_binding_shapes_specified:
            raise RuntimeError("Not all TensorRT binding shapes are specified")

        # Output buffers must match the engine's output dtype (FP16 engines
        # produce FP16 outputs). Fall back to FP32 if dtype lookup fails.
        if self._engine is None:
            raise RuntimeError("TensorRT engine is not loaded")
        outputs: list[torch.Tensor] = []
        for name in self._output_names:
            shape = tuple(context.get_tensor_shape(name))
            shape = tuple(s if s > 0 else input_tensor.shape[0] for s in shape)
            dtype = self._engine.get_tensor_dtype(name)
            torch_dtype = self._trt_dtype_to_torch(dtype)
            outputs.append(torch.empty(shape, dtype=torch_dtype, device=input_tensor.device))

        context.set_tensor_address(self._input_name, int(input_tensor.data_ptr()))
        for name, out in zip(self._output_names, outputs, strict=True):
            context.set_tensor_address(name, int(out.data_ptr()))

        context.execute_async_v3(stream_handle=self._stream.cuda_stream)
        self._stream.synchronize()

        return [out.float().cpu().numpy() for out in outputs]

    @staticmethod
    def _trt_dtype_to_torch(dtype: object) -> torch.dtype:
        import tensorrt as trt
        import torch

        mapping = {
            trt.DataType.FLOAT: torch.float32,
            trt.DataType.HALF: torch.float16,
            trt.DataType.INT32: torch.int32,
            trt.DataType.INT8: torch.int8,
        }
        return mapping.get(dtype, torch.float32)
