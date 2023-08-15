import pytest
from cbs2folio_transformations.csv2holdingsxslt import EXAMPLE_XSL
from defusedxml import ElementTree  # type: ignore[import]
from lxml import etree  # nosec blacklist


class TestSimpleILN204:
    xsl = ElementTree.parse(EXAMPLE_XSL)
    use_numerical = False
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

    @pytest.fixture
    def xslt_fixture(
        self,
    ):
        return etree.XSLT(etree.parse(EXAMPLE_XSL))
