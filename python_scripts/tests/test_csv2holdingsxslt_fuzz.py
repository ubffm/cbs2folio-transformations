#!/usr/bin/env python3
import io
import logging
from collections.abc import Generator
from typing import List
from typing import Literal
from typing import NamedTuple
from typing import Sequence
from typing import Tuple
from typing import TypeAlias

import pytest
from cbs2folio_transformations._helpers import EXAMPLE_XSL
from cbs2folio_transformations._helpers import get_variable_from_xsl
from cbs2folio_transformations._helpers import MARKERS
from cbs2folio_transformations._helpers import reraise
from cbs2folio_transformations._helpers import tokenize
from cbs2folio_transformations._helpers import VALIDATION_REGEX
from cbs2folio_transformations._helpers import XML_MAX_INT
from cbs2folio_transformations._test_helpers import apply_transformations
from cbs2folio_transformations._test_helpers import create_collection
from cbs2folio_transformations._test_helpers import create_record_from_example
from cbs2folio_transformations.csv2holdingsxslt import (
    create_holdings_items_xsl_from_csv,
)
from hypothesis import given
from hypothesis import note
from hypothesis import settings
from hypothesis.strategies import booleans
from hypothesis.strategies import composite
from hypothesis.strategies import DrawFn
from hypothesis.strategies import integers
from hypothesis.strategies import lists
from hypothesis.strategies import sampled_from
from hypothesis.strategies import shared
from hypothesis.strategies import text
from lxml import etree  # nosec B410

# from hypothesis import reproduce_failure

SignatureTuple = Tuple[str, List[str]]

logger = logging.getLogger()


def get_sort_chars() -> str:
    """Return the sortChars.

    This is done in a function to prevent modifying them.

    Returns:
        str: characters ordered by their sort value
    """
    _sort_chars = get_variable_from_xsl(
        "sortChar",
        xsl=etree.parse(  # nosec B320  # this is a trusted XML file
            EXAMPLE_XSL
        ),
    )
    return _sort_chars


# TODO Evaluate allowing bytes
def filter_numeric(letters: str) -> Generator[str, None, None]:
    for char in letters:
        try:
            int(char)
        except ValueError:
            yield char


ALPHABET: List[str] = list(filter_numeric(get_sort_chars()))


class Case(dict):
    department_code: str
    epn: str
    signature: str = "SIGNATURE"
    indicator: str = "INDICATOR"
    expected_location: str = "EXPECTED_LOCATION"


# https://www.testcult.com/handle-test-data-the-right-way-in-pytest/
TEST_FIELD_NAME = Literal[
    "department_code",
    "epn",
    "signature",
    "indicator",
    "expected_location",
]


@composite
def join_signature_strategy(
    draw: DrawFn,
    tokens: List[str],
    delimiters: Sequence[str] = MARKERS,
) -> str:
    """Join signature tokens using random delimiters.

    Args:
        draw (DrawFn): Hypothesis Draw Function
        tokens (List[str]): List of tokens to use for the signature
        delimiters (List[str], optional): Delimiters to use between tokens. Defaults to ["/","."," "].

    Returns:
        str: Signature string
    """  # noqa: ignore[E501]
    _sig = tokens[0]
    for _token in tokens[1:]:
        _delim = draw(sampled_from(delimiters))
        _sig += _delim + _token
    return _sig


@composite
def format_numeric_token_strategy(draw: DrawFn, token) -> str:
    _token = f"{token}"
    _format = f"0{draw(integers(min_value=len(_token)))}d"
    return f"{int(_token):{_format}}"


@composite
def format_text_token_strategy(draw: DrawFn, token) -> str:
    return "".join(c.upper() if draw(booleans()) else c for c in token.lower())


@composite
def signature_strategy(draw: DrawFn) -> SignatureTuple:
    tokens = draw(
        lists(
            text(
                alphabet=ALPHABET,
                # TODO: Evaluate using a bigger set of allowed characters
                # alphabet=characters(
                #     blacklist_categories=[
                #         # Categories: https://en.wikipedia.org/wiki/Unicode_character_property#General_Categoryu # noqa: ignore[E501]
                #         "Cs",  # Control sequences
                #         "Cc",  # Only supported in UTF-16
                #         "P",  # Punctuation characters
                #     ],
                #     whitelist_categories=[
                #         # Categories: https://en.wikipedia.org/wiki/Unicode_character_property#General_Categoryu# noqa: ignore[E501]
                #         "L",  # Letters
                #         "N",  # Numeric digits
                #     ],
                # ),
                min_size=1,
            ),
            min_size=1,
        )
    )
    signature = draw(join_signature_strategy(tokens))
    return (signature, tokens)


