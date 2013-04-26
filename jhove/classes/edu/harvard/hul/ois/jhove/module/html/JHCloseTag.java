/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * Representation of a parsed HTML close tag.
 * 
 * @author Gary McGath
 *
 */
public class JHCloseTag extends JHElement {
    public String _name;

    /** Constructor. 
     * 
     *  @param   elements     The list of parsed elements, to which
     *                        this gets added.  
     *  @param   name         The name of the tag
     *  @param   line         Line number, for information reporting
     *  @param   column       Line number, for information reporting
     */
    public JHCloseTag (List elements, String name, int line, int column) {
        super (elements);
        _name = name.toLowerCase ();
        _line = line;
        _column = column;
    }

    /** Returns the tag's name. */
    public String getName ()
    {
        return _name;
    }
}
