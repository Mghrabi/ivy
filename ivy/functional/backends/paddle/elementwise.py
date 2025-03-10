# global
from typing import Union, Optional, Tuple, Type

import paddle
import math
import ivy.functional.backends.paddle as paddle_backend
import ivy
from ivy import promote_types_of_inputs
from ivy.func_wrapper import with_unsupported_device_and_dtypes, with_supported_dtypes

# local
from . import backend_version
from ...ivy.elementwise import _complex_to_inf


def _elementwise_helper(x1, x2):
    x1, x2 = ivy.promote_types_of_inputs(x1, x2)
    x1, x2 = paddle_backend.broadcast_arrays(x1, x2)
    return x1, x2, x1.dtype


def add(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    alpha: Optional[Union[int, float]] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [
        paddle.int8,
        paddle.uint8,
        paddle.float16,
        paddle.bool,
        paddle.bfloat16,
    ]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    if alpha not in (1, None):
        x2 = paddle_backend.multiply(x2, alpha)
        x1, x2 = ivy.promote_types_of_inputs(x1, x2)
    return paddle.add(x1, x2).astype(ret_dtype)


def bitwise_xor(
    x1: Union[int, bool, paddle.Tensor],
    x2: Union[int, bool, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    return paddle.bitwise_xor(x1, x2)


def expm1(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [paddle.float16, paddle.float32, paddle.float64]:
        return paddle.expm1(x)
    return paddle_backend.subtract(paddle_backend.exp(x), 1.0).astype(x.dtype)


def bitwise_invert(
    x: Union[int, bool, paddle.Tensor], /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    return paddle.bitwise_not(x)


@with_unsupported_device_and_dtypes(
    {
        "2.5.1 and below": {
            "cpu": (
                "int8",
                "int16",
                "uint8",
                "complex64",
                "complex128",
                "bool",
            )
        }
    },
    backend_version,
)
def isfinite(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    return paddle.isfinite(x)


def isinf(
    x: paddle.Tensor,
    /,
    *,
    detect_positive: bool = True,
    detect_negative: bool = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if detect_negative and detect_positive:
        return paddle.isinf(x)

    if detect_negative:
        return paddle_backend.equal(x, float("-inf"))

    if detect_positive:
        return paddle_backend.equal(x, float("inf"))

    return paddle.zeros(shape=x.shape, dtype=bool)


def equal(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    diff = paddle_backend.subtract(x1, x2)
    ret = paddle_backend.logical_and(
        paddle_backend.less_equal(diff, 0), paddle_backend.greater_equal(diff, 0)
    )
    # ret result is sufficient for all cases except where the value is +/-INF of NaN
    return paddle_backend.where(
        paddle_backend.isnan(diff),
        ~paddle_backend.logical_or(paddle_backend.isnan(x1), paddle_backend.isnan(x2)),
        ret,
    )


def less_equal(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.uint8, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x1):
            if paddle.is_complex(x1):
                real = paddle.less_equal(x1.real(), x2.real())
                imag = paddle.less_equal(x1.imag(), x2.imag())
                return paddle_backend.logical_and(real, imag)
        return paddle.less_equal(x1.astype("float32"), x2.astype("float32"))

    return paddle.less_equal(x1, x2)


def bitwise_and(
    x1: Union[int, bool, paddle.Tensor],
    x2: Union[int, bool, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    return paddle.bitwise_and(x1, x2)


def ceil(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    x_dtype = x.dtype
    if x_dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.complex(paddle.ceil(x.real()), paddle.ceil(x.imag()))
        return paddle.ceil(x.astype("float32")).astype(x_dtype)
    elif x_dtype == paddle.int64:
        return paddle.ceil(x.astype("float64")).astype(x_dtype)
    return paddle.ceil(x)


def floor(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    x_dtype = x.dtype
    if x_dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.complex(paddle.floor(x.real()), paddle.floor(x.imag()))
        return paddle.floor(x.astype("float32")).astype(x_dtype)
    elif x_dtype == paddle.int64:
        return paddle.floor(x.astype("float64")).astype(x_dtype)
    return paddle.floor(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def asin(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.asin(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        asinh_iz = paddle_backend.asinh(paddle.complex(-x.imag(), x.real()))
        return paddle.complex(asinh_iz.imag(), -asinh_iz.real())
    return paddle.asin(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def asinh(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.asinh(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        # From https://github.com/python/cpython/blob/39ef93edb9802dccdb6555d4209ac2e60875a011/Modules/cmathmodule.c#L276 # noqa
        s1 = paddle_backend.sqrt(paddle.complex(1 + x.imag(), -x.real()))
        s2 = paddle_backend.sqrt(paddle.complex(1 - x.imag(), x.real()))
        return paddle.complex(
            paddle.asinh(s1.real() * s2.imag() - s2.real() * s1.imag()),
            paddle.atan2(x.imag(), s1.real() * s2.real() - s1.imag() * s2.imag()),
        )
    return paddle.asinh(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128")}},
    backend_version,
)
def sign(
    x: paddle.Tensor,
    /,
    *,
    np_variant: Optional[bool] = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
        paddle.bfloat16,
        paddle.bool,
    ]:
        return paddle.sgn(x.astype("float32")).astype(x.dtype)
    return paddle.sgn(x)


# TODO: Remove `float16` from the list once paddle add it's supporting kernel to `CPU`.
def _determine_sqrt_dtype_cast(
    dtype: Type[paddle.Tensor],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine the appropriate casting dtype for sqrt operations.

    Returns:
        (intermediate_dtype, output_dtype)
    """

    cast_and_return_float32_dtype = {
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.uint8,
        paddle.bool,
    }

    if dtype in cast_and_return_float32_dtype:
        return "float32", "float32"
    elif dtype == paddle.int64:
        return "float64", "float64"
    elif dtype == paddle.float16:
        return "float32", "float16"
    elif dtype == paddle.bfloat16:
        return "float32", "bfloat16"
    else:
        return None, None


def sqrt(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    """Calculate the square root with type handling."""

    if paddle.is_complex(x):
        angle = paddle.angle(x)
        return paddle.complex(
            paddle.cos(angle / 2), paddle.sin(angle / 2)
        ) * paddle.sqrt(paddle.abs(x))

    if x.dtype in {paddle.float32, paddle.float64}:
        return paddle.sqrt(x)

    intermediate_dtype, output_dtype = _determine_sqrt_dtype_cast(x.dtype)
    if intermediate_dtype:
        result = paddle.sqrt(x.astype(intermediate_dtype))
        return result.astype(output_dtype)

    raise ValueError(f"Unsupported data type for sqrt: {x.dtype}")


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def cosh(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.cosh(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        re = x.real()
        im = x.imag()
        return paddle.complex(
            paddle.cosh(re) * paddle.cos(im), paddle.sinh(re) * paddle.sin(im)
        )
    return paddle.cosh(x)


def log10(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            base = paddle.to_tensor(10.0).squeeze()
            return paddle_backend.divide(
                paddle_backend.log(x), paddle_backend.log(base)
            ).astype(x.dtype)
        return paddle.log10(x.astype("float32")).astype(x.dtype)
    return paddle.log10(x)


def log2(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            base = paddle.to_tensor(2.0).squeeze()
            return paddle_backend.divide(
                paddle_backend.log(x), paddle_backend.log(base)
            ).astype(x.dtype)
        return paddle.log2(x.astype("float32")).astype(x.dtype)
    return paddle.log2(x)


def log1p(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle_backend.log(x + 1)
        return paddle.log1p(x.astype("float32")).astype(x.dtype)
    return paddle.log1p(x)


def isnan(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.logical_or(paddle.isnan(x.real()), paddle.isnan(x.imag()))
        return paddle.isnan(x.astype("float32"))
    return paddle.isnan(x)


def less(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.uint8, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x1):
            real = paddle.less_than(x1.real(), x2.real())
            imag = paddle.less_than(x1.imag(), x2.imag())
            return logical_and(real, imag)
        return paddle.less_than(x1.astype("float32"), x2.astype("float32"))

    return paddle.less_than(x1, x2)


def multiply(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.int16, paddle.uint8, paddle.float16]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    return paddle.multiply(x1, x2).astype(ret_dtype)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def cos(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.cos(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        re = x.real()
        im = x.imag()
        return paddle.complex(
            paddle.cos(re) * paddle.cosh(im),
            -paddle.sin(re) * paddle.sinh(im),
        )
    return paddle.cos(x)


def logical_not(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [paddle.uint8, paddle.float16, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x):
            return paddle.logical_and(
                paddle.logical_not(x.real()), paddle.logical_not(x.imag())
            )
        return paddle.logical_not(x.astype("float32"))
    return paddle.logical_not(x)


def divide(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.float16, paddle.bfloat16]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    if not (ivy.is_float_dtype(ret_dtype) or ivy.is_complex_dtype(ret_dtype)):
        ret_dtype = ivy.default_float_dtype(as_native=True)
    return (x1 / x2).astype(ret_dtype)


@with_supported_dtypes(
    {"2.5.1 and below": ("float64", "float32", "int64", "int64")},
    backend_version,
)
def fmin(
    x1: paddle.Tensor,
    x2: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x1.dtype != x2.dtype:
        x1, x2 = promote_types_of_inputs(x1, x2)
    return paddle.fmin(x1, x2)


def greater(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.uint8, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x1):
            if paddle.is_complex(x1):
                real = paddle.greater_than(x1.real(), x2.real())
                imag = paddle.greater_than(x1.imag(), x2.imag())
                return paddle.logical_and(real, imag)
        return paddle.greater_than(x1.astype("float32"), x2.astype("float32"))
    return paddle.greater_than(x1, x2)


def greater_equal(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.uint8, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x1):
            if paddle.is_complex(x1):
                real = paddle.greater_equal(x1.real(), x2.real())
                imag = paddle.greater_equal(x1.imag(), x2.imag())
                return paddle.logical_and(real, imag)
        return paddle.greater_equal(x1.astype("float32"), x2.astype("float32"))
    return paddle.greater_equal(x1, x2)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def acos(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.acos(x.astype("float32")).astype(x.dtype)
    if paddle.is_complex(x):
        # From https://github.com/python/cpython/blob/39ef93edb9802dccdb6555d4209ac2e60875a011/Modules/cmathmodule.c#L178 # noqa
        s1 = paddle_backend.sqrt(1 - x)
        s2 = paddle_backend.sqrt(1 + x)
        return paddle.complex(
            2.0 * paddle.atan2(s1.real(), s2.real()),
            paddle.asinh(s2.real() * s1.imag() - s2.imag() * s1.real()),
        )
    return paddle.acos(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128")}},
    backend_version,
)
def logical_xor(
    x1: paddle.Tensor, x2: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if ret_dtype in [paddle.uint8, paddle.float16, paddle.complex64, paddle.complex128]:
        # this logic works well when both inputs are complex but when one of them
        # is casted from real to complex, the imaginary part is zero which messes
        # with the XOR logic
        # if paddle.is_complex(x1):
        #     return paddle.logical_xor(
        #         paddle.logical_xor(x1.real(), x2.real()),
        #         paddle.logical_xor(x1.imag(), x2.imag()),
        #     )
        return paddle.logical_xor(x1.astype("float32"), x2.astype("float32"))
    return paddle.logical_xor(x1, x2)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128")}},
    backend_version,
)
def logical_and(
    x1: paddle.Tensor, x2: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if ret_dtype in [paddle.uint8, paddle.float16, paddle.complex64, paddle.complex128]:
        # this logic works well when both inputs are complex but when one of them
        # is casted from real to complex, the imaginary part is zero which messes
        # if paddle.is_complex(x1):
        #     return paddle.logical_and(
        #         paddle.logical_and(x1.real(), x2.real()),
        #         paddle.logical_and(x1.imag(), x2.imag()),
        #     )
        return paddle.logical_and(x1.astype("float32"), x2.astype("float32"))
    return paddle.logical_and(x1, x2)


def logical_or(
    x1: paddle.Tensor, x2: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if ret_dtype in [paddle.uint8, paddle.float16, paddle.complex64, paddle.complex128]:
        if paddle.is_complex(x1):
            return paddle.logical_or(
                paddle.logical_or(x1.real(), x2.real()),
                paddle.logical_or(x1.imag(), x2.imag()),
            )
        return paddle.logical_or(x1.astype("float32"), x2.astype("float32"))
    return paddle.logical_or(x1, x2)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def acosh(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.acosh(x.astype("float32")).astype(x.dtype)
    if paddle.is_complex(x):
        # From https://github.com/python/cpython/blob/39ef93edb9802dccdb6555d4209ac2e60875a011/Modules/cmathmodule.c#L221 # noqa
        s1 = paddle_backend.sqrt(paddle.complex(x.real() - 1, x.imag()))
        s2 = paddle_backend.sqrt(paddle.complex(x.real() + 1, x.imag()))
        return paddle.complex(
            paddle.asinh(s1.real() * s2.real() + s1.imag() * s2.imag()),
            2.0 * paddle.atan2(s1.imag(), s2.real()),
        )
    return paddle.acosh(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def sin(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.sin(x.astype("float32")).astype(x.dtype)
    if paddle.is_complex(x):
        re = x.real()
        im = x.imag()
        return paddle.complex(
            paddle.sin(re) * paddle.cosh(im), paddle.cos(re) * paddle.sinh(im)
        )
    return paddle.sin(x)


def negative(
    x: Union[float, paddle.Tensor], /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if not isinstance(x, paddle.Tensor):
        x = paddle.to_tensor(
            x, dtype=ivy.default_dtype(item=x, as_native=True)
        ).squeeze()
    if x.dtype == paddle.bool:
        return paddle.logical_not(x)
    return paddle.neg(x)


def not_equal(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle.logical_not(paddle_backend.equal(x1, x2))


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def tanh(
    x: paddle.Tensor, /, *, complex_mode="jax", out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.tanh(x.astype("float32")).astype(x.dtype)
    if paddle.is_complex(x):
        tanh_a = paddle.tanh(paddle.real(x))
        tan_b = paddle.tan(paddle.imag(x))
        return (tanh_a + 1j * tan_b) / (1 + 1j * (tanh_a * tan_b))
    return paddle.tanh(x)


def floor_divide(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int32, paddle.int64]:
        return paddle.floor_divide(x1, x2)
    return paddle_backend.floor(paddle_backend.divide(x1, x2)).astype(ret_dtype)


def bitwise_or(
    x1: Union[int, bool, paddle.Tensor],
    x2: Union[int, bool, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    return paddle.bitwise_or(x1, x2)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def sinh(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.sinh(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        re = x.real()
        im = x.imag()
        return paddle.complex(
            paddle.sinh(re) * paddle.cos(im), paddle.cosh(re) * paddle.sin(im)
        )
    return paddle.sinh(x)


def positive(
    x: Union[float, paddle.Tensor], /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if not isinstance(x, paddle.Tensor):
        x = paddle.to_tensor(
            x, dtype=ivy.default_dtype(item=x, as_native=True)
        ).squeeze()
    return x.clone()


def square(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [paddle.int32, paddle.int64, paddle.float32, paddle.float64]:
        return paddle.square(x)
    if paddle.is_complex(x):
        return paddle.complex(
            paddle.square(paddle.real(x)) - paddle.square(paddle.imag(x)),
            2.0 * paddle.real(x) * paddle.imag(x),
        )
    return paddle_backend.pow(x, 2).astype(x.dtype)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bfloat16",)}}, backend_version
)
def pow(
    x1: paddle.Tensor,
    x2: Union[int, float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if ivy.is_complex_dtype(x1) and ivy.any(ivy.isinf(x2)):
        inf_indices = paddle.nonzero(paddle.isinf(x2))
        ret = paddle.pow(x1, x2)
        ret[inf_indices] = _complex_to_inf(ret[inf_indices])
        return ret
    if x1.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.bool,
    ]:
        return paddle.pow(x1.astype("float32"), x2.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x1):
        # https://math.stackexchange.com/questions/476968/complex-power-of-a-complex-number
        r = paddle.abs(x1)
        theta = paddle.angle(x1)
        res_mag = paddle.pow(r, x2.real()) / paddle.exp(x2.imag() * theta)
        res_ang = paddle.log(r) * x2.imag() + theta * x2.real()
        result = res_mag * paddle.complex(paddle.cos(res_ang), paddle.sin(res_ang))
        return result.astype(ret_dtype)
    return paddle.pow(x1, x2)


def round(
    x: paddle.Tensor, /, *, decimals: int = 0, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    def _np_round(x):
        # this is a logic to mimic np.round behaviour
        # which rounds odd numbers up and even numbers down at limits like 0.5

        one = paddle.to_tensor(1, dtype="int64")

        # check if the number is even or odd
        is_even = paddle.bitwise_and(paddle_backend.trunc(x).astype("int64"), one) == 0

        # round the number to the nearest integer
        round_x = paddle.sign(x) * paddle.where(
            is_even, paddle.floor(x.abs()), paddle.ceil(x.abs())
        )

        # if the number was rounded up from an even number
        #   round the number down to the nearest even number
        return paddle.where(
            paddle.logical_and(
                paddle.bitwise_and(round_x.astype("int64"), one) == 1.0,
                is_even,
            ),
            round_x - 1.0,
            round_x,
        )

    if x.dtype not in [paddle.float32, paddle.float64]:
        if paddle.is_complex(x):
            return paddle.complex(_np_round(x.real()), _np_round(x.imag()))
        return _np_round(x.astype("float32")).astype(x.dtype)
    return _np_round(x).astype(x.dtype)


def trunc(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.complex(paddle.trunc(x.real()), paddle.trunc(x.imag()))
        return paddle.trunc(x.astype("float32")).astype(x.dtype)
    return paddle.trunc(x)


@with_supported_dtypes(
    {"2.5.1 and below": ("float64", "float32")},
    backend_version,
)
def trapz(
    y: paddle.Tensor,
    /,
    *,
    x: Optional[paddle.Tensor] = None,
    dx: Optional[float] = 1.0,
    axis: Optional[int] = -1,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if x is None:
        d = dx
    else:
        if x.ndim == 1:
            d = paddle.diff(x)
            # reshape to correct shape
            shape = [1] * y.ndim
            shape[axis] = d.shape[0]
            d = d.reshape(shape)
        else:
            d = paddle.diff(x, axis=axis)

    slice1 = [slice(None)] * y.ndim
    slice2 = [slice(None)] * y.ndim

    slice1[axis] = slice(1, None)
    slice2[axis] = slice(None, -1)

    with ivy.ArrayMode(False):
        if y.shape[axis] < 2:
            return ivy.zeros_like(ivy.squeeze(y, axis=axis))
        ret = ivy.sum(
            ivy.divide(
                ivy.multiply(
                    d,
                    ivy.add(
                        ivy.get_item(y, tuple(slice1)), ivy.get_item(y, tuple(slice2))
                    ),
                ),
                2.0,
            ),
            axis=axis,
        )

    return ret


def abs(
    x: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if not isinstance(x, paddle.Tensor):
        x = paddle.to_tensor(x, dtype=ivy.default_dtype(item=x)).squeeze()
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.bfloat16,
        paddle.bool,
    ]:
        return paddle.abs(x.astype("float32")).astype(x.dtype)
    return paddle.abs(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("float16",)}}, backend_version
)
def logaddexp(
    x1: paddle.Tensor, x2: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    amax = paddle_backend.maximum(x1, x2)
    return amax + paddle_backend.log(
        paddle_backend.exp(x1 - amax) + paddle_backend.exp(x2 - amax)
    ).astype(ret_dtype)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("float16",)}}, backend_version
)
def logaddexp2(
    x1: Union[paddle.Tensor, float, list, tuple],
    x2: Union[paddle.Tensor, float, list, tuple],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    with ivy.ArrayMode(False):
        return ivy.log2(ivy.exp2(x1) + ivy.exp2(x2))


@with_unsupported_device_and_dtypes(
    {
        "2.5.1 and below": {
            "cpu": (
                "int8",
                "int16",
                "int32",
                "int64",
                "uint8",
                "float16",
                "float32",
                "float64",
                "bool",
            )
        }
    },
    backend_version,
)
def real(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    return paddle.real(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def tan(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.tan(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        tanh_ix = paddle_backend.tanh(paddle.complex(-x.imag(), x.real()))
        return paddle.complex(tanh_ix.imag(), -tanh_ix.real())
    return paddle.tan(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def atan(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.atan(x.astype("float32")).astype(ret_dtype)
    if x.dtype in [paddle.complex64, paddle.complex128]:
        atanh_iz = paddle_backend.atanh(paddle.complex(-x.imag(), x.real()))
        return paddle.complex(atanh_iz.imag(), -atanh_iz.real())
    return paddle.atan(x)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128", "bool")}},
    backend_version,
)
def atan2(
    x1: paddle.Tensor, x2: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.int16, paddle.uint8]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    return paddle.atan2(x1, x2).astype(ret_dtype)


def log(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x):
            return paddle.complex(paddle.log(paddle.abs(x)), paddle.angle(x))
        return paddle.log(x.astype("float32")).astype(x.dtype)
    return paddle.log(x)


def exp(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [paddle.int32, paddle.int64, paddle.float32, paddle.float64]:
        return paddle.exp(x)
    if paddle.is_complex(x):
        return paddle.multiply(
            paddle.exp(x.real()),
            paddle.complex(paddle.cos(x.imag()), paddle.sin(x.imag())),
        )
    return paddle_backend.pow(math.e, x).astype(x.dtype)


def exp2(
    x: Union[paddle.Tensor, float, list, tuple],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    with ivy.ArrayMode(False):
        return ivy.pow(2, x)


def subtract(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    alpha: Optional[Union[int, float]] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [paddle.int8, paddle.uint8, paddle.float16, paddle.bool]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    if alpha not in (1, None):
        x2 = paddle_backend.multiply(x2, alpha)
        x1, x2 = ivy.promote_types_of_inputs(x1, x2)
    return paddle.subtract(x1, x2).astype(ret_dtype)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128", "bool")}},
    backend_version,
)
def remainder(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    modulus: bool = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if not modulus:
        res = paddle_backend.divide(x1, x2)
        res_floored = paddle_backend.where(
            paddle_backend.greater_equal(res, 0.0),
            paddle_backend.floor(res),
            paddle_backend.ceil(res),
        )
        diff = paddle_backend.subtract(res, res_floored).astype(res.dtype)
        return paddle_backend.round(paddle_backend.multiply(diff, x2)).astype(x1.dtype)

    if x1.dtype in [paddle.int8, paddle.int16, paddle.uint8, paddle.float16]:
        x1, x2 = x1.astype("float32"), x2.astype("float32")
    return paddle.remainder(x1, x2).astype(ret_dtype)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("bool", "bfloat16")}},
    backend_version,
)
def atanh(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.int32,
        paddle.int64,
        paddle.uint8,
        paddle.float16,
    ]:
        ret_dtype = x.dtype
        return paddle.atanh(x.astype("float32")).astype(ret_dtype)
    if paddle.is_complex(x):
        return 0.5 * (paddle_backend.log(1 + x) - paddle_backend.log(1 - x))
    return paddle.atanh(x)


def bitwise_right_shift(
    x1: Union[int, bool, paddle.Tensor],
    x2: Union[int, bool, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    return paddle.floor(x1.astype("float64") / 2 ** x2.astype("float64")).astype(
        ret_dtype
    )


def bitwise_left_shift(
    x1: Union[int, bool, paddle.Tensor],
    x2: Union[int, bool, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    return paddle.floor(x1.astype("float64") * 2 ** x2.astype("float64")).astype(
        ret_dtype
    )


# Extra #
# ------#


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("complex64", "complex128", "bool")}},
    backend_version,
)
def erf(x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None) -> paddle.Tensor:
    # TODO: add support for complex x, supported in scipy only atm
    if x.dtype in [paddle.int8, paddle.int16, paddle.int32, paddle.int64, paddle.uint8]:
        return paddle.erf(x.astype("float32")).astype(x.dtype)
    return paddle.erf(x)


def minimum(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    use_where: bool = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x1):
            use_where = True
        else:
            x1, x2 = x1.astype("float32"), x2.astype("float32")

    if use_where:
        return paddle_backend.where(paddle_backend.less_equal(x1, x2), x1, x2).astype(
            ret_dtype
        )

    return paddle.minimum(x1, x2).astype(ret_dtype)


def maximum(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    use_where: bool = True,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    if x1.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(x1):
            use_where = True
        else:
            x1, x2 = x1.astype("float32"), x2.astype("float32")
    if use_where:
        return paddle_backend.where(
            paddle_backend.greater_equal(x1, x2), x1, x2
        ).astype(ret_dtype)
    return paddle.maximum(x1, x2).astype(ret_dtype)


def reciprocal(
    x: Union[float, paddle.Tensor], /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [paddle.float32, paddle.float64]:
        return paddle.reciprocal(x)
    return paddle_backend.divide(1, x)


def deg2rad(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [paddle.int32, paddle.int64, paddle.bool]:
        return paddle.deg2rad(x.astype("float32")).astype(x.dtype)
    return paddle.deg2rad(x)


def rad2deg(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if x.dtype in [paddle.int32, paddle.int64, paddle.bool]:
        return paddle.rad2deg(x.astype("float32")).astype(x.dtype)
    return paddle.rad2deg(x)


def trunc_divide(
    x1: Union[float, paddle.Tensor],
    x2: Union[float, paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle_backend.trunc(paddle_backend.divide(x1, x2))


def isreal(
    x: paddle.Tensor, /, *, out: Optional[paddle.Tensor] = None
) -> paddle.Tensor:
    if paddle.is_complex(x):
        return paddle.logical_not(x.imag().astype(bool))
    else:
        return paddle.ones_like(x, dtype="bool")


def fmod(
    x1: paddle.Tensor,
    x2: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2, ret_dtype = _elementwise_helper(x1, x2)
    res = paddle_backend.remainder(paddle_backend.abs(x1), paddle_backend.abs(x2))
    return paddle_backend.where(paddle_backend.less(x1, 0), -res, res)


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("int8", "uint8")}},
    backend_version,
)
def lcm(
    x1: paddle.Tensor,
    x2: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1_dtype = x1.dtype
    x2_dtype = x2.dtype
    if (x1_dtype, x2_dtype) == (paddle.int16, paddle.int16):
        return paddle.cast(
            paddle.lcm(paddle.cast(x1, paddle.int32), paddle.cast(x2, paddle.int32)),
            paddle.int16,
        )
    elif x1_dtype != x2_dtype:
        x1, x2 = ivy.promote_types_of_inputs(x1, x2)
    return paddle.lcm(x1, x2)


def angle(
    input: paddle.Tensor,
    /,
    *,
    deg: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    result = paddle.angle(input)
    if deg:
        result = paddle.rad2deg(result)
    return result


@with_unsupported_device_and_dtypes(
    {"2.5.1 and below": {"cpu": ("int8", "int16", "uint8")}}, backend_version
)
def gcd(
    x1: Union[paddle.Tensor, int, list, tuple],
    x2: Union[paddle.Tensor, float, list, tuple],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    x1, x2 = promote_types_of_inputs(x1, x2)
    return paddle.gcd(x1, x2)


@with_unsupported_device_and_dtypes(
    {
        "2.5.1 and below": {
            "cpu": (
                "int8",
                "int16",
                "int32",
                "int64",
                "uint8",
                "float16",
                "float32",
                "float64",
                "bool",
            )
        }
    },
    backend_version,
)
def imag(
    val: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle.imag(val)


def nan_to_num(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = True,
    nan: Optional[Union[float, int]] = 0.0,
    posinf: Optional[Union[float, int]] = None,
    neginf: Optional[Union[float, int]] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    with ivy.ArrayMode(False):
        if ivy.is_int_dtype(x):
            if posinf is None:
                posinf = ivy.iinfo(x).max
            if neginf is None:
                neginf = ivy.iinfo(x).min
        elif ivy.is_float_dtype(x) or ivy.is_complex_dtype(x):
            if posinf is None:
                posinf = ivy.finfo(x).max
            if neginf is None:
                neginf = ivy.finfo(x).min
        ret = ivy.where(ivy.isnan(x), paddle.to_tensor(nan, dtype=x.dtype), x)
        ret = ivy.where(
            ivy.logical_and(ivy.isinf(ret), ret > 0),
            paddle.to_tensor(posinf, dtype=x.dtype),
            ret,
        )
        ret = ivy.where(
            ivy.logical_and(ivy.isinf(ret), ret < 0),
            paddle.to_tensor(neginf, dtype=x.dtype),
            ret,
        )
        if copy:
            return ret.clone()
        else:
            x = ret
            return x
