/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  Class for Tokens which represent PDF names.
 */
public class Name
    extends StringValuedToken
{
    /** Creates an instance of a Name */
    public Name ()
    {
        super ();
    }
    
    /** Returns true if it's within the PDF/A implementation limit */
    public boolean isPdfACompliant () {
        return _value.getBytes().length <= 127; 
    }
}
