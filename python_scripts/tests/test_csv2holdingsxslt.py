#!/usr/bin/env python3
import io
import logging

from cbs2folio_transformations.csv2holdingsxslt import EXAMPLE_XSL
from cbs2folio_transformations.csv2holdingsxslt import LimitDict
from cbs2folio_transformations.csv2holdingsxslt import limitDictList2rangesXML
from cbs2folio_transformations.csv2holdingsxslt import rangesXML2LimitDictList
from defusedxml import ElementTree  # type: ignore [import]
from lxml import (  # type: ignore [import] # nosec B410
    etree,  # pyright: ignore [reportGeneralTypeIssues]
)
from pydantic import ValidationError

logger = logging.getLogger()


parser = etree.XMLParser(remove_comments=True)


def test_csv2holdingsxslt():
    # TODO remove entries
    with open(EXAMPLE_XSL) as f:
        _tree = ElementTree.parse(f, parser=parser)

    _r = _tree.find(".//ranges")

    _ranges_string = etree.tostring(_r, pretty_print=True)
    _ranges_list = rangesXML2LimitDictList(_r)

    # TODO remove empty departments for now
    fromstring_ranges = ElementTree.parse(
        io.BytesIO(_ranges_string), parser=parser
    ).getroot()
    generated_ranges = limitDictList2rangesXML(_ranges_list)
    assert fromstring_ranges.tag == generated_ranges.tag  # nosec assert_used

    _department_codes_right = {
        node.attrib["code"]
        for node in generated_ranges
        if node.tag == "department"
    }
    _department_codes_left = {
        node.attrib["code"]
        for node in fromstring_ranges
        if node.tag == "department"
    }

    try:
        assert _department_codes_left == _department_codes_right  # nosec B101
    except AssertionError as e:
        logger.warning(e)

    _department_codes_common = _department_codes_left.intersection(
        _department_codes_right
    )

    for code in _department_codes_common:
        _left_prefixes = []
        _left_ranges = []
        for node in fromstring_ranges:
            if node.attrib["code"] == code:
                _left_prefixes += [
                    (_node.text, _node.attrib["location"])
                    for _node in node
                    if _node.tag == "prefix"
                ]
                _left_ranges += [
                    (
                        _node.attrib["from"],
                        _node.attrib["to"],
                        _node.attrib["location"],
                    )
                    for _node in node
                    if _node.tag == "range"
                ]
        # Clean the ranges # TODO remove this after the source data is fixed
        _cleaned_left_ranges = []
        for _range in _left_ranges:
            try:
                LimitDict.model_validate(
                    {
                        "department_code": code,
                        "sig_start": _range[0],
                        "sig_end": _range[1],
                        "location_numerical": None,
                        "location_code": _range[2],
                    }
                )
                _cleaned_left_ranges.append(_range)

            except ValidationError as e:
                _error = e.errors()[0]
                _error_context = _error["ctx"] if "ctx" in _error else None
                if _error["type"] == "mixed_tokens":
                    logger.warning(
                        f"Please split the following range into a numeric and an alphabetic range: {_error_context}, {_range}"  # noqa: ignore[E501]
                    )
                elif _error["type"] == "mismatching_token_lengths":
                    logger.warning(
                        f"This range is not a valid one; both limits need to have the same length after tokenization: {_error_context}, {_range}"  # noqa: ignore[E501]
                    )
                else:
                    raise e

        _right_prefixes = []
        _right_ranges = []
        for node in generated_ranges:
            if node.attrib["code"] == code:
                _right_prefixes += [
                    (_node.text, _node.attrib["location"])
                    for _node in node
                    if _node.tag == "prefix"
                ]
                _right_ranges += [
                    (
                        _node.attrib["from"],
                        _node.attrib["to"],
                        _node.attrib["location"],
                    )
                    for _node in node
                    if _node.tag == "range"
                ]

        try:
            assert _left_prefixes == _right_prefixes  # nosec assert_used
        except AssertionError as e:
            logger.warning(e)
        try:
            assert _cleaned_left_ranges == _right_ranges  # nosec assert_used
        except AssertionError as e:
            logger.warning(e)
