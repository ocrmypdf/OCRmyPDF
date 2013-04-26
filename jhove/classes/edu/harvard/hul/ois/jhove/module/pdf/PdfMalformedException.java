/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Exception subclass used internally by the PDF module.
 *  A PdfMalformedException is thrown when a condition indicates
 *  that the document is not well-formed.
 * 
 *  @see PdfInvalidException
 */
@SuppressWarnings("serial")
public class PdfMalformedException extends PdfException {

    /**
     *  Creates a PdfMalformedException.
     */
    public PdfMalformedException (String m)
    {
        super(m);
    }

    /**
     *  Creates a PdfMalformedException with specified offset.
     */
    public PdfMalformedException (String m, long offset) 
    {
        super(m, offset);
    }

    /**
     *  Creates a PdfMalformedException with specified offset and token.
     */
    public PdfMalformedException (String m, long offset, Token token) 
    {
        super(m, offset, token);
    }

    /**
     *  Performs the appropriate disparagement act on a RepInfo
     *  object.  For a PdfInvalidException, this is to call 
     *  <code>setValid (false)</code>.
     */
    public void disparage (RepInfo info) 
    {
        info.setWellFormed (false);
    }

}
