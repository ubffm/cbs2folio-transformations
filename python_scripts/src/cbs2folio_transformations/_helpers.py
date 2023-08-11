"""Module for reusable codesnippets."""
import logging
import pathlib
import re
from typing import NoReturn
from typing import TypeVar

from lxml import etree  # nosec: ignore[blacklist]

logger = logging.getLogger(__name__)
EXAMPLE_XSL = (
    pathlib.Path(__file__)
    .parent.resolve()
    .joinpath("../../../hebis/holding-items-hebis-iln204.xsl")
)

_ExceptionType = TypeVar("_ExceptionType", bound=Exception)


# Source: https://stackoverflow.com/questions/9157210/how-do-i-raise-the-same-exception-with-a-custom-message-in-python  # noqa: E501
def reraise(
    e: "_ExceptionType", info: str  # pyright: ignore [reportInvalidTypeVarUse]
) -> NoReturn:
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


def _get_string_value_of_element(element: etree._Element) -> str:
    # check for nested nodes first
    _xsl_value_of = element.find(
        "./" "xsl:value-of",
        namespaces={"xsl": "http://www.w3.org/1999/XSL/Transform"},
    )
    if _xsl_value_of is not None:
        return _get_string_value_of_element(_xsl_value_of)

    if "select" in element.attrib:
        if (_select_text := element.attrib["select"]) is None:
            raise ValueError("Element with empty select value")
        return str(_select_text).strip("'")
    if hasattr(element, "text"):
        if (_text := element.text) is None:
            raise ValueError("Element with empty text")
        return str(_text).strip("'")

    raise ValueError(
        f"Could not extract value from {etree.tostring(element).decode()}"
    )


# Based on: https://www.mail-archive.com/lxml@python.org/msg00011.html
def get_variable_from_xsl(variable_name: str, xsl: etree._ElementTree) -> str:
    """Get the value of an XSL variable.

    Args:
        variable_name (str): Name of the variable to find
        xsl (etree._ElementTree): XSL Tree to search in

    Raises:
        ValueError: Unknown variable

    Returns:
        str: Value of the variable
    """
    xpath_results = xsl.find(
        f"//xsl:variable[@name='{variable_name}']",
        namespaces={"xsl": "http://www.w3.org/1999/XSL/Transform"},
    )
    if xpath_results is None:
        raise ValueError(
            f"{variable_name} not defined in XSL: {etree.tostring(xsl).decode()}"  # noqa: ignore[E501]
        )
    return _get_string_value_of_element(xpath_results)


# Based on: https://www.mail-archive.com/lxml@python.org/msg00011.html
def get_param_default_from_xsl(
    param_name: str, xsl: etree._ElementTree
) -> str:
    """Get the value of an XSL variable.

    Args:
        variable_name (str): Name of the variable to find
        xsl (etree._ElementTree): XSL Tree to search in

    Raises:
        ValueError: Unknown variable

    Returns:
        str: Value of the variable
    """
    xpath_results = xsl.find(
        f"//xsl:param[@name='{param_name}']",
        namespaces={"xsl": "http://www.w3.org/1999/XSL/Transform"},
    )
    if xpath_results is None:
        raise ValueError(
            f"{param_name} not defined in XSL: {etree.tostring(xsl).decode()}"
        )

    return _get_string_value_of_element(xpath_results)


MARKERS = get_param_default_from_xsl(
    param_name="token-markers",
    xsl=etree.parse(EXAMPLE_XSL),  # nosec B320 # this is a trusted XML file
)  # Mark segments of signatures to be considered tokens

VALIDATION_REGEX = re.compile(
    r"|"
    + r"^\w+"  # Allow empty ranges  # FIXME
    + r"(?:"  # Additional parts
    + r"(?:"  # Seperator
    + r"["
    + ",".join([re.escape(marker) for marker in MARKERS])
    + r"]+"
    + r")"
    + r"\w+"
    + r")*"
    + r"(?:@@@)?"  # Prefix marker
    + r"\s*"  # Allow trailing whitespace  # FIXME
    + r"$"
)


# TODO: evaluate using the tokenize function defined in the XML
def tokenize(  # nosec hardcoded_password_default
    text: str,
    markers=MARKERS,
    token_marker="|",
) -> list[str]:
    """Create a list of tokens from a string.

    Args:
        text (str): Text to tokenize
    """
    for marker in markers:
        text = text.replace(marker, token_marker)
    return [_token for _token in text.split(token_marker) if _token]


NAMESPACES = {"xsl": "http://www.w3.org/1999/XSL/Transform"}
XML_MAX_INT = int("2147483647")