@composite
def draw_higher_char_strategy(draw: DrawFn, char: str, strict: bool = False):
    _sort_chars = get_sort_chars()
    next_chars = _sort_chars.split(char)[1]
    if not strict:
        next_chars += char

    return draw(sampled_from(next_chars))


@composite
def inc_token_strategy(draw: DrawFn, token: int | str) -> str:
    _int_token: int
    _str_token: str
    try:
        _int_token = int(token)
        _offset: int = draw(integers(max_value=XML_MAX_INT - _int_token))
        _str_token = str(_int_token + _offset)

    except ValueError:
        assert isinstance(token, str)  # enforce type # nosec assert_used

        _index = draw(integers(min_value=0, max_value=len(token) - 1))
        _suffix_start = _index + 1  # needed for formatter
        _prefix, _char, _suffix = (
            token[:_index],
            token[_index],
            token[_suffix_start:],
        )
        _incremented_char = draw(draw_higher_char_strategy(_char))
        _str_token = _prefix + _incremented_char + _suffix

    return _str_token


class RangeSampleDict(NamedTuple):
    before_range: str
    range_lower: str
    in_range: str
    range_upper: str
    after_range: str


@composite
def before_range(draw: DrawFn) -> SignatureTuple:
    return draw(signature_strategy())


@pytest.fixture(scope="session")
def department_code() -> str:
    return "001"


@pytest.fixture(scope="session")
def indicator() -> str:
    return "u"


global _epn
_epn: int


@pytest.fixture(scope="session")
def epn() -> Generator[str, None, None]:
    try:
        _epn = (
            _epn + 1  # type: ignore[has-type] # noqa:ignore[F821,F823]
        )  # pyright: ignore=[reportUnboundVariable]
    except UnboundLocalError:
        _epn = 1000
    yield str(_epn)


@composite
def range_strategy(
    draw: DrawFn,
    # before_range: SignatureTuple #Optional[SignatureTuple] = None
) -> RangeSampleDict:
    _before_range_signature, _before_range_tokens = draw(before_range())

    # if before_range is not None:
    #     _before_range_signature, _before_range_tokens = before_range
    # else:
    #     _before_range_signature, _before_range_tokens = before_range

    _index = draw(
        integers(min_value=0, max_value=len(_before_range_tokens) - 1)
    )

    _range_lower_tokens = _before_range_tokens
    try:
        _range_lower_tokens[_index] = draw(
            inc_token_strategy(
                _range_lower_tokens[_index],
            ).filter(lambda x: VALIDATION_REGEX.match(x))
        )
    except IndexError as e:
        reraise(
            e=e,
            info=f"""
        {"|".join(_range_lower_tokens)}
        is str: {isinstance(_range_lower_tokens[0], str)}
        index: {_index}
        len: {len(_range_lower_tokens)}
        """,
        )

    _range_lower_signature = draw(
        join_signature_strategy(tokens=_range_lower_tokens)
    )

    _in_range_tokens = _range_lower_tokens
    _in_range_tokens[_index] = draw(
        inc_token_strategy(_in_range_tokens[_index]).filter(
            lambda x: VALIDATION_REGEX.match(x)
        )
    )
    _in_range_signature = draw(join_signature_strategy(_in_range_tokens))

    _range_upper_tokens = _in_range_tokens
    _range_upper_tokens[_index] = draw(
        inc_token_strategy(_range_upper_tokens[_index]).filter(
            lambda x: VALIDATION_REGEX.match(x)
        )
    )
    _range_upper_signature = draw(join_signature_strategy(_range_upper_tokens))

    _after_range_tokens = _range_upper_tokens
    _after_range_tokens[_index] = draw(
        inc_token_strategy(
            _after_range_tokens[_index],
        ).filter(lambda x: VALIDATION_REGEX.match(x))
    )
    _after_range_signature = draw(join_signature_strategy(_after_range_tokens))

    return RangeSampleDict(
        _before_range_signature,
        _range_lower_signature,
        _in_range_signature,
        _range_upper_signature,
        _after_range_signature,
    )


