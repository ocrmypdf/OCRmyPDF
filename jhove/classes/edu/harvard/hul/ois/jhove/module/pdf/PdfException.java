/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Abstract exception subclass used internally by the PDF module.
 *  Throwing a PDFException indicates that the document is
 *  ill-formed or invalid; use the appropriate subclass to
 *  indicate which.
 */
public abstract class PdfException extends Exception
{
    
    /* Note 25-Feb-2004:  Previously PdfException indicated
     * a not-well-formed condition, and PdfInvalidException
     * was a subclass of PdfException that indicated an
     * invalid condition.  This is a bad class hierarchy,
     * since the role of PdfException was ambiguous,
     * so PdfMalformedException was added, and PdfException
     * was made abstract.
     */
    private long _offset;     // File offset at which the exception occurred
    private Token _token;     // Token associated with the exception

    /**
     *  Create a PdfException.
     */
    public PdfException (String m)
    {
        super(m);
        _offset = -1;
        _token = null;
    }

    /**
     *  Create a PdfException with specified offset.
     */
    public PdfException (String m, long offset) 
    {
        super(m);
        _offset = offset;
        _token = null;
    }

    /**
     *  Create a PdfException with specified offset and token.
     */
    public PdfException (String m, long offset, Token token) 
    {
        super(m);
        _offset = offset;
        _token = token;
    }

    /**
     *  Returns the offset at which the exception occurred.
     */
    public long getOffset ()
    {
        return _offset;
    }
    
    /**
     *  Return the token associated with the exception.
     */
    public Token getToken ()
    {
        return _token;
    }

    /**
     *  Performs the appropriate disparagement act on a RepInfo
     *  object, such as setting the valid or well-formed
     *  flag to <code>false</code>.
     */
    public abstract void disparage (RepInfo info);

}
