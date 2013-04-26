/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class encapsulates the result of calculations which provide a greater
 *  or lesser degree of confirmation of the integrity of a digital
 *  object's content, including checksums, CRC's, message digests,
 *  etc.
 *
 *  @see ChecksumType
 *  @see Checksummer
 */
public class Checksum
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    private ChecksumType _type;
    private String _value;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a Checksum with a given value and type
     */
    public Checksum (String value, ChecksumType type)
    {
	_value = value;
	_type  = type;
    }


    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Accessor methods.
     ******************************************************************/

    /** 
     *  Returns this Checksum's type
     */
    public ChecksumType getType ()
    {
	return _type;
    }

    /** 
     *  Returns this Checksum's value
     */
    public String getValue ()
    {
	return _value;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /**
     *  Sets the type of this Checksum
     */
    public void setType (ChecksumType type)
    {
	_type = type;
    }

    /**
     *  Sets the value of this Checksum
     */
    public void setValue (String value)
    {
	_value = value;
    }

    /******************************************************************
     *  Put here as a convenience for checksum calculators
     *****************************************************************/
    /**
     * Maps unsigned byte value (0 to 256) to signed byte value (-128 to 127).
     */
    public static byte unsignedByteToByte (int value)
    {
	return (byte) ((value < 127) ? value : value - 256);
    }
}
