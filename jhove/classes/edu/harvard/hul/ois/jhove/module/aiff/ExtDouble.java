/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

/**
 * Code to deal with the 80-bit floating point (extended double)
 * numbers which occur in AIFF files.  Should also be applicable
 * in general.
 * 
 * Java has no built-in support for IEEE 754 extended double numbers.
 * Thus, we have to unpack the number and convert it to a double by
 * hand.  There is, of course, loss of precision.
 * 
 * This isn't designed for high-precision work; as the standard
 * disclaimer says, don't use it for life support systems or nuclear
 * power plants.
 *
 * @author Gary McGath
 *
 */
public class ExtDouble {

    byte[] _rawData;
    
    /**
     *  Constructor.  
     * 
     *  @param   rawData A 10-byte array representing the number
     *                   in the sequence in which it was stored.
     */
    public ExtDouble(byte[] rawData) 
    {
        _rawData = rawData;
    }


    /**  Convert the value to a Java double.  This results in
     *   loss of precision.  If the number is out of range,
     *   results aren't guaranteed.
     */
    public double toDouble ()
    {
        int sign;
        int exponent;
        long mantissa = 0;
        
        // Extract the sign bit.
        sign = _rawData[0] >> 7;
        
        // Extract the exponent.  It's stored with a
        // bias of 16383, so subtract that off.
        // Also, the mantissa is between 1 and 2 (i.e.,
        // all but 1 digits are to the right of the binary point, so
        // we take 62 (not 63: see below) off the exponent for that.
        exponent = (_rawData[0] << 8) | _rawData[1];
        exponent &= 0X7FFF;          // strip off sign bit
        exponent -= (16383 + 62);    // 1 is added to the "real" exponent
        
        // Extract the mantissa.  It's 64 bits of unsigned
        // data, but a long is a signed number, so we have to
        // discard the LSB.  We'll lose more than that converting
        // to double anyway.  This division by 2 is the reason for
        // adding an extra 1 to the exponent above.
        int shifter = 55;
        for (int i = 2; i < 9; i++) {
            mantissa |= ((long) _rawData[i] & 0XFFL) << shifter;
            shifter -= 8;
        }
        mantissa |= _rawData[9] >>> 1;
        
        // Now put it together in a floating point number.
        double val = Math.pow (2, exponent);
        val *= mantissa;
        if (sign != 0) {
            val = -val;
        }
        return val;
    }
}
