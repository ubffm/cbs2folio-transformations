#!/usr/bin/env python3
"""Module for creating a 'holdings.xslt' from a csv of ranges."""
import io
import logging
import pathlib
from argparse import ArgumentParser
from argparse import FileType
from collections.abc import Iterable
from csv import DictReader
from sys import stdin
from sys import stdout
from typing import TypedDict

from defusedxml import ElementTree
from lxml import etree  # nosec blacklist

from ._helpers import reraise

logger = logging.getLogger()


EXAMPLE_XSL = (
    pathlib.Path(__file__)
    .parent.resolve()
    .joinpath("../../../hebis/holding-items-hebis-iln204.xsl")
)


class LimitDict(TypedDict):
    """Dictionary to describe either a prefix or a range of signatures."""

    department_code: str
    sig_start: str
    sig_end: str
    location_numerical: str
    location_code: str


def rangesXML2LimitDictList(ranges: etree.Element) -> Iterable[LimitDict]:
    """Parse the 'ranges' node of a 'holdings.xsl' to a list.

    Args:
        ranges (etree.Element): 'ranges' element of a 'holdings.xml'

    Raises:
        ValueError: unparseable tag

    Returns:
        Iterable[LimitDict]: Limits as list
    """
    _ranges = []
    for _department in ranges.findall("department"):
        department_code = _department.attrib["code"]

        if len(_department) == 0:
            logger.warning(
                f"""Default only locations are not yet fully implemented.
                    {department_code} might not be mapped"""
            )
            continue
        else:
            for limit in _department:
                location = limit.attrib["location"]

                if limit.tag == "prefix":
                    _prefix: str = limit.text + "@@@"
                    sig_start = _prefix
                    sig_end = _prefix

                elif limit.tag == "range":
                    sig_start = limit.attrib["from"]
                    sig_end = limit.attrib["to"]

                else:
                    raise ValueError(
                        f"""Unsupported tag {
                            limit.tag
                        } in {
                            etree.tostring(limit)
                        }"""
                    )

                _ranges.append(
                    LimitDict(
                        **{
                            "department_code": department_code,
                            "sig_start": sig_start,
                            "sig_end": sig_end,
                            "location_numerical": None,
                            "location_code": location,
                        }
                    )
                )

            if "default-location" in _department.attrib:
                _ranges.append(
                    LimitDict(
                        **{
                            "department_code": department_code,
                            "sig_start": "",
                            "sig_end": "",
                            "location_numerical": None,
                            "location_code": _department.attrib[
                                "default-location"
                            ],
                        }
                    )
                )

    return _ranges


