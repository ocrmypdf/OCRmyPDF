/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated types for a Checksum on a content
 *  stream or file. 
 *  Applications will not create or modify ChecksumTypes, but will
 *  use one of the predefined ChecksumType instances 
 *  CRC32, MD5, or SHA1.
 *
 *  @see Checksum
 */
public final class ChecksumType
    extends EnumerationType
{
    /** 32-bit Cyclical Redundancy Checksum. */
    public static final ChecksumType CRC32 = new ChecksumType ("CRC32");

    /** 128-bit Message Digest 5. */
    public static final ChecksumType MD5 = new ChecksumType ("MD5");

    /** 160-bit Secure Hash Algorithm. */
    public static final ChecksumType SHA1 = new ChecksumType ("SHA-1");

    /** 
     *  Applications will never create ChecksumTypes directly.
     **/
    private ChecksumType (String value)
    {
	super (value);
    }
}
