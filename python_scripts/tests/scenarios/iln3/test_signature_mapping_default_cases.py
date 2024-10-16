#!/usr/bin/env python3
import pytest

from .. import Scenario


class TestOverlappingJuBuFo(Scenario):
    koko_string = """
152;B 2;B 4;470;KJBMAG
152;JBd 2021;JBq 2021;470;KJBMAG
152;JBd 2022;JBq 2022;470;KJBMAG
152;JBd;JBq;471;KJBZB
152;JB 2018 1;JB 2018 3157;471;KJBZB
152;JB 2019 1;JB 2019 2826;471;KJBZB
152;JB 2020 4;JB 2020 2962;471;KJBZB
152;JB 2021 1;JB 2021 3227;471;KJBZB
152;JB;JB;470;KJBMAG
152;K 1;K 5;470;KJBMAG
152;K JB@@@;K JB@@@;470;KJBMAG
"""
    use_numerical = True
    data = [
        {
            "department_code": "152",
            "epn": 919167942,
            "signature": "JBq 2019/3322",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "471",
        },
        {
            "department_code": "152",
            "epn": 919167934,
            "signature": "JBq 2019/3322",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "471",
        },
        {
            "department_code": "152",
            "epn": 919167926,
            "signature": "JBq 2019/3324",
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "471",
        },
        {
            "department_code": "152",
            "epn": 919140653,
            "signature": "JB /JB",
            "indicator": "g",
            "hrid": 109962869,
            "expected_location": "470",
        },
    ]


class TestDoubleLetter(Scenario):
    """Test for signatures with duplicate letters"""

    koko_string = """
330;14 AA;14 ZZ;414;BZG414
330;14 TFM;14 TFM;414;BZG414
330;14 A;14 D;414;BZG414
330;14 E;14 Z;423;BZG423
"""
    use_numerical = True
    data = [
        {
            "department_code": "330",
            "epn": 184727820,
            "signature": sig,
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "423",
        }
        for sig in [
            "14/E.o. BER. 20",
            "14/F. b. 83 ",
            "14/F. f. 23 ",
            "14/K.a. 26. 7",
            "14/K.a. 88. 5",
            "14/K.c. 12. 24",
            "14/K.c. 12. 40",
            "14/K.c. 12. 41",
            "14/L. c. 227 ",
            "14/L. e. 6",
            "14/L.e. 11. 7",
            "14/L.e. 6. 14",
            "14/L.e. 6.12",
            "14/L.e. 9. 13",
            "14/M.a. GAS. 2",
            "14/M.a. Grae. 1",
            "14/M.a. Gro. 1",
            "14/M.a. OLI. 2",
            "14/M.c. Boo. 1",
            "14/M.c. Kae. 1",
            "14/M.c. Ron. 1",
            "14/S. d. 14",
            "14/S.g. 3. 18",
        ]
    ]


class TestDirtyNamingValid(Scenario):
    koko_string = """
330;01 GL;01 GL;439;BZG439
"""

    use_numerical = True
    data = [
        {
            "department_code": "330",
            "epn": 184727820,
            "signature": sig,
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "439",
        }
        for sig in [
            "01 GL 9381 V489",
            "01 GL 1911 H551",
        ]
    ]


class TestDirtyRanges(Scenario):
    koko_string = """
000 ;Jud;Jud@@@;107;OG3LS
000;W;W@@@;107;OG3LS
"""

    use_numerical = True
    data = [
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": sig,
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "107",
        }
        for sig in ["Wm 1590", "Jud. 7953"]
    ]


@pytest.mark.xfail(reason="Departmentcode with trailing space")
class TestDirtyDepartmentCode(Scenario):
    koko_string = """
000 ;Jud@@@;Jud@@@;107;OG3LS
"""
    use_numerical = True
    data = [
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": sig,
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "107",
        }
        for sig in ["Jud. 7953"]
    ]


class TestNumbers(Scenario):
    """Test for numeric comparison"""

    koko_string = """
000;S 14;S 16;888;ZEPC30
000;S 150;S 150;108;ZC30LS
000;;;090;RESTE
"""
    use_numerical = True
    data = [
        {
            "department_code": "000",
            "epn": 184727820,
            "signature": sig,
            "indicator": "u",
            "hrid": 109962869,
            "expected_location": "108",
        }
        for sig in ["S 150/1864"]
    ]
