#!/usr/bin/env python3

from contextlib import suppress
import csv
import logging

from lxml import etree
import pytest

from csv2holidingsxslt import create_holdings_items_xsl_from_csv
from csv2holidingsxslt import create_holdings_items_xsl_from_csv
from csv2holidingsxslt import EXAMPLE_XSL
from test_generation_holding_items import check_permanentLocationId

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
        next(reader)  # remove header
        yield from reader


class TestSimple:
    data = inject_test_data("cbs2folio_holding-items_Testsignaturen_ILN3.txt")
    xslt = etree.XSLT(create_holdings_items_xsl_from_csv())

    def transform(self):
        return etree.XSLT(create_holdings_items_xsl_from_csv())

    @pytest.mark.parametrize("d", data)
    def test_perm(self, d):
        check_permanentLocationId(xslt=self.xslt, **d)


class TestSimpleAll(TestSimple):
    data = inject_test_data("cbs2folio_holding-items_Testsignaturen_ILN3_alle.txt")


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
    xslt = etree.XSLT(etree.parse(EXAMPLE_XSL))
