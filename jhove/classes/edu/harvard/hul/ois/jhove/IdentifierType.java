/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated types for an Identifier of a
 *  format specification document. 
 *  Applications will not create or modify IdentifierTypes, but will
 *  use one of the predefined IdentifierType instances 
 *  ANSI, DDC, DOI, ECMA, HANDLE, ISO, ISBN, LC, LCCN,
 *  NISO, PII, RFC, SICI, URI, URL, URN, or OTHER.
 *
 *  @see  Identifier
 */
public final class IdentifierType
    extends EnumerationType
{
    /**
     *  Identifier type for American National Standards Institute.
     */
    public static final IdentifierType ANSI = new IdentifierType ("ANSI");
    /**
     *  Identifier type for Dewey Decimal Classification.
     */
    public static final IdentifierType DDC = new IdentifierType ("DDC");
    /**
     *  Identifier type for Digital Object Identifier.
     */
    public static final IdentifierType DOI = new IdentifierType ("DOI");
    /**
     *  Identifier type for ECMA.
     */
    public static final IdentifierType ECMA = new IdentifierType ("ECMA");
    /**
     *  Identifier type for CNRI Handle.
     */
    public static final IdentifierType HANDLE = new IdentifierType ("Handle");
    /**
     *  Identifier type for International Standards Organization.
     */
    public static final IdentifierType ISO = new IdentifierType ("ISO");
    /**
     *  Identifier type for International Standard Book Number.
     */
    public static final IdentifierType ISBN = new IdentifierType ("ISBN");
    /**
     *  Identifier type for Library of Congress classification.
     */
    public static final IdentifierType LC = new IdentifierType ("LC");
    /**
     *  Identifier type for Library of Congress catalogue number.
     */
    public static final IdentifierType LCCN = new IdentifierType ("LCCN");
    /**
     *  Identifier type for NISO standard number.
     */
    public static final IdentifierType NISO = new IdentifierType ("NISO");
    /**
     *  Identifier type for Publisher Item Identifier.
     */
    public static final IdentifierType PII = new IdentifierType ("PII");
    /**
     *  Identifier type for IETF Request for Comment.
     */
    public static final IdentifierType RFC = new IdentifierType ("RFC");
    /**
     *  Identifier type for Serial Item and Contribution Identifier.
     */
    public static final IdentifierType SICI = new IdentifierType ("SICI");
    /**
     *  Identifier type for Uniform Resource Identifier.
     */
    public static final IdentifierType URI = new IdentifierType ("URI");
    /**
     *  Identifier type for Uniform Resource Locator.
     */
    public static final IdentifierType URL = new IdentifierType ("URL");
    /**
     *  Identifier type for Uniform Resource Name.
     */
    public static final IdentifierType URN = new IdentifierType ("URN");
    /**
     *  Identifier type for CCITT.
     */
    public static final IdentifierType CCITT = new IdentifierType ("CCITT");
    /**
     *  Identifier type for International Telecommunication Union.
     */
    public static final IdentifierType ITU = new IdentifierType ("ITU");
    /**
     *  Identifier type for Japan Electronics and Information Technology
     *  Industries Association.
     */
    public static final IdentifierType JEITA = new IdentifierType ("JEITA");
    /**
     *  Identifier type for whatever doesn't fit other categories.
     */
    public static final IdentifierType OTHER = new IdentifierType ("Other");

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Applications will never create SignatureTypes directly.
     **/
    private IdentifierType (String value)
    {
	super (value);
    }
}
