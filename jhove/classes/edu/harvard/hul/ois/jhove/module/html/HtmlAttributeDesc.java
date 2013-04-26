/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

//import java.util.*;

/**
 * Class representing an abstract attribute of an HTML element.
 *
 * @author Gary McGath
 *
 */
public class HtmlAttributeDesc {
    
    /** Permitted values for _kind */
    public final static int 
        REQUIRED = 1,   // #REQUIRED
        CURRENT = 2,    // #CURRENT
        CONREF = 3,     // #CONREF
        IMPLIED = 4,    // #IMPLIED
        OTHER = 5;      // Explicit default
        
    private String _name;
    private int _kind;
    private String[] _permittedValues;
    
    
    /**
     *  Constructor.
     * 
     *  @param  name              The name of the attribute.  Must be lower case.
     *  @param  permittedValues   Specific values allowed for the parameter.  If
     *                            null, then any CDATA value is allowed.
     *  @param   kind             The kind of parameter.  Must be REQUIRED, CURRENT,
     *                            CONREF, or IMPLIED.
     */
    public HtmlAttributeDesc (String name,
            String[] permittedValues,
            int kind)
    {
        _name = name;
        _permittedValues = permittedValues;
        _kind = kind;
    }
    
    /**
     *  Constructor for an attribute that can take any value, with
     *  kind defaulting to IMPLIED. */
    public HtmlAttributeDesc (String name)
    {
        _name = name;
        _permittedValues = null;
        _kind = IMPLIED;
    }
    
    /**
     *  Returns the attribute's name.
     */
    public String getName ()
    {
        return _name;
    }
    
    
    /** Returns <code>true</code> if this tag's name 
     *  matches the parameter. */
    public boolean nameMatches(String name)
    {
        return _name.equals (name);
    }
    
    
    /** Returns <code>true</code> if the parameter is a permissible 
     *  value for the attribute.
     */
    public boolean valueOK (String name, String value) 
    {
        if (_permittedValues == null) {
            return true;
        }
        else if (value == null) {
            // An attribute without a value is permitted only when
            // there is only one legal value, and that equals the 
            // attribute's name.
            if (_permittedValues.length == 1 &&
                _permittedValues[0].equals (name)) {
                    return true;
                }
            else {
                return false;
            }
        }
        else {
            value = value.toLowerCase ();
            for (int i = 0; i < _permittedValues.length; i++) {
                if (_permittedValues[i].equals (value)) {
                    return true;
                }
            }
            return false;   // No match
        }
    }
    
    /** Return <code>true</code> if the attribute is required. */
    public boolean isRequired ()
    {
        return _kind == REQUIRED;
    }
}
