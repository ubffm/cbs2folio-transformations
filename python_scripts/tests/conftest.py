"""Testtooling."""
import io
import logging
import pathlib
from collections.abc import Iterable
from typing import Optional
from typing import TypeVar

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
from defusedxml import ElementTree
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
            with open(metafunc.cls.koko_path, encoding="utf-8") as f:
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

    if (
        hasattr(metafunc.cls, "data_csv_path")
        and metafunc.cls.data_csv_path is not None
    ):
        _data: Iterable[SignatureExample] = inject_test_data(
            metafunc.cls.data_csv_path
        )
    elif hasattr(metafunc.cls, "data") and metafunc.cls.data is not None:
        _data: Iterable[
            SignatureExample
        ] = yield_signature_example_from_data_iterable(metafunc.cls.data)
    else:
        raise ValueError("No data specified.")

    for d in _data:
        _dict = {
            k: v
            for k, v in d.dict(by_alias=True).items()
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


@pytest.fixture()
def initial_record() -> etree.Element:
    """Create an record Element from the EXAMPLE_XML.

    Returns:
        etree.Element: 'record'-Element
    """
    parser = etree.XMLParser(remove_blank_text=True)

    with open(EXAMPLE_XML) as f:
        _tree: ElementTree = ElementTree.parse(f, parser=parser)

    _record = _tree.find(".//record")
    return _record


@pytest.fixture()
def record_from_example(
    initial_record,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    hrid: Optional[int] = None,
) -> etree._Element:
    """Replace the minimum parameters of the record.

    Args:
        initial_record (etree.Element): Example record
        department_code (str): Identifier of the department
        signature (str): Signature of the record
        indicator (str): Status indicator
        epn (int | str): Indentifier of the "exemplar"
        hrid (Optional[int]): HEBIS wide identifier. Defaults to None.

    Returns:
        etree._Element: Element containing the information
    """
    return create_record_from_example(
        initial_record,
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
) -> etree.Element:
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


TreeOrElement = TypeVar("TreeOrElement", etree.Element, etree.ElementTree)


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
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
def xslt(xsl: etree.Element) -> etree.XSLT:
    """Generate an transformation from an XSL.

    Args:
        xsl (etree.Element): XML describing the transformation

    Returns:
        etree.XSLT: Transformation
    """
    return etree.XSLT(xsl)


@pytest.fixture()
def hrid() -> Optional[int]:
    """Fixture to ensure an hrid is always provided.

    Returns:
        (Optional[int]): HEBIS wide identifier. Defaults to None.
    """
    return None


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
    hrid: Optional[int] = None,
) -> etree.Element:
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
        hrid (Optional[int]): HEBIS wide identifier. Defaults to None.

    Raises:
        etree.XSLTApplyError: Error applying the transformation

    Returns:
        etree.Element: transformed entry
    """
    _input = create_collection([record_from_example])
    return apply_transformations(
        _input, [xslt_step1, xslt_step2, xslt_step3, xslt]
    )
