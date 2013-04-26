/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated use types for a Signature in a module. 
 *  These give information on whether a signature is required in
 *  valid content.
 *  Applications will not create or modify SignatureUseTypes, but will
 *  use one of the predefined SignatureUseType instances 
 *  MANDATORY, MANDATORY_IF_APPLICABLE, or OPTIONAL.
 *
 *  @see Signature
 */
public final class SignatureUseType
    extends EnumerationType
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** 
     *  Use type for a required signature.
     */
    public static final SignatureUseType MANDATORY =
	            new SignatureUseType ("Mandatory");


    /** 
     *  Use type for a conditionally required signature.
     */
    public static final SignatureUseType MANDATORY_IF_APPLICABLE =
	            new SignatureUseType ("Mandatory if applicable");
    /**
     *  Use type for an optional signature.
     */
    public static final SignatureUseType OPTIONAL =
	            new SignatureUseType ("Optional");

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Applications will never create SignatureUseTypes directly.
     **/
    private SignatureUseType (String value)
    {
	super (value);
    }
}
