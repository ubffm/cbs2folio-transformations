#!/usr/bin/env python3

import logging
import random
from typing import Any
from typing import Optional

from lxml import etree
import pytest
from xmldiff import main as xmldiffmain

logger = logging.getLogger()


# TODO add stricter typing
Collection = object
Record = Any

XMLInitial = etree._ElementTree
XMLStep1 = etree._ElementTree
XMLStep2 = etree._ElementTree
XMLStep3 = etree._ElementTree
XMLStep4 = etree._ElementTree
XMLStep5 = etree._ElementTree
XMLStep6 = etree._ElementTree


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


EXAMPLE_XML = "hebis/testexamples/iln204.xml"


def _get_initial_record():
    parser = etree.XMLParser(remove_blank_text=True)

    with open(EXAMPLE_XML) as f:
        _tree = etree.parse(f, parser=parser)

    _record = _tree.find("//record")
    return _record


def create_record_from_example(
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    hrid: Optional[int] = None,
) -> etree._Element:

    _record = _get_initial_record()

    if hrid:
        _record.find("hrid").text = f"{hrid}"
        _record.find(
            "metadata/datafield[@tag='003@']/subfield[@code='0']"
        ).text = f"{hrid}"

    _record.find("metadata/item[@epn='184727820']").attrib.update({"epn": f"{epn}"})
    _record.find(
        "metadata/item/datafield[@tag='203@']/subfield[@code='0']"
    ).text = f"{epn}"

    _record.find(
        "metadata/item/datafield[@tag='209A']/subfield[@code='a']"
    ).text = signature
    _record.find(
        "metadata/item/datafield[@tag='209A']/subfield[@code='d']"
    ).text = indicator
    _record.find(
        "metadata/item/datafield[@tag='209A']/subfield[@code='f']"
    ).text = department_code

    return _record


def tmp(
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    hrid: Optional[int] = None,
) -> etree._Element:
    _record = etree.Element("record")

    _status = etree.Element("status")
    _status.text = "upsert"
    _record.append(_status)

    _hrid_value = (
        "".join(random.choices([f"{i}" for i in range(10)], k=5))
        if hrid is None
        else str(hrid)
    )
    _hrid = etree.Element("hrid")
    _hrid.text = _hrid_value
    _record.append(_hrid)

    _metadata = etree.Element("metadata")
    _record.append(_metadata)

    _hrid_datafield = etree.Element("datafield", tag="003@")
    _metadata.append(_hrid_datafield)

    _hrid_subdatafield = etree.Element("subfield", attrib={"code": "0"})
    _hrid_subdatafield.text = f"{hrid}"
    _hrid_datafield.append(_hrid_subdatafield)

    _item = etree.Element("item", attrib={"epn": f"{epn}"})
    _metadata.append(_item)

    _datafield = etree.Element(
        "datafield", attrib={"tag": "203@", "occurrence": "01", "fulltag": "203@/01"}
    )  # TODO use verbose name
    _record.append(_datafield)

    _subfield = etree.Element("subfield", attrib={"code": "0"})  # TODO use verbose name
    _subfield.text = f"{epn}"
    _datafield.append(_subfield)

    _item.append(
        create_signature(
            department_code=department_code, signature=signature, indicator=indicator
        )
    )

    return _record


def create_test_xml_initial() -> XMLInitial:
    ...


def create_record(department_code: str, signature: str, indicator: str):
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

    return _record


def apply_xslt(data, filename):
    with open(filename) as f:
        transform = etree.XSLT(etree.parse(f))
    return transform(data)


def apply_step1(collection):
    transformed = apply_xslt(collection, "hebis/pica2instance-new.xsl")
    return transformed


def apply_step2(collection):
    transformed = apply_xslt(collection, "hebis/relationships.xsl")
    return transformed


def apply_step3(collection):
    transformed = apply_xslt(
        collection,
        "hebis/holdings-items-hebis.xsl",  # TODO Check "hebis/holdings-items-hebis-hrid-test.xsl"
    )
    return transformed


def apply_step4(collection, iln):
    transformed = apply_xslt(collection, f"hebis/holding-items-hebis-iln{iln}.xsl")
    return transformed


def apply_step5(collection):
    transformed = apply_xslt(collection, "hebis/codes2uuid-hebis.xsl")
    return transformed


def apply_step6(collection, iln):
    transformed = apply_xslt(collection, f"hebis/codes2uuid-hebis-iln{iln}.xsl")
    return transformed


def check_permanentLocationId(
    xslt: etree._XSLTProcessingInstruction,
    department_code: str,
    signature: str,
    indicator: str,
    epn: int | str,
    expected_location: str,
    hrid: Optional[int] = None,
):

    from copy import deepcopy

    intermediate = {}
    _input = create_collection(
        [create_record_from_example(department_code, signature, indicator, epn, hrid)]
    )

    i: int = 0
    intermediate[i] = deepcopy(_input)

    for f in [apply_step1, apply_step2, apply_step3]:
        _input = f(_input)
        i += 1
        intermediate[i] = deepcopy(_input)
    # _input = apply_step3(apply_step2(apply_step1(_collection)))

    _result = xslt(_input)

    _location_node = _result.find("//record/holdingsRecords/arr/i/permanentLocationId")

    if not _location_node is None:
        assert _location_node.text == expected_location, f"{signature} was expected to be mapped to {expected_location} but was mapped to {_location_node.text}"
    else:
        logger.error(f"No location set for signature '{signature}'")


@pytest.mark.parametrize(
    "department_code, signature, indicator",
    [
        ("111", "pap 21321", "u"),
        ("000", "2o zz 1", "u"),
        ("000", "BAp 27,Kopernicus-3", "u"),
        ("000", "BAp 27,Jünger 2003", "u"),
        ("000", "BAp 27,Calderon de la Barca-2,2", "u"),
    ],
)
def test_create_record(department_code, signature, indicator):
    create_record(department_code, signature, indicator)


@pytest.mark.parametrize(
    "department_code, signature, indicator, epn, hrid",
    [
        ("000", "BAp 27,Jünger 2003", "u", 184727820, 109962869),
        ("000", "BAp 27,Calderon de la Barca-2,2", "u", "21028126X", 116105488),
        ("000", "BAp 27,Kopernicus-3", "u", "34203166X", 122359909),
    ],
)
def test_create_record_initial(department_code, signature, indicator, epn, hrid):
    create_record_from_example(department_code, signature, indicator, epn, hrid)


@pytest.mark.xfail
@pytest.mark.parametrize(
    "department_code, signature, indicator, epn, hrid",
    [
        ("000", "BAp 27,Jünger 2003", "u", 184727820, 109962869),
        ("000", "BAp 27,Calderon de la Barca-2,2", "u", "21028126X", 116105488),
        ("000", "BAp 27,Kopernicus-3", "u", "34203166X", 122359909),
    ],
)
def test_equiv(department_code, signature, indicator, epn, hrid):
    # TODO do proper testing
    _record_a = create_record(department_code, signature, indicator)
    _record_b = create_record_from_example(
        department_code, signature, indicator, epn, hrid
    )

    diff_options = {"F": 0.5, "ratio_mode": "accurate"}

    diff_a_b = xmldiffmain.diff_trees(_record_a, _record_b, diff_options=diff_options)
    diff_a_orig = xmldiffmain.diff_trees(
        _record_a, _get_initial_record(), diff_options=diff_options
    )
    diff_b_orig = xmldiffmain.diff_trees(
        _record_b, _get_initial_record(), diff_options=diff_options
    )

    assert diff_a_b
    assert diff_a_orig
    assert diff_b_orig
