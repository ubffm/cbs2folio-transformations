"""Module for reusable codesnippets for tests."""
import csv
import logging
import pathlib
from collections.abc import Generator
from collections.abc import Iterable
from copy import deepcopy
from os import PathLike
from typing import Any
from typing import Collection
from typing import Dict
from typing import get_args
from typing import List
from typing import Literal
from typing import Optional
from typing import Set
from typing import TypeVar
from typing import Union

import pytest
from cbs2folio_transformations._helpers import reraise
from defusedxml import ElementTree  # type: ignore[import]
from lxml import etree  # nosec: ignore[blacklist]
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import ValidationError
from pytest import Mark
from pytest import MarkDecorator

logger = logging.getLogger()

_TreeOrElement = TypeVar("_TreeOrElement", etree._Element, etree._ElementTree)

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

    @field_validator("epn", mode="before")
    def _to_str(cls, v: int | str) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, int):
            return str(v)
        raise TypeError(f"Unsupported type {type(v)}")

    model_config = ConfigDict(
        arbitrary_types_allowed=True, populate_by_name=True
    )


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
        _marks: "List[MarkDecorator|Mark]" = (
            [marks] if isinstance(marks, MarkDecorator) else [m for m in marks]
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

            try:
                yield SignatureExample.model_validate(
                    {
                        **d,
                        "id": f"{_sig}@{_dep}->{_loc}",
                        "marks": _marks,
                    }
                )
            except ValidationError as e:
                logger.error(f"Error Validating {d}: {e}")


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


# TODO add stricter typing
# Collection = object
Record = Any


def create_collection(elements: list[Record]) -> etree._ElementTree:
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
    .joinpath("../../../hebis/testexamples/iln204.xml")
)


def get_initial_record() -> etree._Element:
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
            f"Could not find record in {etree.tostring(_tree).decode()}"
        )
    return _record


def create_record_from_example(
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
    _record = get_initial_record()

    if hrid:
        _hrid_field = _record.find("hrid")
        if _hrid_field is None:
            raise ValueError(
                f"Initial record without hrid: {etree.tostring(_record).decode()}"  # noqa: ignore[E501]
            )
        _hrid_field.text = f"{hrid}"
        _hrid_subfield = _record.find(  # TODO: Find better name
            "metadata/datafield[@tag='003@']/subfield[@code='0']"
        )
        if _hrid_subfield is None:
            raise ValueError(
                f"Initial record without field 003@ 0: {etree.tostring(_record).decode()}"  # noqa: ignore[E501]
            )
        _hrid_subfield.text = f"{hrid}"

    _metadata_item_by_epn = _record.find(
        "metadata/item[@epn='184727820']"
    )  # FIXME: check if hardcoding the EPN is sensible
    if _metadata_item_by_epn is None:
        raise ValueError(
            f"Initial record without EPN: {etree.tostring(_record).decode()}"
        )
    _metadata_item_by_epn.attrib.update({"epn": f"{epn}"})

    _metadata_item_datafield_epn = _record.find(
        "metadata/item/datafield[@tag='203@']/subfield[@code='0']"
    )
    if _metadata_item_datafield_epn is None:
        raise ValueError(
            f"Initial record without field 203@ 0: {etree.tostring(_record).decode()}"  # noqa: ignore[E501]
        )
    _metadata_item_datafield_epn.text = f"{epn}"

    _datafield = _record.find(
        "metadata/item/datafield[@tag='209A']"
    )  # TODO: Find better name
    if _datafield is None:
        raise ValueError(
            f"Initial record without field 209A: {etree.tostring(_record).decode()}"  # noqa: ignore[E501]
        )

    _subfields_dict: Dict[Literal["a", "d", "f"], etree._Element] = {}
    _subfields: Set[Literal["a", "d", "f"]] = {"a", "d", "f"}
    for _subfield_key in _subfields:
        _subfield = _datafield.find(f"subfield[@code='{_subfield_key}']")
        if _subfield is not None:
            _subfields_dict[_subfield_key] = _subfield

    if len(_missing_subfields := _subfields - _subfields_dict.keys()) > 0:
        raise ValueError(
            f"Datafield 209A without subfields {_missing_subfields}: {etree.tostring(_datafield).decode()}"  # noqa: ignore[E501]
        )
    _subfields_dict["a"].text = signature
    _subfields_dict["d"].text = indicator
    _subfields_dict["f"].text = department_code

    return _record


# TODO check and finish
@pytest.fixture()
def create_record(
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


TreeOrElement = TypeVar("TreeOrElement", etree._Element, etree._ElementTree)


def apply_xslt(
    data: TreeOrElement, filename: str | PathLike | pathlib.Path
) -> etree._XSLTResultTree:
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


def logstring_for_xsl(xslt: etree.XSLT, result: etree._Element) -> str:
    """Create logging information for transformation and data.

    Args:
        xslt (etree._XSLTProcessingInstruction): Transformation
        result (etree.Element): Element of transformed data

    Returns:
        str: logging information
    """
    # FIXME: Fix typing to show error_log is defined
    _error_log = xslt.error_log  # type: ignore[attr-defined] # pyright: ignore[reportGeneralTypeIssues]# noqa: ignore[E501]
    _xml_result = (
        etree.tostring(result, encoding="utf-8", pretty_print=True).decode(
            "utf-8"
        )
        if False
        else "XML SUPPRESSED"
    )
    return f"""
    XSLT:
    {_error_log}

    XML RESULT:
    {_xml_result}"""


def _apply_step1(collection: TreeOrElement) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/pica2instance-new.xsl"),
    )
    return transformed


def _apply_step2(collection: TreeOrElement) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/relationships.xsl"),
    )
    return transformed


def _apply_step3(collection: TreeOrElement) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(
            "../../hebis/holdings-items-hebis.xsl"
        ),  # TODO Check "hebis/holdings-items-hebis-hrid-test.xsl"
    )
    return transformed


def _apply_step4(
    collection: _TreeOrElement, iln: int
) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/holding-items-hebis-iln{iln}.xsl"),
    )
    return transformed


def _apply_step5(collection: TreeOrElement) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/codes2uuid-hebis.xsl"),
    )
    return transformed


def _apply_step6(collection: TreeOrElement, iln: int) -> etree._XSLTResultTree:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/codes2uuid-hebis-iln{iln}.xsl"),
    )
    return transformed


def create_example_and_apply(
    xslt: etree._XSLTProcessingInstruction,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    expected_location: str,
    record_from_example: etree._Element,
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


def apply_transformations(
    _input: etree._ElementTree | etree._Element,
    transformations: list[etree.XSLT],
) -> etree._ElementTree | etree._Element:
    """Apply a list of transformations to the input.

    Args:
        _input (etree._ElementTree | etree._Element):
            Data to transform

        transformations (list[etree.XSLT]):
            List of transformations

    Returns:
        etree._ElementTree: Transformed data
    """
    # makes debugging easier
    intermediate: dict[
        int, etree._ElementTree | etree._Element | etree._XSLTResultTree
    ] = {}

    for i, _xslt in enumerate(transformations):
        intermediate[i] = deepcopy(_input)
        try:
            _input = _xslt(_input)
        except etree.XSLTApplyError as e:
            # FIXME: Fix typing to show error_log is defined
            reraise(
                e=e,
                info=_xslt.error_log,  # type: ignore[attr-defined]  # pyright: ignore[reportGeneralTypeIssues]# noqa: ignore[E501]
            )

    return _input
