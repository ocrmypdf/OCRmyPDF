/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Exception subclass used internally by the PDF module.
 *  A PdfInvalidException is thrown when a condition indicates
 *  that the document is invalid but not necessarily ill-formed.
 */
public final class PdfInvalidException extends PdfException
{

    /**
     *  Creates a PdfInvalidException.
     */
    public PdfInvalidException (String m)
    {
        super(m);
    }

    /**
     *  Creates a PdfInvalidException with specified offset.
     */
    public PdfInvalidException (String m, long offset) 
    {
        super(m, offset);
    }

    /**
     *  Creates a PdfInvalidException with specified offset and token.
     */
    public PdfInvalidException (String m, long offset, Token token) 
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
        info.setValid (false);
    }
}
