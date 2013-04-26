/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class represents the arity (structure type) of a Property.
 *  Applications will not create or modify PropertyArities, but will
 *  use one of the predefined PropertyArity instances 
 *  ARRAY, LIST, MAP, SCALAR, or SET.
 *
 *   @see Property
 */
public final class PropertyArity
    extends EnumerationType
{
	/**
	 *  An Arity corresponding to a Java array.  For the Java types
	 *  <code>Integer</code>, <code>Boolean</code>, <code>Byte</code>, 
	 *  <code>Character</code>, <code>Double</code>, 
	 *  <code>Float</code>, <code>Long</code>, and
	 *  <code>Short</code>, a Property with arity ARRAY is an array of primitive
	 *  Java types rather than Objects (e.g., <code>int</code> 
	 *  rather than <code>Integer</code>).
	 */
    public static final PropertyArity ARRAY = new PropertyArity ("Array");
    
    /**
     *  An Arity corresponding to java.util.List or any of its derived classes.
     */
    public static final PropertyArity LIST = new PropertyArity ("List");

    /**
     *  An Arity corresponding to java.util.Map or any of its derived classes.
     */
    public static final PropertyArity MAP = new PropertyArity ("Map");

    /**
     *  An Arity corresponding to a simple object, which must be of a
     *  type corresponding to one of the instances of 
     *  <code>PropertyType</code>.
     */
    public static final PropertyArity SCALAR = new PropertyArity ("Scalar");

    /**
     *  An Arity corresponding to java.util.Set or any of its derived classes.
     */
    public static final PropertyArity SET = new PropertyArity ("Set");

    /** 
     *  Applications will never create PropertyArities directly.
     **/
    private PropertyArity (String value)
    {
	super (value);
    }
}