def limitDictList2rangesXML(
    reader: DictReader | Iterable[LimitDict], use_numerical: bool = False
) -> etree._Element:
    """Create the 'ranges' node of a 'holdings.xsl' file.

    Args:
        reader (DictReader | Iterable[LimitDict]): Signature limits
        use_numerical (bool, optional):
            Use the numerical code instead of the text location.
            Defaults to False.

    Raises:
        ValueError: department_code unsupported

    Returns:
        etree._Element: Ranges element for use in the template
    """
    _ranges = etree.Element("ranges")
    for r in reader:
        # TODO ensure type
        _department_code: str = r["department_code"]

        if _department_code.upper() in [
            "INF",  # Information
            "",  # Malformed Entry
            "BIK",  # Header
        ]:
            logger.warning(r)
        else:
            _department_code = f"{int(_department_code):03d}"

        if _department_code and len(_department_code) != 3:
            raise ValueError(f"Invalid data: {_department_code}")

        _department: etree.Element = (
            _d
            if (_d := _ranges.find(f"department[@code='{_department_code}']"))
            is not None
            else etree.SubElement(
                _ranges, "department", attrib={"code": f"{_department_code}"}
            )
        )
        _location: str = r[
            "location_numerical" if use_numerical else "location_code"
        ]

        if r["sig_start"] == r["sig_end"] == "":
            logger.warning(
                f"""Setting default-location for {
                    _department_code
                } to {
                    _location
                }"""
            )
            _department.attrib.update({"default-location": _location})

        elif r["sig_start"].endswith("@@@") or r["sig_end"].endswith("@@@"):
            if not (
                r["sig_start"].removesuffix("@@@")
                == r["sig_end"].removesuffix("@@@")
            ):
                logger.warning(
                    f"""Mixed prefixes are not fully supported: {
                        r['sig_start']
                    } to {
                        r['sig_end']
                        }"""
                )
                _range = etree.Element("range")
                _range.set("from", r["sig_start"].lower().removesuffix("@@@"))
                _range.set("to", r["sig_end"].lower().removesuffix("@@@"))
                _range.set("location", _location)
                _department.append(_range)

            elif r["sig_start"] == r["sig_end"]:
                # Both have the "@@@" suffix

                _prefix = etree.Element("prefix", location=_location)

                _prefix.text = r["sig_start"].removesuffix("@@@").lower()
                _department.append(_prefix)

            else:
                # TODO define default behaviour; prefixes are checked first!
                logger.warning(
                    f"""Unclear definition: {
                        r['sig_start']
                    } to {
                        r['sig_end']
                    }; will handle as prefix for now"""
                )
                _prefix = etree.Element("prefix", location=_location)

                _prefix.text = r["sig_start"].removesuffix("@@@").lower()
                _department.append(_prefix)

        else:
            _range = etree.Element("range")
            _range.set("from", r["sig_start"].lower())
            _range.set("to", r["sig_end"].lower())
            _range.set("location", _location)
            _department.append(_range)

    if len(_ranges) == 0:
        logger.warning(
            "No valid ranges or prefixes have been defined in\n"
            + etree.tostring(
                _ranges, encoding="utf-8", pretty_print=True
            ).decode("utf-8")
        )
    return _ranges


def create_holdings_items_xsl_from_csv(
    koko: io.TextIOWrapper, use_numerical: bool = False, delimiter: str = ","
) -> ElementTree:
    """Create a 'holdings.xsl' from csv of limits.

    Args:
        koko (io.TextIOWrapper): File containing the limits
        use_numerical (bool, optional):
            Use the numerical code instead of the text location.
            Defaults to False.
        delimiter (str, optional):
            Delimiter to expect between the csv fields. Defaults to ",".

    Raises:
        Exceptiom: Caught exception enhanced with `koko.name'

    Returns:
        ElementTree: 'holdings.xsl' as XML
    """
    import csv

    # TODO Fix handling of files if provided via args
    reader = csv.DictReader(
        koko,
        delimiter=delimiter,
        fieldnames=[
            "department_code",
            "sig_start",
            "sig_end",
            "location_numerical",
            "location_code",
        ],
    )

    try:
        _ranges = limitDictList2rangesXML(reader, use_numerical=use_numerical)
    except Exception as e:
        reraise(
            e=e,
            info=f"""Error handling the provided koko{
                (' (' + koko.name + ')' ) if koko.name else ''
            }""",
        )
    # TODO remove entries
    with open(EXAMPLE_XSL) as f:
        # TODO: Check why defusedxml has no getparent
        _tree: ElementTree = etree.parse(f)  # nosec blacklist
        _r = _tree.find(".//ranges")
        _r.getparent().replace(_r, _ranges)

    return _tree


def main():
    """Run the module as script."""
    parser = ArgumentParser(
        description="Create an XSL Transformation file from a koko csv"
    )
    parser.add_argument(
        "--in-file",
        help="Input CSV file",
        type=FileType("r"),
        default=stdin,
    )
    parser.add_argument(
        "--out-file",
        help="Output XSLT file",
        type=FileType("w"),
        default=stdout,
    )

    args = parser.parse_args()

    create_holdings_items_xsl_from_csv(koko=args.in_file)


if __name__ == "__main__":
    main()
