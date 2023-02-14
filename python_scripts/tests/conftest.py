"""Testtooling."""
import csv
import io
import logging
import pathlib
from collections.abc import Generator
from collections.abc import Iterable
from copy import deepcopy
from os import PathLike
from typing import Any
from typing import Collection
from typing import get_args
from typing import Literal
from typing import Optional
from typing import TypeVar
from typing import Union

import pytest
from cbs2folio_transformations._helpers import reraise
from cbs2folio_transformations.csv2holdingsxslt import (
    create_holdings_items_xsl_from_csv,
)
from defusedxml import ElementTree
from lxml import etree  # nosec blacklist
from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger()


# https://www.testcult.com/handle-test-data-the-right-way-in-pytest/
TEST_FIELD_NAME = Literal[
    "department_code",
    "epn",
    "signature",
    "indicator",
    "expected_location",
]


class SignatureExample(BaseModel):
    """Datamodel for signature testcases."""

    department_code: str
    epn: str
    signature: str = Field(...)
    indicator: str
    expected_location: str
    example_id: str = Field(..., alias="id")
    marks: Collection[pytest.MarkDecorator]

    class Config:  # noqa: D106
        arbitrary_types_allowed = True
        allow_population_by_field_name = True


def yield_signature_example_from_data_iterable(
    data: Iterable,
    marks: Union[
        pytest.MarkDecorator,
        Collection[Union[pytest.MarkDecorator, pytest.Mark]],
    ] = (),
) -> Generator[SignatureExample, None, None]:
    """Create parameters for testcases.

    This handles creating an id, and marking cases that won't work.

    Args:
        data (Iterable):
        marks (Union[
            pytest.MarkDecorator,
            Collection[Union[pytest.MarkDecorator, pytest.Mark]]
            ], optional): Marks. Defaults to ().

    Yields:
        Generator[SignatureExample, None, None]: Generator for examples
    """
    for d in data:
        _marks = (
            [marks]
            if isinstance(marks, pytest.MarkDecorator)
            else [m for m in marks]
        )

        if "signature" in d:
            _sig: str = d["signature"]
            _dep: str = d["department_code"]
            _loc: str = d["expected_location"]
            if len(_dep) != 3:
                _marks.append(
                    pytest.mark.xfail(
                        reason=f"'{_dep}' is not a proper department code"
                    )
                )

            if _sig.startswith("Ausgesondert"):
                _marks.append(
                    pytest.mark.xfail(reason=f"'{_sig}' is Ausgesondert")
                )

            # FIXME
            BAD_SIG_LIST: Iterable[str] = [
                "67/557",
                "ZB: 84/KU Al 20 ",
            ]
            if _sig in BAD_SIG_LIST:
                _marks.append(
                    pytest.mark.xfail(reason=f"'{_sig}' is known bad example")
                )

            yield SignatureExample.parse_obj(
                {
                    **d,
                    "id": f"{_sig}@{_dep}->{_loc}",
                    "marks": _marks,
                }
            )


def inject_test_data(
    filename: str | PathLike | pathlib.Path,
) -> Generator[SignatureExample, None, None]:
    """Yield testdata from file.

    Args:
        file (str | PathLike | pathlib.Path):
            path to file containing testcases

    Yields:
        Generator[SignatureExample, None, None]: Generator for examples
    """
    with open(filename) as csvfile:
        reader: csv.DictReader[TEST_FIELD_NAME] = csv.DictReader(
            csvfile,
            fieldnames=get_args(TEST_FIELD_NAME),
            delimiter=";",
            restkey="additional_values",
        )

        yield from yield_signature_example_from_data_iterable(reader)


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


# TODO add stricter typing
# Collection = object
Record = Any


def create_collection(elements: list[Record]) -> etree.ElementTree:
    """Create an XML-Collection of records.

    Args:
        elements (list[Record]): Records to be used

    Returns:
        etree.ElementTree: XML-tree containing the records
    """
    collection = etree.Element("collection")

    for r in elements:
        if r is not None:
            collection.append(r)

    return etree.ElementTree(collection)


def create_signature(
    department_code: str, signature: str, indicator: str
) -> etree._Element:
    """Create an datafield for the signature.

    Args:
        department_code (str): Identifier of the department
        signature (str): Signature of the record
        indicator (str): Status indicator

    Returns:
        etree._Element: 'datafield' containing the parameters
    """
    _datafield_signature = etree.Element(
        "datafield",
        attrib={
            "tag": "209A",
            "occurence": "01",
            "fulltag": "209A/01",
        },
    )
    # Signaturenkategorie 7100
    _signature_category = etree.Element("subfield", attrib={"code": "x"})
    _signature_category.text = "00"
    _department = etree.Element("subfield", attrib={"code": "f"})
    _department.text = department_code
    _indicator = etree.Element("subfield", attrib={"code": "a"})
    _indicator.text = signature
    _signature_value = etree.Element("subfield", attrib={"code": "d"})
    _signature_value.text = indicator

    for _subfield in [
        _signature_category,
        _department,
        _indicator,
        _signature_value,
    ]:
        _datafield_signature.append(_subfield)
    return _datafield_signature


