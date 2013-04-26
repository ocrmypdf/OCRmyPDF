/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-4 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates information about external format signatures.
 *   The value of a Signature may be either a String or a byte array
 *   (stored as an int array to avoid signed byte problems).
 */
public class ExternalSignature
    extends Signature
{
    /**
     *  Creates an ExternalSignature given a string value, a type,
     *  and a use requirement.  
     */
    public ExternalSignature (String value, SignatureType type,
			      SignatureUseType use)
    {
	super (value, type, use);
    }

    /**
     *  Creates an ExternalSignature given a byte array, a type,
     *  and a use requirement.
     */
    public ExternalSignature (int[] value, SignatureType type,
			      SignatureUseType use)
    {
	super (value, type, use);
    }

    /**
     *  Creates an ExternalSignature given a string value, a type,
     *  a use requirement, and a note.  
     */
    public ExternalSignature (String value, SignatureType type,
                  SignatureUseType use,
                  String note)
    {
        super (value, type, use, note);
    }


    /**
     *  Creates an ExternalSignature given a byte array, a type,
     *  a use requirement, and a note.
     */
    public ExternalSignature (int[] value, SignatureType type,
                  SignatureUseType use,
                  String note)
    {
        super (value, type, use, note);
    }


}
