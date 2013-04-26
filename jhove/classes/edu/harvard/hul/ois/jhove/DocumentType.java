/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated types for a Document.
 *  Applications will not create or modify DocumentTypes, but will
 *  use one of the predefined DocumentType instances 
 *  ARTICLE, BOOK, REPORT, RFC, STANDARD, WEB, or OTHER.
 *
 *  @see Document
 *  
 */
public final class DocumentType
    extends EnumerationType
{
    /**
     *  Document type for a printed article.
     */
    public static final DocumentType ARTICLE = new DocumentType ("Article");
    /**
     *  Document type for an book.
     */
    public static final DocumentType BOOK = new DocumentType ("Book");
    /**
     *  Document type for a report.
     */
    public static final DocumentType REPORT = new DocumentType ("Report");
    /**
     *  Document type for an IETF Request for Comment.
     */
    public static final DocumentType RFC = new DocumentType ("RFC");
    /**
     *  Document type for a standards body publication.
     */
    public static final DocumentType STANDARD = new DocumentType ("Standard");
    /**
     *  Document type for a Web page.
     */
    public static final DocumentType WEB = new DocumentType ("Web");
    /**
     *  Document type that doesn't fit the other categories.
     */
    public static final DocumentType OTHER = new DocumentType ("Other");

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Applications will never create DocumentTypes directly.
     **/
    private DocumentType (String value)
    {
	super (value);
    }
}
