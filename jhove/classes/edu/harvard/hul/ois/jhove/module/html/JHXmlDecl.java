/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.List;

/**
 * Representation of an XML declaration.  This class allows
 * XHTML files to be examined without choking.  The actual
 * work is done by the XML module, but first we have to determine
 * that it is XHTML.
 *
 * @author Gary McGath
 *
 */
public class JHXmlDecl extends JHElement {

    /** Constructor.  We don't really care about the content; this is
     *  just a placeholder.  So it has a minimal constructor.
     * 
     *  @param   elements     The list of parsed elements, to which
     *                        this gets added.
     */
    public JHXmlDecl (List elements)
    {
        super (elements);
    }
}
