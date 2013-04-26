/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

/**
 * Subclass of HtmlTagDesc for temporary tags.  This doesn't add
 * any functionality to the superclass, but serves as a marker class.
 *
 * @author Gary McGath
 *
 */
public class HtmlTempTagDesc extends HtmlTagDesc {

    /** 
     *  Constructor.
     * 
     *  @param  name     Tag name
     */
    public HtmlTempTagDesc (String name)
    {
        super (name, false, false, null, null);
        // To minimize excessive error messages, assume unlimited
        // tags can be nested.
        _sequence = new int[1];
        _sequence[0] = SEQ0_MANY;
    }

    /** Reports whether this is a temporary tag descriptor.
     *  Returns <code>true</code>.
     */
    public boolean isTemp ()
    {
        return true;
    }

    /** Reports whether this element allows a given tag name
     *  in its content, at the specified index.  Since we know nothing
     *  about this element, no meaningful answer is possible.  Return
     *  <code>true</code> just to minimize the number of extra error
     *  messages.
     */
    protected boolean allowsTag (String tag, int index, HtmlDocDesc doc)
    {
        return true;
    }
}
