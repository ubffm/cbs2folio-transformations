#!/usr/bin/env python3
import logging
from typing import List
from typing import Tuple

import pytest
from cbs2folio_transformations._helpers import get_param_default_from_xsl
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


@pytest.mark.parametrize(
    "param_name,xsl,value",
    [
        pytest.param(
            "token-markers",
            etree.fromstring(
                """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  version="1.1"
  exclude-result-prefixes="exsl"
  >
  <!-- Normalize a signature or range -->
  <xsl:template name="normalize-signature-or-range">
    <xsl:param name="text"/>
    <xsl:param name="token-markers" select="' /.:'" />
    <xsl:variable name="token-replacement">
      <xsl:call-template name="replace-with-space">
        <xsl:with-param name="text" select="$token-markers"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$debug-template-logic-verbosity">
      <xsl:message>Debug:
        Text: "<xsl:value-of select="$text"/>"
        Normalized: "<xsl:value-of
        select="normalize-space(
            translate($text, $token-markers, $token-replacement )
            )"
        />"
        Markers: "<xsl:value-of select="$token-markers"/>"
        Replacement: "<xsl:value-of select="$token-replacement"/>"
      </xsl:message>
    </xsl:if>
      <xsl:value-of
      select="normalize-space(
        translate($text, $token-markers, $token-replacement )
        )"
        />
  </xsl:template>
</xsl:stylesheet>
                    """.encode()
            ),
            " /.:",
        )
    ],
)
def test_get_param_default_from_xsl(param_name, xsl, value):
    assert (  # nosec assert_used
        get_param_default_from_xsl(param_name=param_name, xsl=xsl) == value
    )
