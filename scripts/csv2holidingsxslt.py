#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
import logging
from sys import stdin, stdout

from lxml import etree

logger = logging.getLogger()

EXAMPLE_XSL = "hebis/holding-items-hebis-iln204.xsl"


def create_holdings_items_xsl_from_csv(koko="koko170.csv"):
    import csv

    # TODO Fix handling of files if provided via args
    with open(koko) as csvfile:
        reader = csv.DictReader(
            csvfile,
            fieldnames=["department_code", "sig_start", "sig_end", "num", "location"],
        )

        _ranges = etree.Element("ranges")
        for r in reader:
            try:
                _r = int(r["department_code"])
            except ValueError as e:
                continue

            _department = (
                _d
                if (_d := _ranges.find(f"department[@code='{_r}']")) is not None
                else etree.SubElement(_ranges, "department", attrib={"code": f"{_r}"})
            )

            if r["sig_start"].endswith("@@@") and r["sig_end"].endswith("@@@"):
                if not (
                    r["sig_start"].removesuffix("@@@")
                    == r["sig_end"].removesuffix("@@@")
                ):
                    logger.warning(
                        f"Mixed prefixes are not fully supported: {r['sig_start']} to {r['sig_end']}"
                    )
                    _range = etree.Element("range")
                    _range.set("from", r["sig_start"])
                    _range.set("to", r["sig_end"])
                    _range.set("location", r["location"])
                    _department.append(_range)

                    continue

                _prefix = etree.Element("prefix", location=r["location"])

                _prefix.text = r["sig_start"].removesuffix("@@@")
                _department.append(_prefix)
            else:
                _range = etree.Element("range")
                _range.set("from", r["sig_start"])
                _range.set("to", r["sig_end"])
                _range.set("location", r["location"])
                _department.append(_range)

    # TODO remove entries
    with open(EXAMPLE_XSL) as f:

        _tree = etree.parse(f)
        _r = _tree.find("//ranges")
        _r.getparent().replace(_r, _ranges)

    return _tree


def main():
    parser = ArgumentParser(
        description="Create an XSL Transformation file from a list of concordances"
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
