/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2009 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated types for an Property of 
 *  some given content. 
 *  Applications will not create or modify PropertyTypes, but will
 *  use one of the predefined PropertyType instances 
 *  BOOLEAN, BYTE, CHARACTER, DATE, DOUBLE, FLOAT, INTEGER,
 *  LONG, OBJECT, PROPERTY, SHORT, STRING, RATIONAL, or
 *  NISOIMAGEMETADATA.
 *
 *  @see Property
 */
public final class PropertyType
    extends EnumerationType
{
    /**
     *  Property type for a <code>Boolean</code> object, or a
     *  <code>boolean</code> if the Arity is Array.
     */
    public static final PropertyType BOOLEAN = new PropertyType ("Boolean");
    /**
     *  Property type for a <code>Byte</code> object, or a <code>byte</code>
     *  if the Arity is Array.
     */
    public static final PropertyType BYTE = new PropertyType ("Byte");
    /**
     *  Property type for a <code>Character</code> object, or a
     *  <code>char</code> if the Arity is Array.
     */
    public static final PropertyType CHARACTER = new PropertyType("Character");
    /**
     *  Property type for a <code>Date</code> object.
     */
    public static final PropertyType DATE = new PropertyType ("Date");
    /**
     *  Property type for a <code>Double</code> object, or 
     *a <code>double</code> if the Arity is Array.
     */
    public static final PropertyType DOUBLE = new PropertyType ("Double");
    /**
     *  Property type for a <code>Float</code> object, or a
     *  <code>float</code> if the Arity is Array.
     */
    public static final PropertyType FLOAT = new PropertyType ("Float");
    /**
     *  Property type for an <code>Integer</code> object, or an
     *  <code>integer</code> if the Arity is Array.
     */
    public static final PropertyType INTEGER = new PropertyType ("Integer");
    /**
     *  Property type for a <code>Long</code> object, or a
     *  <code>long</code> if the Arity is Array.
     */
    public static final PropertyType LONG = new PropertyType ("Long");
    /**
     *  Property type for an <code>Object</code>.
     */
    public static final PropertyType OBJECT = new PropertyType ("Object");
    /**
     *  Property type for an <code>AESAudioMetadata</code>.
     */
    public static final PropertyType AESAUDIOMETADATA =
	new PropertyType ("AESAudioMetadata");
    /**
     *  Property type for a <code>NisoImageMetadata</code>.
     */
    public static final PropertyType NISOIMAGEMETADATA =
    new PropertyType ("NISOImageMetadata");
    /**
     *  Property type for a <code>TextMDMetadata</code>.
     */
    public static final PropertyType TEXTMDMETADATA =
    new PropertyType ("TextMDMetadata");
    /**
     *  Property type for a <code>Property</code> object.
     */
    public static final PropertyType PROPERTY = new PropertyType ("Property");
    /**
     *  Property type for a <code>Short</code> object, or a
     *  <code>short</code> if the Arity is Array.
     */
    public static final PropertyType SHORT = new PropertyType ("Short");
    /**
     *  Property type for a <code>String</code> object.
     */
    public static final PropertyType STRING = new PropertyType ("String");
    /**
     *  Property type for a <code>Rational</code> object.
     */
    public static final PropertyType RATIONAL = new PropertyType ("Rational");

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Applications will never create PropertyTypes directly.
     **/
    private PropertyType (String value)
    {
	super (value);
    }
}
