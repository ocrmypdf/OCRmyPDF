/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.Vector;

/**
 *  Abstract class for all PDF tokens which consist of a character sequence.
 */
public abstract class StringValuedToken
    extends Token
{
    protected String _value;
    protected Vector _rawBytes;

    public StringValuedToken ()
    {
        super ();
    }

    /**
     *  Get the value of the token as a String.
     */
    public String getValue ()
    {
        return _value;
    }

    /** 
     *  Get the value of the token's untranslated bytes. This is unsupported
     *  and will always return null.
     */
    public Vector getRawBytes ()
    {
        return _rawBytes;
    }

    /**
     *  Set the value of the token.
     */
    public void setValue (String value)
    {
        _value = value;
    }

}
