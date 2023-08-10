INSERT IGNORE INTO `STEP` VALUES (10012,'XmlTransformationStep','',NULL,'relationships','<xsl:stylesheet\r\n    version=\"1.0\"\r\n    xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\">\r\n\r\n  <xsl:output indent=\"yes\" method=\"xml\" version=\"1.0\" encoding=\"UTF-8\"/>\r\n\r\n  <xsl:template match=\"collection\">\r\n    <collection>\r\n        <xsl:apply-templates/>\r\n    </collection>\r\n  </xsl:template>\r\n\r\n  <xsl:template match=\"record\">\r\n    <record>\r\n        <xsl:for-each select=\"@* | node()\">\r\n            <xsl:copy-of select=\".\"/>\r\n        </xsl:for-each>\r\n        <xsl:apply-templates/>\r\n    </record>\r\n  </xsl:template>\r\n\r\n  <xsl:template match=\"original\">\r\n    <instanceRelations>\r\n      <!-- Parent instances -->\r\n      <xsl:if test=\"./datafield[@tag=\'036D\' or @tag=\'036F\' or @tag=\'039B\']\">\r\n        <parentInstances>\r\n          <arr>\r\n            <xsl:for-each select=\"datafield[@tag=\'036D\' or @tag=\'036F\' or @tag=\'039B\']\">\r\n              <i>\r\n                <xsl:call-template name=\"rel-body\"/>\r\n                <xsl:variable name=\'is-vol\' select=\"substring(../datafield[@tag=\'002@\']/subfield[@code=\'0\'], 2, 1)\"/>\r\n                <instanceRelationshipTypeId>\r\n                  <xsl:choose>\r\n                    <xsl:when test=\"./@tag=\'039B\'\">6366b68c-aeeb-4dfe-9cd5-92518b2244a0</xsl:when> <!-- article -->\r\n                    <xsl:when test=\"./@tag=\'036F\' and $is-vol=\'v\'\">23651816-7176-406a-8915-52e25b3a9411</xsl:when> <!-- volume -->\r\n                    <xsl:when test=\"./@tag=\'036D\'\">a17daf0a-f057-43b3-9997-13d0724cdf51</xsl:when> <!-- multi-part -->\r\n                    <xsl:when test=\"./@tag=\'036F\'\">30773a27-b485-4dab-aeb6-b8c04fa3cb17</xsl:when> <!-- series -->\r\n                    <xsl:otherwise>758f13db-ffb4-440e-bb10-8a364aa6cb4a</xsl:otherwise> <!-- bound with -->\r\n                  </xsl:choose>\r\n                </instanceRelationshipTypeId>\r\n              </i>\r\n            </xsl:for-each>\r\n          </arr>\r\n        </parentInstances>\r\n      </xsl:if>\r\n      <xsl:variable name=\"prec\" select=\"./datafield[@tag=\'039E\' and subfield[@code=\'b\']=\'f\']\"/>\r\n      <xsl:if test=\"$prec\">\r\n        <precedingTitles>\r\n          <arr>\r\n            <xsl:for-each select=\"$prec\">\r\n              <i>\r\n                <xsl:call-template name=\"rel-body\" />\r\n              </i>\r\n            </xsl:for-each>\r\n          </arr>\r\n        </precedingTitles>\r\n      </xsl:if>\r\n      <xsl:variable name=\"succ\" select=\"./datafield[@tag=\'039E\' and subfield[@code=\'b\']=\'s\']\"/>\r\n      <xsl:if test=\"$succ\">\r\n        <succeedingTitles>\r\n          <arr>\r\n            <xsl:for-each select=\"$succ\">\r\n              <i>\r\n                <xsl:call-template name=\"rel-body\" />\r\n              </i>\r\n            </xsl:for-each>\r\n          </arr>\r\n        </succeedingTitles>\r\n      </xsl:if>\r\n    </instanceRelations>\r\n  </xsl:template>\r\n  <xsl:template match=\"text()\"/>\r\n  \r\n  <xsl:template name=\"rel-body\">\r\n    <instanceIdentifier>\r\n      <hrid><xsl:value-of select=\"./subfield[@code=\'9\']\"/></hrid>\r\n    </instanceIdentifier>\r\n    <provisionalInstance>\r\n      <title>\r\n        <xsl:choose>\r\n          <xsl:when test=\"contains(./subfield[@code=8], \' ; \')\"><xsl:value-of select=\"substring-before(./subfield[@code=\'8\'], \' ; \')\"/></xsl:when>\r\n          <xsl:otherwise><xsl:value-of select=\"./subfield[@code=\'8\']\"/></xsl:otherwise>\r\n        </xsl:choose>\r\n      </title>\r\n      <instanceTypeId><xsl:value-of select=\"../../instance/instanceTypeId\"/></instanceTypeId>\r\n      <source><xsl:value-of select=\"../../instance/source\"/></source>\r\n    </provisionalInstance>\r\n  </xsl:template>\r\n</xsl:stylesheet>\r\n',NULL,'xml','xml',NULL,NULL,NULL,NULL);
