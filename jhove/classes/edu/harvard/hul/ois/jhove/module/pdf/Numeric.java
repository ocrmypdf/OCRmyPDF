/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  Class for Tokens which represent PDF numbers.  Numeric values
 *  are stored as <code>double</code> if they have a real value, or
 *  as int if they have an integer value.  The implementation notes
 *  state that the maximum value of an integer on a 32-bit machine
 *  is 2 ^ 31 - 1.  However, they also say that byte offsets have
 *  a limit of 10 decimal digits, which is a larger value.  So we
 *  store integer values as long.
 */
public class Numeric
    extends Token
{
    /** True if real value; false if integer. */
    private boolean _real;
    private double _realValue;
    private long _intValue; 

    /** Creates an instance of a Numeric */
    public Numeric ()
    {
        super ();
        _real = false;
        _intValue = 0;
    }

    /** Returns the value, converted to an integer */
    public int getIntegerValue ()
    {
        if (_real) {
            return (int) _realValue;
        }
        else {
            return (int) _intValue;
        }
    }

    /** Returns the value, converted to a long */
    public long getLongValue ()
    {
        if (_real) {
            return (long) _realValue;
        }
        else {
            return _intValue;
        }
    }

    /** Returns the value of this Numeric as a double */
    public double getValue ()
    {
        if (_real) {
            return _realValue;
        }
        else {
            return (double) _intValue;
        }
    }

    /** 
     *  Returns true if the value is stored as a floating-point
     *  number.
     */
    public boolean isReal ()
    {
        return _real;
    }

    /** 
     *  Set this object's value to a double.
     */
    public void setValue (double value)
    {
        _realValue = value;
        _real = true;
    }


    /** 
     *  Set this object's value to a long.
     */
    public void setValue (long value)
    {
        _intValue = value;
        _real = false;
    }
    
    /** Returns true if this is within PDF/A implementation limits. */
    public boolean isPdfACompliant () {
        if (_real) {
            double absRealValue = (_realValue < 0 ? -_realValue : _realValue);
            return (absRealValue <= 3.404E38);
        }
        else {
            return (_intValue <= 2147483647 && _intValue >= -2147483648);
        }
            
    }

}

