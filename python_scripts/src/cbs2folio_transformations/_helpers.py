"""Module for reusable codesnippets."""
from typing import NoReturn
from typing import TypeVar

_ExceptionType = TypeVar("_ExceptionType", bound=Exception)


# Source: https://stackoverflow.com/questions/9157210/how-do-i-raise-the-same-exception-with-a-custom-message-in-python  # noqa: E501
def reraise(
    e: _ExceptionType, info: str
) -> NoReturn:  # pyright: reportInvalidTypeVarUse=false
    """Reraise an exception after adding information.

    Args:
        e (_ExceptionType): Exception to reraise
        info (str): Additional information

    Raises:
        e.with_traceback (_ExceptionType): The appended Exception

    Returns:
        NoReturn: Does not return
    """
    e.args = info, *e.args
    raise e.with_traceback(e.__traceback__)
