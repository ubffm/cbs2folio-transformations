#!/usr/bin/env python3
import csv
import io
import logging

from collections.abc import Generator
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Tuple
from typing import get_args
from typing import Literal
from typing import Optional
from typing import TypeVar,Collection

import pytest
from _pytest.mark import ParameterSet
from cbs2folio_transformations.csv2holdingsxslt import (
    create_holdings_items_xsl_from_csv,
)
from defusedxml import ElementTree
from hypothesis.strategies._internal.strategies import Ex
from lxml import etree
from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger()


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        help="Allow slow tests.",
    )


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line("markers", "slow: mark test as slow.")


def pytest_runtest_setup(item):
    if "slow" in [mark.name for mark in item.iter_markers()]:
        if not item.config.getoption("--runslow", default=False):
            pytest.skip(f"Skipping slow tests unless explicitly forced to.")


# https://www.testcult.com/handle-test-data-the-right-way-in-pytest/
TEST_FIELD_NAME = Literal[
    "department_code",
    "epn",
    "signature",
    "indicator",
    "expected_location",
]


class SignatureExample(BaseModel):
    department_code: str
    epn: str
    signature: str = Field(...)
    indicator: str
    expected_location: str
    example_id: str = Field(..., alias="id")
    marks: Collection[pytest.MarkDecorator]

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True


from typing import Union, Collection


