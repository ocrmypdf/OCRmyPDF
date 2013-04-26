/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 * Enumerated data type.  To create an emumeration, define a subclass
 * of EnumerationType with a private constructor, and define as
 * many <code>public final static</code> instances of the subclass,
 * within the subclass definition, as there are enumeration cases.
 * No other instances of an EnumerationType should ever be created,
 * and the only operations which should ever be performed on an
 * EnumerationType are assignment and equality testing.
 * 
 */
public abstract class EnumerationType
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Enumeration value. */
    private String _value;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     * Instantiate an <tt>EnumerationType</tt> object.
     * @param value Enumeration value
     */
    protected EnumerationType (String value)
    {
    _value = value;
    }

    /**
     *  Private no-argument constructor to close off the default
     *  constructor.
     */
    private EnumerationType ()
    {
    }
     
    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     * Type equality test.
     * @param enm Enumerated type
     * @return True, if equal
     */
    public boolean equals (EnumerationType enm)
    {
    return this == enm;
    }

    /**
     * Return enumeration value.
     * @return Value
     */
    public String toString ()
    {
    return _value;
    }
}
