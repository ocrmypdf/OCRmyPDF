/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * Representation of a parsed HTML comment.
 *
 * @author Gary McGath
 *
 */
public class JHComment extends JHElement {

    /** Constructor.
     *  Just adds the comment to the element list. */
    public JHComment (List elements, String text) {
        super (elements);
    }

}