def yield_signature_example_from_data_iterable(
    data: Iterable,
    marks: Union[
        pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]]
    ] = (),
) -> Generator[SignatureExample, None, None]:
    """Create parameters for testcases.

    This handles creating an id, and marking cases that won't work.

    Args:
        data (Iterable): _description_
        marks (Union[ pytest.MarkDecorator, Collection[Union[pytest.MarkDecorator, pytest.Mark]] ], optional): _description_. Defaults to ().

    Yields:
        Generator[ParameterSet, None, None]: _description_
    """
    for d in data:
        _marks = (
            [marks] if isinstance(marks, pytest.MarkDecorator) else [m for m in marks]
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
                _marks.append(pytest.mark.xfail(reason=f"'{_sig}' is Ausgesondert"))

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


def inject_test_data(file):  # Iterable[dict[Literal[TEST_FIELD_NAME],str]]:
    with open(file) as csvfile:
        reader: csv.DictReader[TEST_FIELD_NAME] = csv.DictReader(
            csvfile,
            fieldnames=get_args(TEST_FIELD_NAME),
            delimiter=";",
            restkey="additional_values",
        )

        yield from yield_signature_example_from_data_iterable(reader)


# Source https://docs.pytest.org/en/6.2.x/example/parametrize.html#paramexamples
def pytest_generate_tests(metafunc: pytest.Metafunc):
    idlist = []
    argvalues = []

    argnames = ["d", "xsl"]

    if metafunc.cls is None:
        return

    if hasattr(metafunc.cls, "xsl") and metafunc.cls.xsl is not None:
        _xsl = metafunc.cls.xsl
    elif hasattr(metafunc.cls, "koko_string") and metafunc.cls.koko_string is not None:
        _xsl = create_holdings_items_xsl_from_csv(
            io.StringIO(metafunc.cls.koko_string),
            use_numerical=metafunc.cls.use_numerical,
            delimiter=metafunc.cls.delimiter,
        )

    elif hasattr(metafunc.cls, "koko_path") and metafunc.cls.koko_path is not None:
        try:
            with open(metafunc.cls.koko_path, encoding="utf-8") as f:
                _xsl = create_holdings_items_xsl_from_csv(
                    f,
                    use_numerical=metafunc.cls.use_numerical,
                    delimiter=metafunc.cls.delimiter,
                )
        except UnicodeDecodeError as e:
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
        _data: Iterable[SignatureExample] = inject_test_data(metafunc.cls.data_csv_path)
    elif hasattr(metafunc.cls, "data") and metafunc.cls.data is not None:
        _data: Iterable[SignatureExample] = yield_signature_example_from_data_iterable(
            metafunc.cls.data
        )
    else:
        raise ValueError("No data specified.")

    for d in _data:
        _dict = { k:v for k,v in d.dict(by_alias=True).items() if k not in ["id","marks"]}
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
#Collection = object
Record = Any


def create_collection(elements: list[Record]):
    collection = etree.Element("collection")

    for r in elements:
        if r is not None:
            collection.append(r)

    return etree.ElementTree(collection)


def create_signature(
    department_code: str, signature: str, indicator: str
) -> etree._Element:
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

    for _subfield in [_signature_category, _department, _indicator, _signature_value]:
        _datafield_signature.append(_subfield)
    return _datafield_signature


import pathlib

EXAMPLE_XML = (
    pathlib.Path(__file__)
    .parent.resolve()
    .joinpath("../../hebis/testexamples/iln204.xml")
)


@pytest.fixture()
def initial_record() -> etree.Element:
    parser = etree.XMLParser(remove_blank_text=True)

    with open(EXAMPLE_XML) as f:
        _tree: ElementTree = etree.parse(f, parser=parser)

    _record = _tree.find("//record")
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
    _record = initial_record

    if hrid:
        _record.find("hrid").text = f"{hrid}"
        _record.find(
            "metadata/datafield[@tag='003@']/subfield[@code='0']"
        ).text = f"{hrid}"

    _record.find("metadata/item[@epn='184727820']").attrib.update({"epn": f"{epn}"})
    _record.find(
        "metadata/item/datafield[@tag='203@']/subfield[@code='0']"
    ).text = f"{epn}"

    _datafield = _record.find("metadata/item/datafield[@tag='209A']")
    _datafield.find("subfield[@code='a']").text = signature
    _datafield.find("subfield[@code='d']").text = indicator
    _datafield.find("subfield[@code='f']").text = department_code

    return _record


@pytest.fixture()
def record(
    department_code: str,
    signature: str,
    indicator: str,
    location: Optional[str] = "LOCATION",
):
    _record = etree.Element("record")
    _record.append(
        etree.fromstring(
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
        etree.SubElement(_record, "original"), "item", attrib={"epn": "184727820"}
    )

    _item.append(
        create_signature(
            department_code=department_code, signature=signature, indicator=indicator
        )
    )

    _holdings_record = etree.SubElement(_record, "holdingsRecord")

    _i = etree.SubElement(etree.SubElement(_holdings_record, "arr"), "i")
    etree.SubElement(_i, "permanentLocationId").text = "LOCATION"

    etree.SubElement(etree.SubElement(etree.SubElement(_i, "items"), "arr"), "i")

    print(_record)
    return _record


TreeOrElement = TypeVar("TreeOrElement", etree.Element, etree.ElementTree)


def apply_xslt(data: TreeOrElement, filename) -> TreeOrElement:
    with open(filename) as f:
        transform: etree.XSLT = etree.XSLT(etree.parse(f))
    return transform(data)


def apply_step1(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/pica2instance-new.xsl"),
    )
    return transformed


def apply_step2(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/relationships.xsl"),
    )
    return transformed


def apply_step3(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(
            "../../hebis/holdings-items-hebis.xsl"
        ),  # TODO Check "hebis/holdings-items-hebis-hrid-test.xsl"
    )
    return transformed


def apply_step4(collection: TreeOrElement, iln: int) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath(f"../../hebis/holding-items-hebis-iln{iln}.xsl"),
    )
    return transformed


def apply_step5(collection: TreeOrElement) -> TreeOrElement:
    transformed = apply_xslt(
        collection,
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("../../hebis/codes2uuid-hebis.xsl"),
    )
    return transformed


def apply_step6(collection: TreeOrElement, iln: int) -> TreeOrElement:
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
    return f"""
    XSLT: {xslt.error_log}

    XML RESULT:
    { etree.tostring(result, encoding="utf-8", pretty_print=True).decode("utf-8") if False else "XML SUPPRESSED"}
    """


@pytest.fixture()
def xslt(xsl: etree.Element):
    return etree.XSLT(xsl)


@pytest.fixture()
def hrid():
    return None


@pytest.fixture()
def create_example_and_apply(
    xslt: etree._XSLTProcessingInstruction,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    expected_location: str,
    record_from_example,
    hrid: Optional[int] = None,
):
    # makes debugging easier
    intermediate = {}
    _input = create_collection([record_from_example])

    i: int = 0
    intermediate[i] = deepcopy(_input)

    for f in [apply_step1, apply_step2, apply_step3]:
        _input = f(_input)
        i += 1
        intermediate[i] = deepcopy(_input)

    try:
        return xslt(_input)
    except etree.XSLTApplyError as e:
        raise Exception(xslt.error_log) from e
