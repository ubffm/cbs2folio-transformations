"""Module for test scenarios."""
from collections.abc import Iterable
from pathlib import Path
from typing import Optional

from cbs2folio_transformations._helpers import reraise
from lxml import etree  # nosec blacklist


def logstring_for_xsl(xslt: etree.XSLT, result: etree._Element) -> str:
    """Create logging information for transformation and data.

    Args:
        xslt (etree._XSLTProcessingInstruction): Transformation
        result (etree.Element): Element of transformed data

    Returns:
        str: logging information
    """
    # TODO: Fix the type
    _error_log: str = xslt.error_log  # type: ignore[attr-defined]

    return f"""
    XSLT: {_error_log}

    XML RESULT:
    {
        etree
        .tostring(result, encoding="utf-8", pretty_print=True)
        .decode("utf-8")
        if False
        else "XML SUPPRESSED"
    }
    """


def logstring_for_department(
    ranges: etree._Element, department_code: str
) -> str:
    """Create logging information for mapping.

    Args:
        ranges (etree.Element): XML Element containing the ranges
        department_code (str): Identifier of the department

    Returns:
        str: logging information
    """
    _department = ranges.find(f"department[@code='{department_code}']")
    return (
        etree.tostring(
            _department,
            pretty_print=True,
            encoding="utf-8",
        ).decode("utf-8")
        if _department is not None and len(_department)
        else f"""No matching department for department code {department_code}.

        Known departments are {
            [_range.attrib["code"] for _range in ranges.findall("department")]
        }"""
        + f"""{
            etree
            .tostring(ranges, encoding="utf-8")
            .decode("utf-8")
            if False
            else "SUPPRESSED RANGES"
            }"""
    )


class Scenario:
    """Base class for test scenarios."""

    data_csv_path: Optional[str | Path] = None
    data: Optional[Iterable] = None

    use_numerical: bool = False
    delimiter: str = ";"
    xsl: Optional[etree._ElementTree] = None
    koko_string: Optional[str] = None
    koko_path: Optional[str | Path] = None

    def test_location_assigned(
        self,
        department_code: str,
        signature: str,
        indicator: str,
        epn: int | str,
        expected_location: str,
        xsl: etree._ElementTree,
        create_example_and_apply_for_step_4: etree._Element,
        xslt: etree._XSLTProcessingInstruction,
        hrid: Optional[int],
    ):
        """Test for existence of location.

        Args:
            department_code (str): Identifier of the department
            signature (str): Signature of the record
            indicator (str): Status indicator
            epn (int | str): Identifier of the "exemplar"
            expected_location (str): expected location of the "exemplar"
            xsl (ElementTree): XML tree containing the transformation
            create_example_and_apply_for_step_4 (etree.Element):
                transformed entry
            xslt (etree._XSLTProcessingInstruction): Transformation
            hrid (Optional[int]): HEBIS wide identifier. Defaults to None.
        """
        try:
            _result = create_example_and_apply_for_step_4
            _location_node = _result.find(
                "//record/holdingsRecords/arr/i/permanentLocationId"
            )

            try:
                assert not (  # nosec assert_used
                    _location_node is None or _location_node.text is None
                ), f"""No location set for signature '{
                    signature
                    }' in department {
                    department_code
                    }. (Expected: {
                    expected_location
                    })"""
            except AssertionError as e:
                reraise(
                    e=e,
                    info=logstring_for_xsl(xslt, _result),
                )

        except AssertionError as e:
            ranges = xsl.find("//ranges")
            assert ranges is not None  # nosec assert_used
            reraise(
                e=e,
                info=logstring_for_department(
                    ranges=ranges, department_code=department_code
                ),
            )

    def test_correct_location_assigned(
        self,
        department_code: str,
        signature: str,
        indicator: str,
        epn: int | str,
        expected_location: str,
        xsl: etree._ElementTree,
        create_example_and_apply_for_step_4,
        hrid: Optional[int],
        xslt,
    ):
        """Test for correctness of location.

        Args:
            department_code (str): Identifier of the department
            signature (str): Signature of the record
            indicator (str): Status indicator
            epn (int | str): Identifier of the "exemplar"
            expected_location (str): expected location of the "exemplar"
            xsl (ElementTree): XML tree containing the transformation
            create_example_and_apply_for_step_4 (etree.Element):
                transformed entry
            xslt (etree._XSLTProcessingInstruction): Transformation
            hrid (Optional[int]): HEBIS wide identifier. Defaults to None.
        """
        _result: etree._Element = create_example_and_apply_for_step_4
        try:
            _location_node = _result.find(
                "//record/holdingsRecords/arr/i/permanentLocationId"
            )
            assert _location_node is not None  # nosec assert_used
            assert (  # nosec assert_used
                _location_node.text == expected_location
            )

        except AssertionError as e:
            ranges = xsl.find("//ranges")
            assert ranges is not None  # nosec assert_used
            reraise(
                e=e,
                info=logstring_for_xsl(xslt, _result)
                if _result
                else logstring_for_department(
                    ranges=ranges, department_code=department_code
                ),
            )
