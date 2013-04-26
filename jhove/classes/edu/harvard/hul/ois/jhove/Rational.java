/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates a number which is defined as the ratio
 *  of two 32-bit unsigned integers, in accordance with the TIFF
 *  specification.  
 */
public class Rational
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Numerator of ratio. */
    private long _numerator;
    /** Denominator of ratio. */
    private long _denominator;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/
	
    /**
     *  The arguments to this constructor are long in order to
     *  represent all possible 32-bit unsigned integers.  Parameters
     *  greater than 2 ^ 32 - 1 are not meaningful. 
     *  @param numerator     numerator of the Rational value
     *  @param denominator   denominator of the Rational value
     */
    public Rational (long numerator, long denominator)
    {
	_numerator = numerator;
	_denominator = denominator;
    }
    
    /**
     *  The arguments to the int constructor are treated as
     *  32-bit unsigned integers.   
     *  @param numerator     numerator of the Rational value
     *  @param denominator   denominator of the Rational value
     */
    public Rational (int numerator, int denominator)
    {
	_numerator = (long) numerator & 0XFFFFFFFF;
	_denominator = (long) denominator & 0XFFFFFFFF;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/
	
    /**
     *  Returns the Numerator property.
     */
    public long getNumerator ()
    {
	return _numerator;
    }
	
    /**
     *  Returns the Denominator property.
     */
    public long getDenominator()
    {
	return _denominator;
    }

    /**
     *  Converts to a floating-point value (numerator/denominator).
     *  May throw an ArithmeticException.
     **/
    public double toDouble ()
    {
	return ((double) _numerator / (double) _denominator);
    }

    /**
     *  Converts to a long value (numerator/denominator).
     *  May throw an ArithmeticException.
     **/
    public long toLong ()
    {
	return (long) ((double) _numerator / (double) _denominator);
    }

    /**
     *	Represents the Rational as a String in the form of 
     *  "numerator/denominator".
     */	
    public String toString ()
    {
	return Long.toString (_numerator) + "/" +
	       Long.toString (_denominator);
    }
}
