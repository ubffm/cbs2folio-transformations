#!/usr/bin/env python3
"""Testtooling."""
import io
import logging
import pathlib
from collections.abc import Iterable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import pytest
from cbs2folio_transformations._test_helpers import apply_transformations
from cbs2folio_transformations._test_helpers import create_collection
from cbs2folio_transformations._test_helpers import create_record
from cbs2folio_transformations._test_helpers import create_record_from_example
from cbs2folio_transformations._test_helpers import EXAMPLE_XML
from cbs2folio_transformations._test_helpers import inject_test_data
from cbs2folio_transformations._test_helpers import SignatureExample
from cbs2folio_transformations._test_helpers import (
    yield_signature_example_from_data_iterable,
)
from cbs2folio_transformations.csv2holdingsxslt import (
    create_holdings_items_xsl_from_csv,
)
from defusedxml import ElementTree  # type: ignore[import]
from lxml import etree  # nosec blacklist

logger = logging.getLogger()


# Source https://docs.pytest.org/en/6.2.x/example/parametrize.html#paramexamples  # noqa: E501
def pytest_generate_tests(metafunc: pytest.Metafunc):
    """Generate the tests by iterating on the Scenario classes.

    Args:
        metafunc (pytest.Metafunc): pytest fixture

    Raises:
        ValueError: No transformation has been defined
        ValueError: No data has been defined
    """
    argvalues = []

    argnames = ["d", "xsl"]

    if metafunc.cls is None:
        return

    if hasattr(metafunc.cls, "xsl") and metafunc.cls.xsl is not None:
        _xsl = metafunc.cls.xsl
    elif (
        hasattr(metafunc.cls, "koko_string")
        and metafunc.cls.koko_string is not None
    ):
        _xsl = create_holdings_items_xsl_from_csv(
            io.StringIO(metafunc.cls.koko_string),
            use_numerical=metafunc.cls.use_numerical,
            delimiter=metafunc.cls.delimiter,
        )

    elif (
        hasattr(metafunc.cls, "koko_path")
        and metafunc.cls.koko_path is not None
    ):
        try:
            with open(
                metafunc.cls.koko_path,
                encoding=getattr(metafunc.cls, "koko_encoding", "utf-8"),
            ) as f:
                _xsl = create_holdings_items_xsl_from_csv(
                    f,
                    use_numerical=metafunc.cls.use_numerical,
                    delimiter=metafunc.cls.delimiter,
                )
        except UnicodeDecodeError:
            with open(metafunc.cls.koko_path, encoding="ISO-8859-1") as f:
                _xsl = create_holdings_items_xsl_from_csv(
                    f,
                    use_numerical=metafunc.cls.use_numerical,
                    delimiter=metafunc.cls.delimiter,
                )
    else:
        raise ValueError("No XSL specified.")

    metafunc.cls.xsl = _xsl

    _data: Iterable[SignatureExample]
    if (
        hasattr(metafunc.cls, "data_csv_path")
        and metafunc.cls.data_csv_path is not None
    ):
        _data = inject_test_data(
            metafunc.cls.data_csv_path,
            encoding=getattr(metafunc.cls, "data_encoding", "utf-8"),
        )
    elif hasattr(metafunc.cls, "data") and metafunc.cls.data is not None:
        _data = yield_signature_example_from_data_iterable(metafunc.cls.data)
    else:
        raise ValueError("No data specified.")

    for d in _data:
        _dict = {
            k: v
            for k, v in d.model_dump(by_alias=True).items()
            if k not in ["id", "marks"]
        }
        argnames = list(_dict.keys()) + ["xsl"]
        argvalues.append(
            pytest.param(*_dict.values(), _xsl, marks=d.marks, id=d.example_id)
        )

    metafunc.parametrize(
        argnames,
        argvalues,
        scope="class",
    )


@pytest.fixture(scope="session")
def initial_record() -> etree._Element:
    """Create an record Element from the EXAMPLE_XML.

    Returns:
        etree.Element: 'record'-Element
    """
    parser = etree.XMLParser(remove_blank_text=True)

    with open(EXAMPLE_XML) as f:
        _tree: etree._ElementTree = ElementTree.parse(f, parser=parser)

    _record = _tree.find(".//record")
    if _record is None:
        raise ValueError(
            f"Could not find 'record' in {etree.tostring(_tree).decode()}"
        )
    return _record


