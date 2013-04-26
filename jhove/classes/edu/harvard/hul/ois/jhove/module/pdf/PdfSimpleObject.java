/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;

/**
 *  A representation of a PDF object which can be represented
 *  by a Token.  In some cases, this means that the full
 *  content of the object isn't stored, because we don't
 *  (think we) need it for our purposes.
 */
public class PdfSimpleObject extends PdfObject
{

    private Token _token;

    /** 
     *  Creates a PdfSimpleObject.
     *
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     *  @param token      The Token represented by this object
     */
    public PdfSimpleObject (Token token, int objNumber, int genNumber)
    {
        super (objNumber, genNumber);
        _token = token;
    }


    /** 
     *  Creates a PdfSimpleObject.
     *
     *  @param token      The Token represented by this object
     */
    public PdfSimpleObject (Token token)
    {
        super ();
        _token = token;
    }

    /**
     *  Returns the token represented by this object.
     */
    public Token getToken ()
    {
        return _token;
    }

    /**
     *  Return the string value of the token.  Returns
     *  null if the token is not a StringValuedToken.
     */
    public String getStringValue ()
    {
        if (!(_token instanceof StringValuedToken)) {
            return null;
        }
        else {
            return ((StringValuedToken) _token).getValue ();
        }
    }


    /**
     *  Return the raw bytes of the token, as a Vector of Integer objects.
     *  Returns null if the token is not a StringValuedToken.
     */
    public Vector getRawBytes ()
    {
        if (!(_token instanceof StringValuedToken)) {
            return null;
        }
        else {
            return ((StringValuedToken) _token).getRawBytes ();
        }
    }


    /**
     *  Return the integer value of the token.  Throws a ClassCastException
     *  if the token is not a Numeric.
     */
    public int getIntValue ()
    {
        return ((Numeric) _token).getIntegerValue ();
    }

    /**
     *  Return the <code>double</code> value of the token.  Throws a 
     *  ClassCastException if the token is not a Numeric.
     */
    public double getDoubleValue ()
    {
        return ((Numeric) _token).getValue ();
    }
    
    /**
     *  Return <code>true</code> if the value of the token is the keyword
     *  "true", and false otherwise.
     */
    public boolean isTrue () 
    {
        if (!(_token instanceof Keyword)) {
                return false;
        }
        else {
                return "true".equals (((Keyword) _token).getValue ());
        }
    }

    /**
     *  Return <code>true</code> if the value of the token is the keyword
     *  "false", and false otherwise.
     */
    public boolean isFalse () 
    {
        if (!(_token instanceof Keyword)) {
                return false;
        }
        else {
                return "false".equals (((Keyword) _token).getValue ());
        }
    }

}
