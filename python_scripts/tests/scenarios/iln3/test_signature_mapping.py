#!/usr/bin/env python3
import pathlib

from lxml import etree  # nosec blacklist

from .. import Scenario


class TestSimpleILN3(Scenario):
    """Small set of general testcases."""

    data_csv_path = (
        pathlib.Path(__file__)
        .parent.resolve()
        .joinpath("cbs2folio_holding-items_Testsignaturen_ILN3.txt")
    )
    use_numerical = True

    koko_path, delimiter = (
        pathlib.Path(__file__).parent.resolve().joinpath("koko174.csv"),
        ";",
    )
    # koko_path, delimiter = (
    #     pathlib.Path(__file__).parent.resolve().joinpath("koko173.csv"),
    #     ";",
    # )
    # koko_path, delimiter = (
    #     pathlib.Path(__file__).parent.resolve().joinpath("koko170.csv"),
    #     ",",
    # )


# @pytest.mark.slow
# class TestAll:

#     use_numerical = True
#     data_csv_path = "cbs2folio_holding-items_Testsignaturen_ILN3_alle.txt"

#     koko_path = DEFAULT_KOKO_PATH


def department2ranges(department: etree._Element):
    _ranges = etree.Element("ranges")
    _ranges.append(department)

    return _ranges