@composite
def xsl_strategy(draw: DrawFn) -> etree._ElementTree:  # type: ignore[return]
    department_code = draw(
        shared(sampled_from(["000"]), key="department_code")
    )
    range_example = draw(shared(range_strategy(), key="Simple Example"))
    try:
        return create_holdings_items_xsl_from_csv(
            io.StringIO(
                f"""
                {department_code};{range_example.range_lower};{range_example.range_upper};111;MATCH
                """.strip()
            ),
            use_numerical=True,
            delimiter=";",
        )
    except Exception as e:
        reraise(
            e=e,
            info=f"""
        department_code: {department_code}
        range_example: {range_example}
        """,
        )


# TODO
HRID_TYPE: TypeAlias = int
LOCATION_TYPE: TypeAlias = str


@given(
    department_code=shared(sampled_from(["000"]), key="department_code"),
    xsl=xsl_strategy(),
    range_example=shared(range_strategy(), key="Simple Example"),
)
@settings(print_blob=True, max_examples=5000)
def test_match(
    xsl,
    range_example: RangeSampleDict,
    xslt_step1,
    xslt_step2,
    xslt_step3,
    indicator,
    epn,
    hrid,
    department_code,
):
    xslt = etree.XSLT(xsl)

    example_before = create_record_from_example(
        department_code,
        range_example.before_range,
        indicator,
        999,
        hrid,
    )

    example_between = create_record_from_example(
        department_code,
        range_example.in_range,
        indicator,
        1000,
        hrid,
    )

    example_after = create_record_from_example(
        department_code,
        range_example.after_range,
        indicator,
        1001,
        hrid,
    )
    _input: etree._ElementTree = create_collection(
        [
            example_after,
            example_before,
            example_between,
        ]
    )

    note(
        "\n".join(
            [
                etree.tostring(_item, pretty_print=True).decode()
                for _item in _input.findall("/".join(["//metadata/item"]))
            ]
        )
    )

    _result: etree._ElementTree = apply_transformations(
        _input,
        [
            xslt_step1,
            xslt_step2,
            xslt_step3,
            xslt,
        ],
    )

    _location_nodes: list[etree._Element] = _result.findall(
        "//record/holdingsRecords/arr/i/permanentLocationId"
    )
    assert len(_location_nodes) == 3  # nosec: B101

    def _get_parent(x: etree._Element) -> etree._Element:
        parent = x.getparent()  # nosec B101
        assert parent is not None  # nosec B101
        return parent

    def _get_hrid(x: etree._Element) -> str:
        hrid_node = _get_parent(x).find("hrid")
        assert hrid_node is not None  # nosec B101
        hrid = hrid_node.text
        assert hrid is not None  # nosec B101
        return hrid

    def _get_sort_key(x: etree._Element) -> int:
        return int(_get_hrid(x))

    sorted_list = sorted(_location_nodes, key=_get_sort_key)

    try:
        note(
            f"""{'='*10}HRIDs{'='*10}\n"""
            + "\n".join([_get_hrid(_item) for _item in sorted_list])
            + f"""\n{'='*10}SORTED{'='*10}\n"""
            + "\n".join(
                [
                    etree.tostring(
                        _get_parent(_item), pretty_print=True
                    ).decode()
                    for _item in sorted_list
                ]
            )
        )

        expected_results = [
            "111"
            if tokenize(range_example.before_range)
            == tokenize(range_example.range_lower)
            else None,
            "111",
            "111"
            if tokenize(range_example.after_range)
            == tokenize(range_example.range_upper)
            else None,
        ]
        assert [  # nosec: B101
            _node.text for _node in sorted_list
        ] == expected_results
    except AssertionError as e:
        _error_log: str = xslt.error_log  # type: ignore[attr-defined]
        note(_error_log)
        reraise(e=e, info="")


class Fuzz:
    ...

    def test_lower(self):
        ...
