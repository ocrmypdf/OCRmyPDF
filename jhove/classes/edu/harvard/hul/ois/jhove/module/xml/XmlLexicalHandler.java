/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.xml;

import java.util.*;
import org.xml.sax.SAXException;
import org.xml.sax.ext.LexicalHandler;

/**
 * 
 * This implementation of LexicalHandler takes care of
 * comments, DTD's, entities and other stuff for XmlModule.
 * The caller has to make sure the LexicalHandler property
 * is supported by the SAX implementation, and set that
 * property to this class.
 * 
 * @author Gary McGath
 *
 */
public class XmlLexicalHandler implements LexicalHandler {

    private List<String> _comments;
    private Set<String> _entityNames;
    public XmlLexicalHandler ()
    {
        _comments = new LinkedList<String> ();
        _entityNames = new HashSet<String> ();
    }
    
    
    
    /**
     * Report the end of a CDATA section.
     * Does nothing.
     * @see org.xml.sax.ext.LexicalHandler#endCDATA()
     */
    public void endCDATA() throws SAXException {
        // no action necessary
    }

    /**
     * Report the end of DTD declarations.
     * Does nothing.
     * @see org.xml.sax.ext.LexicalHandler#endDTD()
     */
    public void endDTD() throws SAXException {

    }

    /** 
     * Report the start of a CDATA section.
     * Does nothing.
     * @see org.xml.sax.ext.LexicalHandler#startCDATA()
     */
    public void startCDATA() throws SAXException {
        // no action necessary
    }

    /**
     * Gathers comments into the comments list.
     * 
     * @see org.xml.sax.ext.LexicalHandler#comment(char[], int, int)
     */
    public void comment(char[] text, int start, int length) throws SAXException {
        _comments.add (String.copyValueOf (text, start, length));
    }

    /**
     * Accumulates entity names into the entity set.  This will be
     * used for determining which entities are actually used.
     * 
     * @see org.xml.sax.ext.LexicalHandler#startEntity(java.lang.String)
     */
    public void startEntity(String name) throws SAXException 
    {
        _entityNames.add (name);
    }

    /**
     * Report the end of an entity.
     * Does nothing.
     * 
     * @see org.xml.sax.ext.LexicalHandler#endEntity(java.lang.String)
     */
    public void endEntity(String name) throws SAXException 
    {
        // No action necessary
    }


    /**
     * Report the start of DTD declarations, if any.
     * Does nothing.
     * @see org.xml.sax.ext.LexicalHandler#startDTD(java.lang.String, java.lang.String, java.lang.String)
     */
    public void startDTD(String arg0, String arg1, String arg2)
        throws SAXException 
    {

    }


    /**
     *  Returns the value of the comments list, which is
     *  a List of Strings.
     */
    public List<String> getComments () 
    {
        return _comments;
    }
    
    
    /**
     *  Returns the Set of entity names.
     */
    public Set<String> getEntityNames ()
    {
        return _entityNames;
    }
}
