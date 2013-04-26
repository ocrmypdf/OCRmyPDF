/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

/**
 * A description of an attribute within a JHOpenTag.
 * This is not a subclass of JHElement, as it isn't part of
 * the elements list.  It is simply a way to store the information
 * about an attribute in a JHOpenTag.
 *
 * @author Gary McGath
 *
 */
public class JHAttribute {

    private String _name;
    private String _namespace;
    private String _value;
    private int _line;
    private int _column;
    
    /**
     *  Constructor.
     * 
     *  @param    name       Name of the attribute.  Will be forced to
     *                       lower case as it is stored.  Must not be null.
     *  @param    namespace  Namespace for the attribute.  May be null
     *                       if no namespace is specified.
     *  @param    value      Value of the attribute.  May be null.
     *                       If it is in quotes, the quotes will be stripped.
     *  @param    line       Line number at which the attribute begins.
     *  @param    column     Column number at which the attribute begins.
     */
    public JHAttribute (String name, String namespace, String value, 
                        int line, int column)
    {
        _name = name.toLowerCase ();
        _namespace = namespace;
        _line = line;
        _column = column;
        // Clean up value if it's quoted
        if (value != null &&
                value.length () >= 2 && 
                value.charAt (0) == '\"' && 
                value.charAt (value.length() - 1) == '\"') {
            value = value.substring (1, value.length () - 1);
        }
        _value = value;
    }
    
    /** Returns the attribute's name.  This is guaranteed to be
     * in lower case. */
    public String getName ()
    {
        return _name;
    }
    
    /** Returns the namespace of the attribute's name.  May be null. */
    public String getNamespace ()
    {
        return _namespace;
    }

    /** Returns the attribute's value.  May be null.  If not null
     *  and was originally enclosed in double quotes, the return
     *  value has quotes stripped. */
    public String getValue ()
    {
        return _value;
    }

    /** Returns the line number of the beginning of the
     *  attribute definition. */
    public int getLine ()
    {
        return _line;
    }

    /** Returns the column number of the beginning of the
     *  attribute definition. */
    public int getColumn ()
    {
        return _column;
    }
}
