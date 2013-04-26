/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.util.*;

/**
 *  This class encapsulates arbitrary format-specific properties.
 *  A Property's value can be a simple object or a structure.
 *  If it is a simple object, it has arity SCALAR.  If it is
 *  a structure, its must be a Map, a List, a Set, or an array,
 *  with corresponding Arity.  The simple object (in the case of
 *  arity SCALAR) or the components of the structure must have a
 *  type corresponding to one of the enumerations given by
 *  <code>PropertyType</code>.
 *
 *  The components of a Property may themselves be Property 
 *  objects, allowing nested structures.
 *
 *  @see PropertyType
 *  @see PropertyArity
 */
public class Property
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    private String _name;
    private PropertyType _type;
    private PropertyArity _arity;
    private Object _value;


    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

	/**
	 *  Creates a Property with arity SCALAR.
	 *
	 *  @param   name   The displayable name of the property
	 *  @param   type   The type of property
	 *  @param   value  The value of the property.  The type of the
	 *                  parameter must agree with <code>type</code>.
	 */
    public Property (String name, PropertyType type, Object value)
    {
	init (name, type, PropertyArity.SCALAR, value);
    }

	/**
	 *  Creates a Property with a given name, type, arity and value.
	 *
	 *  @param   name   The displayable name of the property.
	 *  @param   type   The type of property.
	 *  @param   arity  The arity of the property.
	 *  @param   value  The value of the property.  If the arity is
	 *		SCALAR, the type of this parameter must agree
	 *		with <code>type</code>.  Otherwise, the arity
	 *              must agree with <code>arity</code>, and its
	 *              components must agree with <code>type</code>.
	 */
    public Property (String name, PropertyType type, PropertyArity arity,
		     Object value)
    {
	init (name, type, arity, value);
    }

    private void init (String name, PropertyType type, PropertyArity arity,
		       Object value)
    {
	/* Some limited type checking. Checking for mismatched
           types here may help avoid difficult chasing down
           of the bugs such mismatches cause. */
	if (value == null) {
	    throw new NullPointerException ("Null value for Property not permitted");
	}
	if (arity == PropertyArity.SCALAR) {
	    if (value instanceof List ||
		    value instanceof Map ||
		    value instanceof Set) {
		throw new IncompatibleClassChangeError
			("Wrong class for Scalar Property");
	    }
	}
	else if (arity == PropertyArity.MAP) {
	    if (!(value instanceof Map)) {
		throw new IncompatibleClassChangeError
			("Wrong class for Map Property");
	    }

	}
	else if (arity == PropertyArity.SET) {
	    if (!(value instanceof Set)) {
		throw new IncompatibleClassChangeError
			("Wrong class for Set Property");
	    }

	}
	else if (arity == PropertyArity.LIST) {
	    if (!(value instanceof List)) {
		throw new IncompatibleClassChangeError
			("Wrong class for List Property");
	    }

	}

	_name  = name;
	_type  = type;
	_arity = arity;
	_value = value;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Accessor methods.
     ******************************************************************/

	/**
	 *   Returns the arity (type of structure) of this Property.
	 */
    public PropertyArity getArity ()
    {
	return _arity;
    }

    /**
     * Return a property by its name, regardless of its position in the
     * structural hierarchy of properties.
     * @param name Property name
     * @return Named property (or null)
     */
    public Property getByName (String name)
    {
	if (_name.equals (name)) {
	    return this;
	}

	if (!_arity.equals (PropertyArity.SCALAR) &&
	    _type.equals (PropertyType.PROPERTY)) {
	    if (_arity.equals (PropertyArity.ARRAY)) {
		Property [] array = (Property []) _value;
		for (int i=0; i<array.length; i++) {
		    Property prop = array[i].getByName (name);
		    if (prop != null) {
			return prop;
		    }
		}
	    }
	    else if (_arity.equals (PropertyArity.LIST)) {
		List list = (List) _value;
		int len = list.size ();
		for (int i=0; i<len; i++) {
		    Property prop = ((Property) list.get (i)).getByName (name);
		    if (prop != null) {
			return prop;
		    }
		}
	    }
	    else if (_arity.equals (PropertyArity.MAP)) {
		Collection coll = ((Map) _value).values ();
		Iterator iter = coll.iterator ();
		while (iter.hasNext ()) {
		    Property prop = ((Property) iter.next ()).getByName (name);
		    if (prop != null) {
			return prop;
		    }
		}
	    }
	    else if (_arity.equals (PropertyArity.SET)) {
		Iterator iter = ((Set) _value).iterator ();
		while (iter.hasNext ()) {
		    Property prop = ((Property) iter.next ()).getByName (name);
		    if (prop != null) {
			return prop;
		    }
		}
	    }
	}

	return null;
    }

	/**
	 *   Returns the displayable name of this Property.
	 */
    public String getName ()
    {
	return _name;
    }

	/**
	 *  Returns the type of this Property.
	 *  If the arity is other than SCALAR, the type refers to the
	 *  compononents of the Property structure.
	 */
    public PropertyType getType ()
    {
	return _type;
    }

	/**
	 *  Returns the Object which is the Property's value.
	 */
    public Object getValue ()
    {
	return _value;
    }
}
