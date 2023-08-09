#!/usr/bin/env python3
"""Module for creating a 'holdings.xslt' from a csv of ranges."""
from __future__ import annotations

import io
import logging
from argparse import ArgumentParser
from argparse import FileType
from collections.abc import Iterable
from contextlib import suppress
from csv import DictReader
from sys import stdin
from sys import stdout
from typing import Annotated
from typing import Iterator
from typing import List
from typing import Optional
from typing import Text
from typing import Union

from annotated_types import Len
from lxml import etree  # type: ignore [import] # nosec: ignore [blacklist]
from pydantic import BaseModel
from pydantic import field_validator
from pydantic import model_validator
from pydantic import ValidationError
from pydantic_core import PydanticCustomError

from ._helpers import EXAMPLE_XSL
from ._helpers import reraise
from ._helpers import tokenize
from ._helpers import VALIDATION_REGEX

logger = logging.getLogger()


class LimitDict(BaseModel):
    """Dictionary to describe either a prefix or a range of signatures."""

    def __getitem__(self, item):
        """Access the model fields in a dictionary like way."""
        return getattr(self, item)

    # def __iter__(self) -> "TupleGenerator":
    #     return super().__iter__()

    # def copy(
    #     self: Self,
    #     *,
    #     include: Optional[
    #         Union["AbstractSetIntStr", "MappingIntStrAny"]
    #     ] = None,
    #     exclude: Optional[
    #         Union["AbstractSetIntStr", "MappingIntStrAny"]
    #     ] = None,
    #     update: Optional["DictStrAny"] = None,
    #     deep: bool = False,
    # ) -> Self:
    #     return super().copy(
    #         include=include, exclude=exclude, update=update, deep=deep
    #     )

    department_code: str

    @field_validator("department_code")
    def _validate_department_code(cls, v, values) -> str | None:
        _department_code = v
        if _department_code.upper() in [
            "INF",  # Information
            "",  # Malformed Entry
            "BIK",  # Header
        ]:
            logger.warning(values)
        else:
            _department_code = f"{int(_department_code):03d}"

        if _department_code and len(_department_code) != 3:
            raise ValueError(f"Invalid data: {_department_code}")

        return _department_code

    sig_start: str
    sig_end: str

    @field_validator("sig_start", "sig_end")
    def _validate_signature_regexp(cls, v) -> str:
        if not (VALIDATION_REGEX.match(v)):
            raise ValueError(
                f"'{v}' contains invalid characters \
                            (RegEx: {VALIDATION_REGEX.pattern})"
            )
        return v

    @model_validator(mode="after")
    def _validate_range(self: "LimitDict") -> "LimitDict":
        _tokenized_start = tokenize(sig_start := self["sig_start"])
        _tokenized_end = tokenize(sig_end := self["sig_end"])

        if len(_tokenized_start) != len(_tokenized_end):
            raise PydanticCustomError(
                "mismatching_token_lengths",
                "'{sig_start}' has a different length from '{sig_end}'\
                        ({_tokenized_start,_tokenized_end})",
                {
                    "sig_start": sig_start,
                    "sig_end": sig_end,
                    "_tokenized_start": _tokenized_start,
                    "_tokenized_end": _tokenized_end,
                },
            )

        for token_idx in range(len(_tokenized_start)):
            if _tokenized_start[token_idx] == _tokenized_end[token_idx]:
                continue
            else:
                _validate_tokens(
                    _tokenized_start[token_idx],
                    _tokenized_end[token_idx],
                    sig_start=sig_start,
                    sig_end=sig_end,
                )
        return self

    location_numerical: str | None
    location_code: str


