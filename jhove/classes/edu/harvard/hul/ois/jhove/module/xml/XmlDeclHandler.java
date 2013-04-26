/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.xml;

import java.util.*;
import org.xml.sax.SAXException;
import org.xml.sax.ext.DeclHandler;

/**
 * 
 * This implementation of DeclHandler takes care of
 * collecting entity declarations.
 * 
 * @author Gary McGath
 *
 */
public class XmlDeclHandler implements DeclHandler {

    private List<String[]> _intEntityDeclarations;
    private List<String[]> _extEntityDeclarations;
    
    public XmlDeclHandler ()
    {
        _intEntityDeclarations = new LinkedList<String[]> ();
        _extEntityDeclarations = new LinkedList<String[]> ();
    }
    
    
    
    /**
     * Report an element type declaration.
     * Does nothing.
     * @see org.xml.sax.ext.DeclHandler#elementDecl(java.lang.String, java.lang.String)
     */
    public void elementDecl(String arg0, String arg1) throws SAXException 
    {
    }

    /**
     *  Adds internal entity declarations to the entity declarations
     *  list in the form of a String[2], with element 0 being the
     *  name and element 1 being the value. 
     */
    public void internalEntityDecl(String name, String value)
        throws SAXException {
        String[] decl = new String[2];
        decl[0] = name;
        decl[1] = value;
        _intEntityDeclarations.add (decl);
    }

    /**
     *  Adds external entity declarations to the entity declarations
     *  list in the form of a String[3], with element 0 being the
     *  name, element 1 the public ID, and 2 the system ID. 
     */
    public void externalEntityDecl(String name, String publicID, String systemID)
        throws SAXException {
        String[] decl = new String[3];
        decl[0] = name;
        decl[1] = publicID;
        decl[2] = systemID;
        _extEntityDeclarations.add (decl);
    }

    /** Report an attribute type declaration.
     *  Does nothing.
     *  @see org.xml.sax.ext.DeclHandler#attributeDecl(java.lang.String, java.lang.String, java.lang.String, java.lang.String, java.lang.String)
     */
    public void attributeDecl(
        String arg0,
        String arg1,
        String arg2,
        String arg3,
        String arg4)
        throws SAXException 
    {
 
    }


    /**
     *  Returns list of entity declarations.  Each list
     *  is an array String[2], giving the name and
     *  value respectively.
     */
    public List<String[]> getInternalEntityDeclarations ()
    {
        return _intEntityDeclarations;
    }


    /**
     *  Returns list of entity declarations.  Each list
     *  is an array String[3], giving the name,
     *  public ID, and system ID respectively.
     */
    public List<String[]> getExternalEntityDeclarations ()
    {
        return _extEntityDeclarations;
    }
}
