"""Constants."""
import pathlib
import re

from lxml import etree  # nosec blacklist

from ._helpers import get_param_default_from_xsl

EXAMPLE_XSL = (
    pathlib.Path(__file__)
    .parent.resolve()
    .joinpath("../../../hebis/holding-items-hebis-iln204.xsl")
)

MARKERS = get_param_default_from_xsl(
    param_name="token-markers", xsl=etree.parse(EXAMPLE_XSL)
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


NAMESPACES = {"xsl": "http://www.w3.org/1999/XSL/Transform"}
XML_MAX_INT = int("2147483647")