def rangesXML2LimitDictList(ranges: etree.Element) -> Iterable[LimitDict]:
    """Parse the 'ranges' node of a 'holdings.xsl' to a list.

    Args:
        ranges (etree.Element): 'ranges' element of a 'holdings.xml'

    Raises:
        ValueError: unparsable tag

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
                        f"Unsupported tag {limit.tag} in {etree.tostring(limit)}"  # noqa: ignore[E501]
                    )

                try:
                    _ranges.append(
                        LimitDict.model_validate(
                            {
                                "department_code": department_code,
                                "sig_start": sig_start,
                                "sig_end": sig_end,
                                "location_numerical": None,
                                "location_code": location,
                            }
                        )
                    )
                except ValidationError as e:
                    _error = e.errors()[0]
                    _error_context = _error["ctx"] if "ctx" in _error else None
                    if _error["type"] == "mixed_tokens":
                        logger.warning(
                            f"Please split the following range into a numeric and an alphabetic range: {_error_context}, {etree.tostring(limit)}"  # noqa: ignore[E501]
                        )
                    elif _error["type"] == "mismatching_token_lengths":
                        logger.warning(
                            f"This range is not a valid one; both limits need to have the same length after tokenization: {_error_context}, {etree.tostring(limit)}"  # noqa: ignore[E501]
                        )
                    else:
                        logger.error(f"Error Validating {limit}: {e}")

            if "default-location" in _department.attrib:
                try:
                    _ranges.append(
                        LimitDict.model_validate(
                            {
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
                except ValidationError as e:
                    logger.error(f"Error Validating {_department}: {e}")

    return _ranges


OneCharacterString = Annotated[str, Len(min_length=1, max_length=1)]


class LimitDictReader:
    """Adapted DictReader returning LimitDict instances."""

    reader: DictReader

    def __init__(self, f: Iterable[Text], delimiter: OneCharacterString):
        """Initialize the LimitDictReader.

        Args:
            f (Iterable[Text]): Iterable text to parse as csv.
            delimiter (OneCharacterString): Delimiter for the fields.
        """
        self.reader = DictReader(
            f,
            delimiter=delimiter,
            fieldnames=[
                "department_code",
                "sig_start",
                "sig_end",
                "location_numerical",
                "location_code",
            ],
        )

    def __iter__(self) -> "Iterator[LimitDict]":
        """Return an Iterator of LimitDicts."""
        return map(LimitDict.model_validate, self.reader)

    # def __next__(self) -> LimitDict:
    #     return
    #     return LimitDict.parse_obj(super().__next__())


def _validate_tokens(
    token_start: str, token_end: str, sig_start: str, sig_end: str
) -> None:
    """Validate wether the tokens are ok for comparison.

    Args:
        token_start (str): Token from start of signature range
        token_end (str): Token from end of signature range
        sig_start (str): Start of the signature range
        sig_end (str): End of the signature range
    """
    _token_start_as_int: Optional[int] = None
    with suppress(ValueError):
        _token_start_as_int = int(sig_start)

    _token_end_as_int: Optional[int] = None
    with suppress(ValueError):
        _token_end_as_int = int(sig_end)

    if _token_start_as_int is None and _token_end_as_int is None:
        # check for alphabet order
        ...

    elif _token_start_as_int is None or _token_end_as_int is None:
        raise PydanticCustomError(
            "mixed_tokens",
            "Mixing alphabetical and \
                        numerical tokens is not supported: \
                        {token_start} and {token_end} \
                            in ({sig_start}, {sig_end})",
            {
                "sig_end": sig_end,
                "sig_start": sig_start,
                "token_end": token_end,
                "token_start": token_start,
            },
        )

    else:
        if _token_end_as_int < _token_start_as_int:
            raise ValueError(
                f"The upper end of the range \
                            should not be smaller than the lower end. \
                                ({sig_start},{sig_end})"
            )


def _validate_range(sig_start: str, sig_end: str):
    """Check if the range is valid.

    Args:
        sig_start (str): Start of the signature range
        sig_end (str): End of the signature range
    """
    if not (VALIDATION_REGEX.match(sig_start)):
        raise PydanticCustomError(
            "string_pattern_mismatch",
            "'{sig_start}' contains invalid characters \
                        (RegEx: {pattern})",
            {
                "sig_end": sig_end,
                "sig_start": sig_start,
                "pattern": VALIDATION_REGEX.pattern,
            },
        )
    if not (VALIDATION_REGEX.match(sig_end)):
        raise PydanticCustomError(
            "string_pattern_mismatch",
            "'{sig_end}' contains invalid characters \
                        (RegEx: {pattern})",
            {
                "sig_end": sig_end,
                "sig_start": sig_start,
                "pattern": VALIDATION_REGEX.pattern,
            },
        )

    _tokenized_start = tokenize(sig_start)
    _tokenized_end = tokenize(sig_end)

    if len(_tokenized_start) != len(_tokenized_end):
        raise PydanticCustomError(
            "mismatching_token_lengthss",
            "'{sig_start}' has a different length from '{sig_end}'\
                        ({_tokenized_start,_tokenized_end})",
            {
                "sig_start": sig_start,
                "sig_end": sig_end,
                "_tokenized_start": _tokenized_start,
                "_tokenized_end": _tokenized_end,
            },
        )

    for token_idx in range(len(_tokenized_start)):
        if _tokenized_start[token_idx] == _tokenized_end[token_idx]:
            continue
        else:
            _validate_tokens(
                _tokenized_start[token_idx],
                _tokenized_end[token_idx],
                sig_start=sig_start,
                sig_end=sig_end,
            )


def limitDictList2rangesXML(
    reader: Iterable[LimitDict],
    use_numerical: bool = False,
) -> "etree._Element":
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
    _errors: List[Union[LimitDict, int, ValueError]] = []

    _ranges = etree.Element("ranges")
    for idx, r in enumerate(reader):
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
        try:
            _validate_range(r["sig_start"], r["sig_end"])
        except ValueError as e:
            _errors.append(e)
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
    koko: io.TextIOWrapper,
    use_numerical: bool = False,
    delimiter: OneCharacterString = OneCharacterString(","),
) -> etree.ElementTree:
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
    # TODO Fix handling of files if provided via args
    reader = LimitDictReader(
        koko,
        delimiter=delimiter,
    )

    try:
        _ranges = limitDictList2rangesXML(reader, use_numerical=use_numerical)
    except Exception as e:
        reraise(
            e=e,
            info=f"""Error handling the provided koko{
                (' (' + koko.name + ')' )
                if hasattr(koko,"name") and koko.name
                else ''
            }""",
        )
    # TODO remove entries
    with open(EXAMPLE_XSL) as f:
        # TODO: Check why defusedxml has no getparent
        _tree: etree.ElementTree = etree.parse(f)  # nosec blacklist
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