EXAMPLE_XML = (
    pathlib.Path(__file__)
    .parent.resolve()
    .joinpath("../../hebis/testexamples/iln204.xml")
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
    _record = initial_record

    if hrid:
        _record.find("hrid").text = f"{hrid}"
        _record.find(
            "metadata/datafield[@tag='003@']/subfield[@code='0']"
        ).text = f"{hrid}"

    _record.find("metadata/item[@epn='184727820']").attrib.update(
        {"epn": f"{epn}"}
    )
    _record.find(
        "metadata/item/datafield[@tag='203@']/subfield[@code='0']"
    ).text = f"{epn}"

    _datafield = _record.find("metadata/item/datafield[@tag='209A']")
    _datafield.find("subfield[@code='a']").text = signature
    _datafield.find("subfield[@code='d']").text = indicator
    _datafield.find("subfield[@code='f']").text = department_code

    return _record


# TODO check and finish
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
    _record = etree.Element("record")
    _record.append(
        ElementTree.fromstring(
            """
        <processing>
            <item>
                <status>
                <policy>overwrite</policy>
                <ifStatusWas>
                    <arr>
                    <i>
                        <name>On order</name>
                    </i>
                    </arr>
                </ifStatusWas>
                </status>
            </item>
        </processing>
        """
        )
    )
    _item = etree.SubElement(
        etree.SubElement(_record, "original"),
        "item",
        attrib={"epn": "184727820"},
    )

    _item.append(
        create_signature(
            department_code=department_code,
            signature=signature,
            indicator=indicator,
        )
    )

    _holdings_record = etree.SubElement(_record, "holdingsRecord")

    _i = etree.SubElement(etree.SubElement(_holdings_record, "arr"), "i")
    etree.SubElement(_i, "permanentLocationId").text = "LOCATION"

    etree.SubElement(
        etree.SubElement(etree.SubElement(_i, "items"), "arr"), "i"
    )

    print(_record)
    return _record


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


def apply_xslt(
    data: TreeOrElement, filename: str | PathLike | pathlib.Path
) -> TreeOrElement:
    """Apply an XSL-transformation from a file.

    Args:
        data (TreeOrElement): Data to apply the transformation to
        filename (str | PathLike | pathlib.Path):
            Path of the file containing the transformation

    Returns:
        TreeOrElement: Transformed data
    """
    with open(filename) as f:
        # TOOD: Check why the defusedxml parser is not working here
        transform: etree.XSLT = etree.XSLT(etree.parse(f))  # nosec blacklist
    return transform(data)


def _apply_step1(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/pica2instance-new.xsl"),
    )
    return transformed


def _apply_step2(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/relationships.xsl"),
    )
    return transformed


def _apply_step3(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(
            "../../hebis/holdings-items-hebis.xsl"
        ),  # TODO Check "hebis/holdings-items-hebis-hrid-test.xsl"
    )
    return transformed


def _apply_step4(collection: TreeOrElement, iln: int) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/holding-items-hebis-iln{iln}.xsl"),
    )
    return transformed


def _apply_step5(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/codes2uuid-hebis.xsl"),
    )
    return transformed


def _apply_step6(collection: TreeOrElement, iln: int) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/codes2uuid-hebis-iln{iln}.xsl"),
    )
    return transformed


def logstring_for_xsl(
    xslt: etree._XSLTProcessingInstruction, result: etree.Element
) -> str:
    """Create logging information for transformation and data.

    Args:
        xslt (etree._XSLTProcessingInstruction): Transformation
        result (etree.Element): Element of transformed data

    Returns:
        str: logging information
    """
    return f"""
    XSLT:
    {xslt.error_log}

    XML RESULT:
    {
        etree
        .tostring(result, encoding="utf-8", pretty_print=True)
        .decode("utf-8")
        if False
        else "XML SUPPRESSED"
    }"""


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
def create_example_and_apply(
    xslt: etree._XSLTProcessingInstruction,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    expected_location: str,
    record_from_example: etree._Element,
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
        hrid (Optional[int]): HEBIS wide identifier. Defaults to None.

    Raises:
        etree.XSLTApplyError: Error applying the transformation

    Returns:
        etree.Element: transformed entry
    """
    # makes debugging easier
    intermediate = {}
    _input = create_collection([record_from_example])

    i: int = 0
    intermediate[i] = deepcopy(_input)

    for f in [_apply_step1, _apply_step2, _apply_step3]:
        _input = f(_input)
        i += 1
        intermediate[i] = deepcopy(_input)

    try:
        return xslt(_input)
    except etree.XSLTApplyError as e:
        reraise(e=e, info=xslt.error_log)
