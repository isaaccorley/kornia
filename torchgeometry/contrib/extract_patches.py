from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class ExtractTensorPatches(nn.Module):
    r"""Module that extract patches from tensors and stack them.
    """

    def __init__(
            self,
            window_size: int,
            stride: int = 1,
            padding: int = 0) -> None:
        super(ExtractTensorPatches, self).__init__()
        self.window_size: int = window_size
        self.stride: int = stride
        self.padding: int = padding
        self.eps: float = 1e-6

        # create base kernel
        self.kernel: torch.Tensor = self.create_kernel(self.window_size)

    @staticmethod
    def create_kernel(window_size: int, eps: float = 1e-6) -> torch.Tensor:
        window_range = window_size * window_size
        kernel = torch.zeros(window_range, window_range) + eps
        for i in range(window_range):
            kernel[i, i] += 1.0
        return kernel.view(window_range, 1, window_size, window_size)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if not torch.is_tensor(input):
            raise TypeError("Input input type is not a torch.Tensor. Got {}"
                            .format(type(input)))
        if not len(input.shape) == 4:
            raise ValueError("Invalid input shape, we expect BxCxHxW. Got: {}"
                             .format(input.shape))
        # unpack shapes
        batch_size, channels, height, width = input.shape

        # run convolution 2d to extract patches
        kernel: torch.Tensor = self.kernel.repeat(channels, 1, 1, 1)
        kernel = kernel.to(input.device).to(input.dtype)
        output_tmp: torch.Tensor = F.conv2d(
            input,
            kernel,
            stride=self.stride,
            padding=self.padding,
            groups=channels)

        # reshape the output tensor
        output: torch.Tensor = output_tmp.view(
            batch_size, channels, self.window_size, self.window_size, -1)
        return output.permute(0, 4, 1, 2, 3)  # BxNxCxhxw


######################
# functional interface
######################


def extract_tensor_patches(
        input: torch.Tensor,
        window_size: int, stride: int = 1, padding: int = 0) -> torch.Tensor:
    r"""Function that extract patches from tensors and stack them.

    See :class:`~torchgeometry.contrib.ExtractTensorPatches` for details.
    """
    return ExtractTensorPatches(window_size, stride, padding)(input)
