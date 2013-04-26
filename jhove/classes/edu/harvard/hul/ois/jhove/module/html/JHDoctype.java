/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * Representation of a parsed HTML DOCTYPE.
 * 
 * @author Gary McGath
 *
 */
public class JHDoctype extends JHElement {

    /** List of tokens in the DOCTYPE. */
    public List _doctypeElements;

    /** Constructor. */
    public JHDoctype (List elements, List dtElements) {
        super (elements);
        _doctypeElements = dtElements;
    }
    
    /** Returns the doctype token list. */
    public List getDoctypeElements ()
    {
        return _doctypeElements;
    }
}
