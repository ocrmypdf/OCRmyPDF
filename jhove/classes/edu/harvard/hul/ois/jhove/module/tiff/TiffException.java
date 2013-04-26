/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

/**
 *  Exception subclass used internally by the TIFF module.
 */
public final class TiffException extends Exception
{
    private long _offset;     // File offset at which the exception occurred

    /**
     *  Create a TiffException.
     */
    public TiffException (String m)
    {
	super(m);
	_offset = -1;
    }

    /**
     *  Create a TiffException with specified offset.
     */
    public TiffException (String m, long offset) 
    {
	super(m);
	_offset = offset;
    }

    /**
     *  Returns the offset at which the exception occurred.
     */
    public long getOffset ()
    {
	return _offset;
    }
}
