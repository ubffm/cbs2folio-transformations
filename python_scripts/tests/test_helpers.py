#!/usr/bin/env python3
import logging
from typing import List
from typing import Tuple

import pytest
from cbs2folio_transformations._helpers import get_variable_from_xsl
from lxml import etree  # nosec blacklist


SignatureTuple = Tuple[str, List[str]]

logger = logging.getLogger()

NAMESPACES = {"xsl": "http://www.w3.org/1999/XSL/Transform"}


@pytest.mark.parametrize(
    "variable_name,xsl,value",
    [
        pytest.param(
            "sortChar",
            etree.fromstring(
                """<?xml version="1.0" encoding="UTF-8"?>
                    <xsl:stylesheet
                        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                        xmlns:exsl="http://exslt.org/common"
                        version="1.1"
                        exclude-result-prefixes="exsl">

                    <xsl:variable
                        name="sortChar">'0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz'</xsl:variable>
                    </xsl:stylesheet>
                    """.encode()
            ),
            "0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz",
            id="Value in Text",
        ),
        pytest.param(
            "sortChar",
            etree.fromstring(
                """<?xml version="1.0" encoding="UTF-8"?>
                    <xsl:stylesheet
                        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                        xmlns:exsl="http://exslt.org/common"
                        version="1.1"
                        exclude-result-prefixes="exsl">

                    <xsl:variable name="sortChar">
                    <xsl:value-of
                        select="'0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz'"/>
                    </xsl:variable>
                    </xsl:stylesheet>
                    """.encode()
            ),
            "0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz",
            id="Value in value-of",
        ),
        pytest.param(
            "sortChar",
            etree.fromstring(
                """<?xml version="1.0" encoding="UTF-8"?>
                    <xsl:stylesheet
                        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                        xmlns:exsl="http://exslt.org/common"
                        version="1.1"
                        exclude-result-prefixes="exsl">

                    <xsl:variable name="sortChar">
                    <xsl:value-of
                        select="'0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz'"/>
                    </xsl:variable>
                    </xsl:stylesheet>
                    """.encode()
            ),
            "0123456789aäbcdefghijklmnoöpqrsßtuüvwxyz",
            id="Value in value-of",
        ),
    ],
)
def test_get_variable_from_xsl(variable_name, xsl, value):
    assert (  # nosec assert_used
        get_variable_from_xsl(variable_name=variable_name, xsl=xsl) == value
    )
