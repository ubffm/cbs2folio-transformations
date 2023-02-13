#!/usr/bin/env python3
import logging
from typing import Optional

import pytest
from lxml import etree  # nosec blacklist
from xmldiff import main as xmldiffmain

logger = logging.getLogger()


@pytest.mark.xfail(reason="Not fully implemented yet")
@pytest.mark.parametrize(
    "department_code, signature, indicator",
    [
        ("111", "pap 21321", "u"),
        ("000", "2o zz 1", "u"),
        ("000", "BAp 27,Kopernicus-3", "u"),
        ("000", "BAp 27,Jünger 2003", "u"),
        ("000", "BAp 27,Calderon de la Barca-2,2", "u"),
    ],
)
def test_create_record(department_code, signature, indicator, record):
    _record_string = etree.tostring(
        record, encoding="utf-8", pretty_print=True
    )

    assert signature.encode("utf-8") in _record_string  # nosec assert_used
    assert (  # nosec assert_used
        record.find("metadata/item/datafield[@tag='209A']/subfield[@code='d']")
        is not None
    ), _record_string.decode("utf-8")
    assert (  # nosec assert_used
        record.find(
            "metadata/item/datafield[@tag='209A']/subfield[@code='d']"
        ).text
        == indicator
    )
    assert (  # nosec assert_used
        record.find(
            "metadata/item/datafield[@tag='209A']/subfield[@code='a']"
        ).text
        == signature
    )
    assert (  # nosec assert_used
        record.find(
            "metadata/item/datafield[@tag='209A']/subfield[@code='f']"
        ).text
        == department_code
    )


@pytest.mark.parametrize(
    "department_code, signature, indicator, epn, hrid",
    [
        ("000", "BAp 27,Jünger 2003", "u", 184727820, 109962869),
        (
            "000",
            "BAp 27,Calderon de la Barca-2,2",
            "u",
            "21028126X",
            116105488,
        ),
        ("000", "BAp 27,Kopernicus-3", "u", "34203166X", 122359909),
    ],
)
def test_create_record_initial(
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    hrid: Optional[int],
    record_from_example: etree.Element,
):
    _record_string = etree.tostring(
        record_from_example, encoding="utf-8", pretty_print=True
    )

    assert signature.encode("utf-8") in _record_string  # nosec assert_used
    assert (  # nosec assert_used
        _datafield := record_from_example.find(
            "metadata/item/datafield[@tag='209A']"
        )
    ) is not None, _record_string
    _datafield_string = etree.tostring(
        _datafield, encoding="utf-8", pretty_print=True
    ).decode("utf-8")
    assert (  # nosec assert_used
        _datafield.find('subfield[@code="d"]') is not None
    ), _datafield_string
    assert (  # nosec assert_used
        _datafield.find("subfield[@code='d']").text == indicator
    )
    assert (  # nosec assert_used
        _datafield.find("subfield[@code='a']").text == signature
    )
    assert (  # nosec assert_used
        _datafield.find("subfield[@code='f']").text == department_code
    )


@pytest.mark.xfail
@pytest.mark.parametrize(
    "department_code, signature, indicator, epn, hrid",
    [
        ("000", "BAp 27,Jünger 2003", "u", 184727820, 109962869),
        (
            "000",
            "BAp 27,Calderon de la Barca-2,2",
            "u",
            "21028126X",
            116105488,
        ),
        ("000", "BAp 27,Kopernicus-3", "u", "34203166X", 122359909),
    ],
)
def test_equiv(
    department_code,
    signature,
    indicator,
    epn,
    hrid,
    initial_record,
    record,
    record_from_example,
):
    # TODO do proper testing
    _record_a = record
    _record_b = record_from_example

    diff_options = {"F": 0.5, "ratio_mode": "accurate"}

    diff_a_b = xmldiffmain.diff_trees(
        _record_a, _record_b, diff_options=diff_options
    )
    diff_a_orig = xmldiffmain.diff_trees(
        _record_a, initial_record, diff_options=diff_options
    )
    diff_b_orig = xmldiffmain.diff_trees(
        _record_b, initial_record, diff_options=diff_options
    )

    assert diff_a_b  # nosec assert_used
    assert diff_a_orig  # nosec assert_used
    assert diff_b_orig  # nosec assert_used
