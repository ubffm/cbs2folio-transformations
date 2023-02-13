#!/usr/bin/env python3
import io
import logging

import pytest
from cbs2folio_transformations.csv2holdingsxslt import EXAMPLE_XSL
from cbs2folio_transformations.csv2holdingsxslt import limitDictList2rangesXML
from cbs2folio_transformations.csv2holdingsxslt import rangesXML2LimitDictList
from defusedxml import ElementTree
from lxml import etree  # nosec blacklist
from xmldiff import main as xmldiffmain

logger = logging.getLogger()


parser = etree.XMLParser(remove_comments=True)


# TODO
@pytest.mark.xfail
def test_csv2holdingsxslt():
    # TODO remove entries
    with open(EXAMPLE_XSL) as f:
        _tree = ElementTree.parse(f, parser=parser)

    _r = _tree.find("//ranges")

    _ranges_string = etree.tostring(_r, pretty_print=True)
    _ranges_list = rangesXML2LimitDictList(_r)

    # TODO remove empty departments for now
    fromstring_ranges = ElementTree.parse(
        io.BytesIO(_ranges_string), parser=parser
    ).getroot()
    generated_ranges = limitDictList2rangesXML(_ranges_list)
    diff_options = {"ignored_attrs": ["default-location"]}
    diff = xmldiffmain.diff_trees(
        fromstring_ranges, generated_ranges, diff_options=diff_options
    )
    min_range = min(len(fromstring_ranges), len(generated_ranges))
    for i in range(min_range):
        assert (  # nosec assert_used
            fromstring_ranges[i].tag == generated_ranges[i].tag
            and (
                fromstring_ranges[i].attrib["location"]
                == generated_ranges[i].attrib["location"]
            )
            if fromstring_ranges[i].tag in ["prefix", "range"]
            else True
        ), f"""Difference between ranges {
            etree.tostring(
                fromstring_ranges[i], pretty_print=True, encoding="utf-8"
            ).decode("utf-8")
            } and {
                etree.tostring(
                generated_ranges[i], pretty_print=True, encoding="utf-8"
            ).decode("utf-8")},"""

    if min_range < len(fromstring_ranges):
        raise AssertionError(
            "\n".join(
                [
                    etree.tostring(fromstring_ranges[i]).decode("utf-8")
                    for i in range(
                        min_range,
                        max(len(fromstring_ranges), len(generated_ranges)),
                    )
                ]
                + ["were not encoded"]
            )
        )

    print(diff)
