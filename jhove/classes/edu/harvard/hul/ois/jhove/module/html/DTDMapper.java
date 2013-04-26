/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.io.InputStream;
import java.net.URL;
import org.xml.sax.InputSource;


/**
 * Class to map public DTD ID's to files which are included with this
 * HTML module.  This class is used by the XML module, due to the
 * intermodulary nature of XHTML.
 * 
 * @author Gary McGath
 *
 */
public class DTDMapper {

    private final static String xhtml1Frameset = "-//W3C//DTD XHTML 1.0 FRAMESET//EN";
    private final static String xhtml1Strict = "-//W3C//DTD XHTML 1.0 STRICT//EN";
    private final static String xhtml1Transitional = "-//W3C//DTD XHTML 1.0 TRANSITIONAL//EN";
    private final static String xhtml11 = "-//W3C//DTD XHTML 1.1//EN";
    private final static String latin1Ent = "-//W3C//ENTITIES LATIN 1 FOR XHTML//EN";
    private final static String specialEnt = "-//W3C//ENTITIES SPECIAL FOR XHTML//EN";
    private final static String symbolEnt = "-//W3C//ENTITIES SYMBOLS FOR XHTML//EN";
    
    /** Attempts to convert a public ID to a matching DTD or Entity resource.
     *  Returns an InputStream for that resource if there is a match.  
     *  Otherwise returns <code>null</code>.
     * 
     *  @param publicID   The PUBLIC ID associated with a DTD or entity document
     */
    public static InputSource publicIDToFile(String publicID)
    {
        String filename = null;
        if (publicID == null) {
            return null;
        }
        // Make comparisons case-insensitive -- just in case
        publicID = publicID.toUpperCase ();
        if (xhtml1Frameset.equals (publicID)) {
            filename = "xhtml1-frameset.dtd";
        }
        else if (xhtml1Strict.equals (publicID)) {
            filename = "xhtml1-strict.dtd"; 
        }
        else if (xhtml1Transitional.equals (publicID)) {
            filename = "xhtml1-transitional.dtd";
        }
        else if (xhtml11.equals (publicID)) {
            filename = "xhtml11-flat.dtd";
        }
        else if (latin1Ent.equals (publicID)) {
            filename = "xhtml-lat1.ent";
        }
        else if (specialEnt.equals (publicID)) {
            filename = "xhtml-special.ent";
        }
        else if (symbolEnt.equals (publicID)) {
            filename = "xhtml-symbol.ent";
        }
        if (filename != null) {
            URL dtdURL = DTDMapper.class.getResource(filename);
            if (dtdURL != null) {
                try {
                    InputStream strm = dtdURL.openStream();
                    return new InputSource (strm);
                }
                catch (Exception e) {
                    return null;
                }
            }
        }
        return null;
    }
    
    
    /** Returns TRUE if the parameter is the public ID of a
     *  known XHTML DTD. */
    public static boolean isXHTMLDTD (String publicID) 
    {
        if (publicID == null) {
            return false;
        }
        publicID = publicID.toUpperCase ();
        return (xhtml1Frameset.equals (publicID) ||
                xhtml1Strict.equals (publicID) ||
                xhtml1Transitional.equals (publicID) ||
                xhtml11.equals (publicID));
    }
    
    /** Returns the XHTML version associated with the DTD's 
     *  public ID.  Returns <code>null</code> if it isn't
     *  a known XHTML public ID. */
    public static String getXHTMLVersion (String publicID) {
        publicID = publicID.toUpperCase ();
        if (!isXHTMLDTD (publicID)) {
            return null;
        }
        else if (xhtml11.equals (publicID)) {
            return "1.1";
        }
        else {
            return "1.0";
        }
    }
}
