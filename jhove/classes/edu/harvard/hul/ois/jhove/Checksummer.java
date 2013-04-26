/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2006 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;
import java.security.*;
import java.util.zip.*;

/**
 *  The Checksummer class encapsulates the calculation of the 
 *  CRC32, MD5, and SHA-1 checksums. 
 */
public class Checksummer implements java.util.zip.Checksum
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Byte count. */
    protected long _nByte;
    /** CRC32 object. */
    private CRC32 _crc32;
    /** MD5 message digest. */
    private MessageDigest _md5;
    /** SHA-1 message digest. */
    private MessageDigest _sha1;

    /**
     *  Creates a Checksummer, with instances of each of 
     *  CRC32, MD5 MessageDigest, and SHA-1 MessageDigest.
     *  If one or both of the MessageDigests aren't supported
     *  on the current platform, they are left as null.
     *
     *  @see CRC32
     *  @see MessageDigest
     */
    public Checksummer ()
    {
	reset ();
    }
    
    /** Resets all checksums and the byte count to their
     *  initial values.
     */
    public void reset ()
    {
        _nByte = 0;
        _crc32 = new CRC32 ();
        try {
            _md5  = MessageDigest.getInstance ("MD5");
            _sha1 = MessageDigest.getInstance ("SHA-1");
        }
        catch (NoSuchAlgorithmException e) {
        }
    }
    
    /** getValue is required by the Checksum interface, but
     *  we can return only one of the three values.  We 
     *  return the CRC32 value, since that's the one which
     *  is guaranteed to be available.
     */
    public long getValue ()
    {
        return _crc32.getValue ();
    }
    
    /**
     *  Updates the checksum with the argument.
     *  Called when a signed byte is available.
     */
    public void update (byte b)
    {
	_crc32.update (b);
	if (_md5 != null) {
	    _md5.update (b);
	}
	if (_sha1 != null) {
       	    _sha1.update (b);
	}
    }

    /**
     *  Updates the checksum with the argument.
     *  Called when an unsigned byte is available.
     */
    public void update (int b)
    {
	byte sb;
	if (b > 127) {
	    sb = (byte) (b - 256);
	}
	else {
	    sb = (byte) b;
	}
	update (sb);
    }
    
    /**
     *  Updates the checksum with the argument.
     *  Called when a byte array is available.
     */
    public void update (byte[] b)
    {
	_crc32.update (b);
	if (_md5 != null) {
	    _md5.update (b);
	}
	if (_sha1 != null) {
	    _sha1.update (b);
	}
    }
    
    /**
     *  Updates the checksum with the argument.
     *  Called when a byte array is available.
     */
    public void update (byte[] b, int off, int len)
    {
	_crc32.update (b, off, len);
	if (_md5 != null) {
	    _md5.update (b, off, len);
	}
	if (_sha1 != null) {
	    _sha1.update (b, off, len);
	}
    }

    /**
     *  Returns the value of the CRC32 as a hex string.
     */
    public String getCRC32 ()
    {
	return padLeadingZeroes 
            (Long.toHexString (_crc32.getValue ()), 8);
    }

    /**
     *  Returns the value of the MD5 digest as a hex string.
     *  Returns null if the digest is not available.
     */
    public String getMD5 ()
    {
	String value = null;

	if (_md5 != null) {
	    StringBuffer buffer = new StringBuffer ();
	    byte [] digest = _md5.digest ();
	    for (int i=0; i<digest.length; i++) {
		int un = (digest[i] >= 0) ? digest[i] : 256+digest[i];
                buffer.append (padLeadingZeroes 
                                (Integer.toHexString (un), 2));
	    }
	    value = buffer.toString ();
	}

	return value;
    }

    /**
     *  Returns the value of the SHA-1 digest as a hex string.
     *  Returns null if the digest is not available.
     */
    public String getSHA1 ()
    {
	String value = null;

	if (_sha1 != null) {
	    StringBuffer buffer = new StringBuffer ();
	    byte [] digest = _sha1.digest ();
	    for (int i=0; i<digest.length; i++) {
		int un = (digest[i] >= 0) ? digest[i] : 256+digest[i];
		buffer.append (padLeadingZeroes 
                                (Integer.toHexString (un), 2));
	    }
	    value = buffer.toString ();
	}

	return value;
    }
    
    /** Pad a hexadecimal (or other numeric) string out to
     *  the specified length with leading zeroes. */
    private String padLeadingZeroes (String str, int len)
    {
        // This is optimized for adding just one leading zero
        // or none, which will be the usual case.
        while (str.length () < len) {
            str = "0" + str;
        }
        return str;
    }
}
