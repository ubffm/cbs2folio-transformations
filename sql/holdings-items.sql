INSERT IGNORE INTO `STEP` VALUES (10013,'XmlTransformationStep','',NULL,'holdings-items','<xsl:stylesheet xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\" version=\"1.0\">\r\n  <xsl:output indent=\"yes\" method=\"xml\" version=\"1.0\" encoding=\"UTF-8\"/>\r\n\r\n  <xsl:template match=\"collection\">\r\n    <collection>\r\n        <xsl:apply-templates/>\r\n    </collection>\r\n  </xsl:template>\r\n\r\n  <xsl:template match=\"record\">\r\n    <record>\r\n        <xsl:for-each select=\"@* | node()\">\r\n            <xsl:copy-of select=\".\"/>\r\n        </xsl:for-each>\r\n        <xsl:apply-templates/>\r\n    </record>\r\n  </xsl:template>\r\n\r\n  <xsl:template match=\"original\">\r\n    <xsl:if test=\"item/datafield[@tag=\'203@\']/subfield[@code=\'0\']\">\r\n      <holdingsRecords>\r\n        <arr>\r\n          <xsl:apply-templates select=\"item\"/>\r\n       </arr>\r\n      </holdingsRecords>\r\n    </xsl:if>\r\n  </xsl:template>\r\n\r\n  <xsl:template match=\"item\">\r\n    <i>\r\n      <xsl:variable name=\"hhrid\" select=\"datafield[@tag=\'203@\']/subfield[@code=\'0\']\"/>\r\n      <hrid>\r\n        <xsl:value-of select=\"$hhrid\"/>\r\n      </hrid>\r\n      <xsl:variable name=\"lcode\" select=\"datafield[@tag=\'209A\']/subfield[@code=\'f\']\"/>\r\n      <permanentLocationId>\r\n        <xsl:value-of select=\"$lcode\"/>\r\n      </permanentLocationId>\r\n      <callNumber>\r\n        <xsl:value-of select=\"datafield[@tag=\'209A\']/subfield[@code=\'a\']\"/>\r\n      </callNumber>\r\n	  <holdingsTypeId>\r\n	    <xsl:variable name=\"holType\" select=\"../datafield[@tag=\'002@\']/subfield[@code=\'0\']\"/>\r\n		<xsl:variable name=\"holType1\" select=\"substring($holType, 1, 1)\"/>\r\n		<xsl:choose>\r\n		  <xsl:when test=\"$holType1 = \'O\'\">electronic</xsl:when>\r\n		  <xsl:otherwise>physical</xsl:otherwise>\r\n		</xsl:choose>\r\n	  </holdingsTypeId>\r\n      <holdingsStatements>\r\n	    <xsl:if test=\"datafield[@tag=\'231B\']/subfield[@code=\'a\']\">\r\n		  <arr>\r\n		    <xsl:for-each select=\"datafield[@tag=\'231B\']/subfield[@code=\'a\']\">\r\n			  <i>\r\n			    <statement>\r\n				  <xsl:value-of select=\".\"/>\r\n				</statement>\r\n              </i>\r\n			</xsl:for-each>\r\n		  </arr>\r\n	    </xsl:if>\r\n      </holdingsStatements>\r\n	  <sourceId>K10plus</sourceId>\r\n	  <discoverySuppress>\r\n        <xsl:choose>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'c\'\">true</xsl:when>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'d\'\">true</xsl:when>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'e\'\">true</xsl:when>\r\n          <xsl:otherwise>false</xsl:otherwise>\r\n        </xsl:choose>\r\n      </discoverySuppress>\r\n      <xsl:if test=\"datafield[@tag=\'220B\' or @tag=\'237A\' or @tag=\'244Z\' or @tag=\'209O\' or @tag=\'206X\' or @tag=\'206W\']\">\r\n        <notes>\r\n          <arr>\r\n            <!-- 4801 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'237A\']\">\r\n              <xsl:if test=\"./subfield[@code=\'a\'] or ./subfield[@code=\'0\']\">\r\n                <i>\r\n                  <note>\r\n                    <xsl:value-of select=\"./subfield[@code=\'a\'] | ./subfield[@code=\'0\']\"/>\r\n                  </note>\r\n                  <holdingsNoteTypeId>Exemplarbezogener Kommentar - benutzerrelevante Hinweise (4801)</holdingsNoteTypeId>\r\n                  <staffOnly>false</staffOnly>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n            <!-- 4802 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'220B\']\">\r\n              <xsl:if test=\"./subfield[@code=\'a\'] or ./subfield[@code=\'0\']\">\r\n                <i>\r\n                  <note>\r\n                    <xsl:value-of select=\"./subfield[@code=\'a\'] | ./subfield[@code=\'0\']\"/>\r\n                  </note>\r\n                  <holdingsNoteTypeId>Exemplarbezogener Kommentar - bibliotheksinterne Hinweise (4802)</holdingsNoteTypeId>\r\n                  <staffOnly>true</staffOnly>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n            <!-- 6800 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'244Z\']\">\r\n              <xsl:variable name=\"expansion\" select=\"substring-before(./subfield[@code=\'8\'], \' ; ID:\')\"/>\r\n              <i>\r\n                <note>\r\n                  <xsl:choose>\r\n                    <xsl:when test=\"./subfield[@code=\'S\']\">\r\n                      <xsl:choose>\r\n                        <xsl:when test=\"$expansion\">\r\n                          <xsl:value-of select=\"concat(./subfield[@code=\'S\'], \' \', $expansion)\"/>\r\n                        </xsl:when>\r\n                        <xsl:when test=\"./subfield[@code=\'8\']\">\r\n                          <xsl:value-of select=\"concat(./subfield[@code=\'S\'], \' \', ./subfield[@code=\'8\'])\"/>\r\n                        </xsl:when>\r\n                        <xsl:when test=\"./subfield[@code=\'a\']\">\r\n                          <xsl:value-of select=\"concat(./subfield[@code=\'S\'], \' \', ./subfield[@code=\'a\'])\"/>\r\n                        </xsl:when>\r\n                      </xsl:choose>\r\n                    </xsl:when>\r\n                    <xsl:otherwise>\r\n                      <xsl:choose>\r\n                        <xsl:when test=\"$expansion\">\r\n                          <xsl:value-of select=\"$expansion\"/>\r\n                        </xsl:when>\r\n                        <xsl:when test=\"./subfield[@code=\'8\']\">\r\n                          <xsl:value-of select=\"./subfield[@code=\'8\']\"/>\r\n                        </xsl:when>\r\n                        <xsl:when test=\"./subfield[@code=\'a\']\">\r\n                          <xsl:value-of select=\"./subfield[@code=\'a\']\"/>\r\n                        </xsl:when>\r\n                      </xsl:choose>\r\n                    </xsl:otherwise>\r\n                  </xsl:choose>\r\n                </note>\r\n                <holdingsNoteTypeId>Lokale Schlagwörter (6800)</holdingsNoteTypeId>\r\n                <staffOnly>false</staffOnly>\r\n              </i>\r\n            </xsl:for-each>\r\n            <!-- 8600 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'209O\']\">\r\n              <xsl:if test=\"./subfield[@code=\'a\']\">\r\n                <i>\r\n                  <note>\r\n                    <xsl:value-of select=\"./subfield[@code=\'a\']\"/>\r\n                  </note>\r\n                  <holdingsNoteTypeId>Abrufzeichen exemplarspezifisch (8600)</holdingsNoteTypeId>\r\n                  <staffOnly>true</staffOnly>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n            <!-- 7811 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'206X\']\">\r\n              <xsl:if test=\"./subfield[@code=\'0\']\">\r\n                <i>\r\n                  <note>\r\n                    <xsl:value-of select=\"./subfield[@code=\'0\']\"/>\r\n                  </note>\r\n                  <holdingsNoteTypeId>Lokale Identifikationsnummer anderer Systeme (7811)</holdingsNoteTypeId>\r\n                  <staffOnly>false</staffOnly>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n            <!-- 7812 -->\r\n            <xsl:for-each select=\"datafield[@tag=\'206W\']\">\r\n              <xsl:if test=\"./subfield[@code=\'0\']\">\r\n                <i>\r\n                  <note>\r\n                    <xsl:value-of select=\"./subfield[@code=\'0\']\"/>\r\n                  </note>\r\n                  <holdingsNoteTypeId>Lokale Identifikationsnummer externer Systeme (7812)</holdingsNoteTypeId>\r\n                  <staffOnly>false</staffOnly>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n          </arr>\r\n        </notes>\r\n      </xsl:if>\r\n      <xsl:if test=\"datafield[@tag=\'209R\']\">\r\n        <electronicAccess>\r\n          <arr>\r\n            <xsl:for-each select=\"datafield[@tag=\'209R\']\">\r\n              <xsl:if test=\"./subfield[@code=\'u\']\">\r\n                <i>\r\n                  <uri>\r\n                    <xsl:value-of select=\"./subfield[@code=\'u\']\"/>\r\n                  </uri>\r\n                  <relationshipId>f5d0068e-6272-458e-8a81-b85e7b9a14aa</relationshipId>\r\n                  <!-- Resource -->\r\n                  <xsl:if test=\"../datafield[@tag=\'209K\']\">\r\n                    <publicNote>\r\n                      <xsl:variable name=\"enote\" select=\"../datafield[@tag=\'209K\'][1]/subfield[@code=\'a\']\"/>\r\n                      <xsl:variable name=\"bnote\" select=\"../datafield[@tag=\'209K\'][1]/subfield[@code=\'b\']\"/>\r\n                      <xsl:variable name=\"cnote\" select=\"../datafield[@tag=\'209K\'][1]/subfield[@code=\'c\']\"/>\r\n                      <xsl:choose>\r\n                        <xsl:when test=\"$enote=\'a\'\">Zugriffsrechte: domain, der Zugriff ist nur hausintern möglich</xsl:when>\r\n                        <xsl:when test=\"$enote=\'b\'\">Zugriffsrechte: free, der Zugriff ist unbeschränkt möglich</xsl:when>\r\n                        <xsl:when test=\"$enote=\'c\'\">Zugriffsrechte: blocked, der Zugriff ist gar nicht möglich</xsl:when>\r\n                        <xsl:when test=\"$enote=\'d\'\">Zugriffsrechte: domain+, der Zugriff ist hausintern und für bestimmte zugelassene, andere Benutzer möglich</xsl:when>\r\n                        <xsl:when test=\"$bnote\">\r\n                          <xsl:value-of select=\"concat(\'Zahl der parallelen Zugriffe: \', $bnote)\"/>\r\n                        </xsl:when>\r\n                      </xsl:choose>\r\n                      <xsl:choose>\r\n                        <xsl:when test=\"$cnote and ($enote or $bnote)\">\r\n                          <xsl:value-of select=\"concat(\' ; \', $cnote)\"/>\r\n                        </xsl:when>\r\n                        <xsl:when test=\"$cnote\">\r\n                          <xsl:value-of select=\"$cnote\"/>\r\n                        </xsl:when>\r\n                      </xsl:choose>\r\n                    </publicNote>\r\n                  </xsl:if>\r\n                </i>\r\n              </xsl:if>\r\n            </xsl:for-each>\r\n          </arr>\r\n        </electronicAccess>\r\n      </xsl:if>\r\n      <items>\r\n        <arr>\r\n          <xsl:choose>\r\n            <xsl:when test=\"datafield[@tag=\'209G\']/subfield[@code=\'a\'][2]\">\r\n              <xsl:for-each select=\"datafield[@tag=\'209G\']/subfield[@code=\'a\']\">\r\n                <xsl:apply-templates select=\"../..\" mode=\"make-item\">\r\n                  <xsl:with-param name=\"hhrid\" select=\"concat($hhrid, \'-\', .)\"/>\r\n                  <xsl:with-param name=\"bcode\" select=\".\"/>\r\n                  <xsl:with-param name=\"copy\" select=\"./following-sibling::subfield[@code=\'c\'][1]\"/>\r\n                </xsl:apply-templates>\r\n              </xsl:for-each>\r\n            </xsl:when>\r\n            <!-- start implement bound-with case -->\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'i\']\">\r\n              <xsl:if test=\"datafield[@tag=\'209G\']/subfield[@code=\'a\']\">\r\n                <xsl:apply-templates select=\".\" mode=\"make-item\">\r\n                  <xsl:with-param name=\"hhrid\" select=\"$hhrid\"/>\r\n                </xsl:apply-templates>             \r\n              </xsl:if>\r\n              <xsl:if test=\"not(datafield[@tag=\'209G\']/subfield[@code=\'a\'])\">\r\n                <!-- exit and don\'t create an item -->\r\n              </xsl:if>\r\n            </xsl:when>\r\n            <!-- end implement bound-with case -->\r\n            <xsl:otherwise>\r\n              <xsl:apply-templates select=\".\" mode=\"make-item\">\r\n                <xsl:with-param name=\"hhrid\" select=\"$hhrid\"/>\r\n              </xsl:apply-templates>\r\n            </xsl:otherwise>\r\n          </xsl:choose>\r\n        </arr>\r\n      </items>\r\n    </i>\r\n  </xsl:template>\r\n  <xsl:template match=\"item\" mode=\"make-item\">\r\n    <xsl:param name=\"hhrid\"/>\r\n    <xsl:param name=\"bcode\" select=\"datafield[@tag=\'209G\']/subfield[@code=\'a\']\"/>\r\n    <xsl:param name=\"copy\" select=\"datafield[@tag=\'209G\']/subfield[@code=\'c\']\"/>\r\n    <i>\r\n      <hrid>\r\n        <xsl:value-of select=\"$hhrid\"/>\r\n      </hrid>\r\n      <materialTypeId>\r\n        <xsl:variable name=\"type\" select=\"../datafield[@tag=\'002@\']/subfield[@code=\'0\']\"/>\r\n        <xsl:variable name=\"type1\" select=\"substring($type, 1, 1)\"/>\r\n        <xsl:variable name=\"type12\" select=\"substring($type, 1, 2)\"/>\r\n        <xsl:variable name=\"type2\" select=\"substring($type, 2, 1)\"/>\r\n        <xsl:variable name=\"pd\" select=\"../datafield[@tag=\'013H\']/subfield[@code=\'a\']\"/>\r\n        <xsl:variable name=\"mt\" select=\"../datafield[@tag=\'002D\']/subfield[@code=\'b\']\"/>\r\n        <xsl:choose>\r\n          <xsl:when test=\"$type12 = \'Ab\'\">\r\n            <xsl:choose>\r\n              <xsl:when test=\"$pd = \'zt\'\">Zeitung</xsl:when>\r\n              <xsl:otherwise>Zeitschrift</xsl:otherwise>\r\n            </xsl:choose>\r\n          </xsl:when>\r\n          <xsl:when test=\"$type2 = \'s\'\">Aufsatz</xsl:when>\r\n          <xsl:when test=\"$type2 = \'c\'\">Mehrteilige Monografie</xsl:when>\r\n          <xsl:when test=\"$type2 = \'d\'\">Serie</xsl:when>\r\n          <xsl:when test=\"$type1 = \'A\'\">\r\n            <xsl:choose>\r\n              <xsl:when test=\"$pd = \'kart\'\">Karte(nwerk)</xsl:when>\r\n              <xsl:when test=\"$pd = \'lo\'\">Loseblattwerk</xsl:when>\r\n              <xsl:when test=\"$pd = \'muno\'\">Musiknote</xsl:when>\r\n              <xsl:otherwise>Buch</xsl:otherwise>\r\n            </xsl:choose>\r\n          </xsl:when>\r\n          <xsl:when test=\"$type1 = \'B\'\">\r\n            <xsl:choose>\r\n              <xsl:when test=\"$pd = \'vide\' or $mt = \'v\'\">Film (DVD/Video)</xsl:when>\r\n              <xsl:when test=\"$mt = \'g\' or $mt = \'n\'\">Bild(ersammlung)</xsl:when>\r\n              <xsl:when test=\"$pd = \'muno\'\">Musiknote</xsl:when>\r\n              <xsl:otherwise>Tonträger</xsl:otherwise>\r\n            </xsl:choose>\r\n          </xsl:when>\r\n          <xsl:when test=\"$type1 = \'C\'\">Blindenschriftträger</xsl:when>\r\n          <xsl:when test=\"$type1 = \'E\'\">Mikroform</xsl:when>\r\n          <xsl:when test=\"$type1 = \'H\'\">Handschrift</xsl:when>\r\n          <xsl:when test=\"$type1 = \'O\'\">E-Ressource</xsl:when>\r\n          <xsl:when test=\"$type1 = \'S\'\">E-Ressource auf Datenträger</xsl:when>\r\n          <xsl:when test=\"$type1 = \'V\'\">Objekt</xsl:when>\r\n          <xsl:when test=\"$type = \'Lax\'\">Lax</xsl:when>\r\n          <xsl:otherwise>Nicht spezifiziert</xsl:otherwise>\r\n        </xsl:choose>\r\n      </materialTypeId>\r\n      <permanentLoanTypeId>\r\n        <xsl:variable name=\"loantype\" select=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']\"/>\r\n        <xsl:choose>\r\n          <xsl:when test=\"$loantype=\'u\'\">ausleihbar/Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'b\'\">verkürzt ausleihbar/Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'c\'\">ausleihbar/keine Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'s\'\">mit Zustimmung ausleihbar/nur Kopie in die Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'d\'\">mit Zustimmung ausleihbar/Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'i\'\">Lesesaalausleihe/keine Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'f\'\">Lesesaalausleihe/nur Kopie in die Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'g\'\">für die Ausleihe gesperrt/keine Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'a\'\">bestellt/keine Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'o\'\">keine Angabe/keine Fernleihe</xsl:when>\r\n          <xsl:when test=\"$loantype=\'z\'\">Verlust/keine Fernleihe</xsl:when>\r\n          <xsl:otherwise>ausleihbar/Fernleihe</xsl:otherwise>\r\n        </xsl:choose>\r\n      </permanentLoanTypeId>\r\n      <status>\r\n		<xsl:variable name=\"frequency\" select=\"substring(../datafield[@tag=\'002@\']/subfield[@code=\'0\'],2,1)\"/>\r\n        <name>\r\n          <xsl:choose>\r\n			      <xsl:when test=\"$frequency=\'b\'\">Intellectual item</xsl:when>\r\n			      <xsl:when test=\"$frequency=\'c\'\">Intellectual item</xsl:when>\r\n			      <xsl:when test=\"$frequency=\'d\'\">Intellectual item</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'a\'\">On order</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'u\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'b\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'c\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'s\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'d\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'i\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'f\'\">Available</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'z\'\">Missing</xsl:when>\r\n            <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'g\'\">Restricted</xsl:when>\r\n			      <xsl:when test=\"datafield[@tag=\'209A\']/subfield[@code=\'d\']=\'o\'\">Unknown</xsl:when>\r\n            <xsl:otherwise>Available</xsl:otherwise>\r\n          </xsl:choose>\r\n        </name>\r\n      </status>\r\n      <xsl:if test=\"$bcode\">\r\n        <barcode>\r\n          <xsl:value-of select=\"$bcode\"/>\r\n        </barcode>\r\n      </xsl:if>\r\n      <copyNumber>\r\n        <xsl:value-of select=\"$copy\"/>\r\n      </copyNumber>\r\n      <volume>\r\n        <xsl:for-each select=\"datafield[@tag=\'231@\']/subfield[@code=\'d\' or @code=\'n\']\">\r\n          <xsl:choose>\r\n            <xsl:when test=\"./@code=\'n\'\">\r\n              <xsl:value-of select=\"concat(\'-\', .)\"/>\r\n            </xsl:when>\r\n            <xsl:when test=\"./@code=\'d\' and position()&gt;1\">\r\n              <xsl:value-of select=\"concat(\', \', .)\"/>\r\n            </xsl:when>\r\n            <xsl:otherwise>\r\n              <xsl:value-of select=\".\"/>\r\n            </xsl:otherwise>\r\n          </xsl:choose>\r\n          <xsl:if test=\"position()=last() and ./@code=\'d\' and ../subfield[@code=\'6\']\">-</xsl:if>\r\n        </xsl:for-each>\r\n      </volume>\r\n      <chronology>\r\n        <xsl:for-each select=\"datafield[@tag=\'231@\']/subfield[@code=\'j\' or @code=\'k\']\">\r\n          <xsl:choose>\r\n            <xsl:when test=\"./@code=\'k\'\">\r\n              <xsl:value-of select=\"concat(\'-\', .)\"/>\r\n            </xsl:when>\r\n            <xsl:when test=\"./@code=\'j\' and position()&gt;1\">\r\n              <xsl:value-of select=\"concat(\', \', .)\"/>\r\n            </xsl:when>\r\n            <xsl:otherwise>\r\n              <xsl:value-of select=\".\"/>\r\n            </xsl:otherwise>\r\n          </xsl:choose>\r\n          <xsl:if test=\"position()=last() and ./@code=\'j\' and ../subfield[@code=\'6\']\">-</xsl:if>\r\n        </xsl:for-each>\r\n      </chronology>\r\n      <enumeration>\r\n        <xsl:value-of select=\"datafield[@tag=\'231B\']/subfield[@code=\'a\']\"/>\r\n      </enumeration>\r\n      <descriptionOfPieces>\r\n        <xsl:value-of select=\"datafield[@tag=\'208F\']/subfield[@code=\'a\']\"/>\r\n      </descriptionOfPieces>\r\n      <accessionNumber>\r\n        <xsl:for-each select=\"datafield[@tag=\'209C\']\">\r\n          <xsl:value-of select=\"./subfield[@code=\'a\']\"/>\r\n          <xsl:if test=\"position() != last()\">, </xsl:if>\r\n        </xsl:for-each>\r\n      </accessionNumber>\r\n      <discoverySuppress>\r\n        <xsl:choose>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'c\'\">true</xsl:when>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'d\'\">true</xsl:when>\r\n          <xsl:when test=\"substring(datafield[@tag=\'208@\']/subfield[@code=\'b\'],1,1)=\'e\'\">true</xsl:when>\r\n          <xsl:otherwise>false</xsl:otherwise>\r\n        </xsl:choose>\r\n      </discoverySuppress>\r\n    </i>\r\n  </xsl:template>\r\n  <xsl:template match=\"text()\"/>\r\n</xsl:stylesheet>\r\n',NULL,'xml','xml',NULL,'','',NULL);
