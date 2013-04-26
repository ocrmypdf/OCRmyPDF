/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

/**
 * Class for defining special items in HTML element and attribute
 * definitions.  This class is never instantiated except by the
 * static elements it defines.
 *
 * @author Gary McGath
 *
 */
public class HtmlSpecialToken {

    String _name;
    
    /** Private constructor.  This class may not be instantiated. */
    private HtmlSpecialToken () {}
    
    private HtmlSpecialToken (String name) 
    {
        _name = name;
    }
    
    //public static HtmlSpecialToken EMPTY = new HtmlSpecialToken ("EMPTY");
    /** The PCDATA token. Signifies that PCDATA is permitted in the content
     *  of an element. */
    public static HtmlSpecialToken PCDATA = new HtmlSpecialToken ("PCDATA");
}