@pytest.fixture()
def record_from_example(
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    hrid: Optional[int] = None,
) -> etree._Element:
    """Replace the minimum parameters of the record.

    Args:
        department_code (str): Identifier of the department
        signature (str): Signature of the record
        indicator (str): Status indicator
        epn (int | str): Indentifier of the "exemplar"
        hrid (Optional[int]): HEBIS wide identifier. Defaults to None.

    Returns:
        etree._Element: Element containing the information
    """
    return create_record_from_example(
        department_code,
        signature,
        indicator,
        epn,
        hrid,
    )


@pytest.fixture()
def record(
    department_code: str,
    signature: str,
    indicator: str,
    location: Optional[str] = "LOCATION",
) -> etree._Element:
    """Create a record from nothing.

    Args:
        department_code (str): Identifier of the department
        signature (str): Signature of the record
        indicator (str): Status indicator
        location (Optional[str]):
            Location of the "exemplar". Defaults to "LOCATION".

    Returns:
        etree._Element: Element containing the information
    """
    return create_record(
        department_code,
        signature,
        indicator,
        location,
    )


@pytest.fixture(scope="session")
def xslt_step1() -> etree.XSLT:
    """Return the transformation for the 1st step.

    Returns:
        etree.XSLT: Transformation for the 1st step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/pica2instance-new.xsl")
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture(scope="session")
def xslt_step2() -> etree.XSLT:
    """Return the transformation for the 2nd step.

    Returns:
        etree.XSLT: Transformation for the 2nd step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/relationships.xsl")
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture(scope="session")
def xslt_step3() -> etree.XSLT:
    """Return the transformation for the 3rd step.

    Returns:
        etree.XSLT: Transformation for the 3rd step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(
            "../../hebis/holdings-items-hebis.xsl"
        ),  # TODO Check "hebis/holdings-items-hebis-hrid-test.xsl"
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture(scope="session")
def xslt_step4(iln: int) -> etree.XSLT:
    """Return the transformation for the 4th step.

    Args:
        iln (int): ILN of the library to apply for

    Returns:
        etree.XSLT: Transformation for the 4th step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/holding-items-hebis-iln{iln}.xsl"),
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture(scope="session")
def xslt_step5() -> etree.XSLT:
    """Return the transformation for the 5th step.

    Returns:
        etree.XSLT: Transformation for the 5th step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/codes2uuid-hebis.xsl"),
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture(scope="session")
def xslt_step6(iln: int) -> etree.XSLT:
    """Return the transformation for the 6th step.

    Args:
        iln (int): ILN of the library to apply for

    Returns:
        etree.XSLT: Transformation for the 6th step
    """
    with open(
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/codes2uuid-hebis-iln{iln}.xsl"),
    ) as f:
        _xslt: etree.XSLT = etree.XSLT(etree.parse(f))
    return _xslt


@pytest.fixture()
def xslt(xsl: "etree._ElementOrTree") -> etree.XSLT:
    """Generate an transformation from an XSL.

    Args:
        xsl (etree.Element): XML describing the transformation

    Returns:
        etree.XSLT: Transformation
    """
    return etree.XSLT(xsl)


@pytest.fixture(scope="session")
def hrid() -> Optional[int]:
    """Fixture to ensure an hrid is always provided.

    Returns:
        (Optional[int]): HEBIS wide identifier. Defaults to None.
    """
    return None


@pytest.fixture
def xslt_debug_level():
    """Set the debug level for the XSL transformation."""
    return etree.XSLT.strparam("0")


@pytest.fixture()
def create_example_and_apply_for_step_4(
    xslt: etree._XSLTProcessingInstruction,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    expected_location: str,
    record_from_example: etree._Element,
    xslt_step1: etree.XSLT,
    xslt_step2: etree.XSLT,
    xslt_step3: etree.XSLT,
    xslt_debug_level,
    hrid: Optional[int] = None,
) -> etree._ElementTree | etree._Element:
    """Create an example using the parameters and apply the transformation.

    Args:
        xslt (etree._XSLTProcessingInstruction): Transformation
        department_code (str): Identifier of the department
        signature (str): Signature of the record
        indicator (str): Status indicator
        epn (int | str): Indentifier of the "exemplar"
        expected_location (str): expected location of the "exemplar"
        record_from_example (etree._Element): XML record
        xslt_step1 (etree.XSLT): transformation for 1st step
        xslt_step2 (etree.XSLT): transformation for 2nd step
        xslt_step3 (etree.XSLT): transformation for 3rd step
        hrid (Optional[int]): HeBIS wide identifier. Defaults to None.

    Raises:
        etree.XSLTApplyError: Error applying the transformation

    Returns:
        etree.Element: transformed entry
    """
    _input = create_collection([record_from_example])
    _tmp = apply_transformations(
        _input,
        [xslt_step1, xslt_step2, xslt_step3],
    )
    try:
        _result = xslt(
            _tmp, **{"debug-template-logic-verbosity": xslt_debug_level}
        )
        if hasattr(xslt, "error_log"):
            logger.error(xslt.error_log)
        return _result
    except etree.XSLTApplyError as e:
        logger.error(e.args)

        logger.error(e)
        raise


def _compare_eq_etree_Element_department(
    left: etree._Element, right: etree._Element, verbose: int = 0
) -> List[str]:
    explanation: List[str] = []
    assert left.attrib["code"] == right.attrib["code"]  # nosec: ignore[B101]

    explanation += [f"Difference in department {str(left.attrib['code'])}:"]

    _left_prefixes: Dict[str, etree._Element] = {
        node.text: node for node in left if node.tag == "prefix" and node.text
    }
    _right_prefixes: Dict[str, etree._Element] = {
        node.text: node for node in right if node.tag == "prefix" and node.text
    }

    if _extra_prefixes_left := _left_prefixes.keys() - _right_prefixes.keys():
        explanation += [f"Extra prefixes in {left}"]
        explanation += [
            str(_left_prefixes[prefix]) for prefix in _extra_prefixes_left
        ]

    if _extra_prefixes_right := _right_prefixes.keys() - _left_prefixes.keys():
        explanation += [f"Extra prefixes in {right}"]
        explanation += [
            str(_right_prefixes[prefix]) for prefix in _extra_prefixes_right
        ]

    _common_prefixes: Set[str] = set(_left_prefixes.keys()).intersection(
        _right_prefixes.keys()
    )

    if _common_prefixes:
        explanation += ["Differences in prefixes:"]
        explanation += [
            f"Different location for {prefix}: {_location_left!r} != {_location_right!r}"  # noqa: E501
            for prefix in _common_prefixes
            if (_location_left := _left_prefixes[prefix].attrib["location"])
            != (_location_right := _right_prefixes[prefix].attrib["location"])
        ]

    def _create_range_repr(node: etree._Element) -> str:
        _from = node.attrib["from"]
        _to = node.attrib["to"]
        return f"{_from!s}---{_to!s}"

    _left_ranges = {
        _create_range_repr(node): node for node in left if node.tag == "range"
    }
    _right_ranges = {
        _create_range_repr(node): node for node in right if node.tag == "range"
    }

    def _repr_range(range: etree._Element) -> str:
        return f"{range.tag}: {range.attrib}"

    if _extra_ranges_left := _left_ranges.keys() - _right_ranges.keys():
        explanation += [f"Extra ranges in {left}"]
        explanation += [
            _repr_range(_left_ranges[range]) for range in _extra_ranges_left
        ]

    if _extra_ranges_right := _right_ranges.keys() - _left_ranges.keys():
        explanation += [f"Extra ranges in {right}"]
        explanation += [
            _repr_range(_right_ranges[range]) for range in _extra_ranges_right
        ]

    _common_ranges: Set[str] = set(_left_ranges.keys()).intersection(
        _right_ranges.keys()
    )

    if _common_ranges:
        explanation += ["Differences in ranges:"]
        explanation += [
            f"Different location for {range}: {_location_left!r} != {_location_right!r}"  # noqa: E501
            for range in _common_ranges
            if (_location_left := _left_ranges[range].attrib["location"])
            != (_location_right := _right_ranges[range].attrib["location"])
        ]
    return explanation


def _compare_eq_etree_Element_ranges(
    left: etree._Element, right: etree._Element, verbose: int = 0
) -> List[str]:
    explanation: List[str] = []

    explanation += [
        f"  {left} != {right}",
    ]

    if left.tag != right.tag:
        explanation += [f"Differing tags: {left.tag} != {right.tag}"]

    if left.attrib != right.attrib:
        explanation += [
            f"Differing attributes: {left.attrib} != {right.attrib}"
        ]

    _left_departments: Dict[str, etree._Element] = {
        str(node.attrib["code"]): node
        for node in left
        if node.tag == "department"
    }
    _right_departments: Dict[str, etree._Element] = {
        str(node.attrib["code"]): node
        for node in right
        if node.tag == "department"
    }

    _extra_departments_left = (
        _left_departments.keys() - _right_departments.keys()
    )
    _extra_departments_right = (
        _right_departments.keys() - _left_departments.keys()
    )

    def _repr_department(department: etree._Element) -> str:
        return f"{department.tag}: {department.attrib}"

    if _extra_departments_left:
        explanation += [f"Extra departments in {left}:"]
        explanation += [
            _repr_department(_left_departments[code])
            for code in _extra_departments_left
        ]

    if _extra_departments_right:
        explanation += [f"Extra departments in {right}:"]
        explanation += [
            _repr_department(_right_departments[code])
            for code in _extra_departments_right
        ]

    _common_departments = set(_left_departments.keys()).intersection(
        set(_right_departments.keys())
    )

    explanation += ["Differences in departments:"]

    if _common_departments:
        for code in _common_departments:
            if _left_departments[code] != _right_departments[code]:
                explanation += _compare_eq_etree_Element_department(
                    _left_departments[code],
                    _right_departments[code],
                    verbose,
                )

    _left_children: Set[etree._Element] = {
        node for node in left if node.tag != "department"
    }
    _right_children: Set[etree._Element] = {
        node for node in right if node.tag != "department"
    }
    if _left_children != _right_children:
        if _extra_left := _left_children - _right_children:
            explanation += ["Extra children in left:"]
            explanation += [
                etree.tostring(child).decode() for child in _extra_left
            ]

        if _extra_right := _right_children - _left_children:
            explanation += ["Extra children in right:"]
            explanation += [
                etree.tostring(child).decode() for child in _extra_right
            ]

    return explanation


def _compare_eq_etree_Element(
    left: etree._Element, right: etree._Element, verbose: int = 0
) -> List[str]:
    """Comparison explanation for Etree._Element objects.

    Based on code from pytest.

    Args:
        left (etree._Element): left XML Node.
        right (etree._Element): right XML Node.
        verbose (int, optional): level of verbosity. Defaults to 0.

    Returns:
        List[str]: Explanation of the difference in nodes.
    """
    explanation: List[str] = []

    explanation += [
        f"  {left} != {right}",
    ]

    if left.tag != right.tag:
        explanation += [f"Differing tags: {left.tag} != {right.tag}"]
    elif left.tag == "ranges":
        explanation += _compare_eq_etree_Element_ranges(left, right, verbose)

    return explanation


def pytest_assertrepr_compare(
    op, left, right, verbose: int = 0
) -> List[str] | None:  # noqa: ignore[C901]
    """Create a proper representation for comparison.

    Args:
        op (str): comparison operator.
        left (Any): left object.
        right (_type_): right object.
        verbose (int, optional): Level of verbosity. Defaults to 0.

    Returns:
        List[str] | None: Explanation of the differences between left and right.
    """  # noqa: E501
    if (
        op == "=="
        and isinstance(left, etree._Element)
        and isinstance(right, etree._Element)
    ):
        return _compare_eq_etree_Element(left, right, verbose)

    logger.warning(f"No dedicated representation for {left}, {right}, {op}")
    return None
