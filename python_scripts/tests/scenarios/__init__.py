from collections.abc import Iterable
from pathlib import Path
from typing import Optional

import pytest
from defusedxml import ElementTree
from lxml import etree

from cbs2folio_transformations._helpers import reraise


def logstring_for_xsl(xslt: etree.XSLT, result: etree.Element) -> str:
    return f"""
    XSLT: {xslt.error_log}

    XML RESULT:
    { etree.tostring(result, encoding="utf-8", pretty_print=True).decode("utf-8") if False else "XML SUPPRESSED"}
    """


def logstring_for_department(ranges: etree.Element, department_code: str) -> str:
    _department = ranges.find(f"department[@code='{department_code}']")
    return (
        etree.tostring(
            _department,
            pretty_print=True,
            encoding="utf-8",
        ).decode("utf-8")
        if not _department is None and len(_department)
        else f"""No matching department for department code {department_code}.

        Known departments are {[_range.attrib["code"] for _range in ranges.findall("department")]}"""
        + """{etree.tostring(ranges, encoding="utf-8").decode("utf-8") if False else "SUPPRESSED RANGES"}"""
    )


class MappingTestCase(dict):
    department_code: str
    epn: str
    signature: str = "SIGNATURE"
    indicator: str = "INDICATOR"
    expected_location: str = "EXPECTED_LOCATION"


@pytest.mark.usefixtures(
    "create_example_and_apply",
)
class Scenario:
    """Base class for test scenarios.

    Raises:
        Exception: _description_
        Exception: _description_
    """

    data_csv_path: Optional[str | Path] = None
    data: Optional[Iterable] = None

    use_numerical: bool = False
    delimiter: str = ";"
    xsl: Optional[etree.ElementTree] = None
    koko_string: Optional[str] = None
    koko_path: Optional[str | Path] = None

    def test_location_assigned(
        self,
        department_code: str,
        signature: str,
        indicator: str,
        epn: int | str,
        expected_location: str,
        xsl: ElementTree,
        create_example_and_apply,
        xslt,
        hrid: Optional[int],
    ):

        try:
            _result = create_example_and_apply
            _location_node = _result.find(
                "//record/holdingsRecords/arr/i/permanentLocationId"
            )

            try:
                assert not (
                    _location_node is None or _location_node.text is None
                ), f"No location set for signature '{signature}' in department {department_code}. (Expected: {expected_location})"
            except AssertionError as e:
                reraise(
                    e=e,
                    info=logstring_for_xsl(xslt, _result),
                )

        except AssertionError as e:
            reraise(
                e=e,
                info=logstring_for_department(xsl.find("//ranges"), department_code),
            )

    def test_correct_location_assigned(
        self,
        department_code: str,
        signature: str,
        indicator: str,
        epn: int | str,
        expected_location: str,
        xsl: ElementTree,
        create_example_and_apply,
        hrid: Optional[int],
        xslt,
    ):

        _result: etree.Element = create_example_and_apply
        try:
            _location_node = _result.find(
                "//record/holdingsRecords/arr/i/permanentLocationId"
            )
            assert _location_node.text == expected_location

        except AssertionError as e:
            reraise(
                e=e,
                info=logstring_for_xsl(xslt, _result)
                if _result
                else logstring_for_department(xsl.find("//ranges"), department_code),
            )
