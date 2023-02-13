#!/usr/bin/env python3
import csv
import logging
import pathlib
from typing import Optional

from cbs2folio_transformations.csv2holdingsxslt import EXAMPLE_XSL
from defusedxml import ElementTree
from lxml import etree

logger = logging.getLogger()


# https://www.testcult.com/handle-test-data-the-right-way-in-pytest/
def inject_test_data(file):
    with open(file) as csvfile:
        reader = csv.DictReader(
            csvfile,
            fieldnames=[
                "department_code",
                "epn",
                "signature",
                "indicator",
                "expected_location",
            ],
            delimiter=";",
        )
        yield from reader


class TestSimple:
    use_numerical = True
    delimiter = ";"
    data = inject_test_data(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("scenarios/iln3/cbs2folio_holding-items_Testsignaturen_ILN3.txt")
    )
    koko_path = (
        pathlib.Path(__file__).parent.resolve().joinpath("scenarios/iln3/koko174.csv")
    )

    def test_perm(
        self,
        create_example_and_apply: etree.Element,
        department_code: str,
        signature: str,
        indicator: str,
        epn: int | str,
        expected_location: str,
        xsl: ElementTree,
        hrid: Optional[int],
    ):
        _result = create_example_and_apply

        _location_node = _result.find(
            "//record/holdingsRecords/arr/i/permanentLocationId"
        )

        try:
            assert not (
                _location_node is None or _location_node.text is None
            ), f"No location set for signature '{signature}' in department {department_code}. (Expected: {expected_location})"
        except Exception as e:
            e.args = (
                # logstring_for_xsl(xslt, _result),
            ) + e.args
            raise e.with_traceback(e.__traceback__)


# class TestSimpleAll(TestSimple):
#     data = inject_test_data(
#         pathlib.Path(__file__)
#         .parent.resolve()
#         .joinpath("scenarios/iln3/cbs2folio_holding-items_Testsignaturen_ILN3_alle.txt")
#     )


class TestSimpleILN204(TestSimple):
    data = [
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": "BAp 27,Jünger 2003",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "ILN204/CG/UB/UBMag3",
        },
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": "BAp 27,Jünger 2003",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "ILN204/CG/UB/UBMag3",
        },
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": "BAp 28,Jünger 2003",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "ILN204/CG/UB/UBMagAltbau",
        },
    ]
    xsl = etree.parse(EXAMPLE_XSL)
