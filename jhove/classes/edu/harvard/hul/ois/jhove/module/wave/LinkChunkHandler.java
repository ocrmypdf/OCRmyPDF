/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.util.*;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;

/**
 * 
 * This handler parses the data of a WAVE List chunk.
 * 
 * @author Gary McGath
 *
 */
public class LinkChunkHandler extends DefaultHandler {

    private StringBuffer _content;
    private int state;
    private List fileNames;
    private String id;
    
    private final static int STATE_DEFAULT = 0,
        STATE_FILE = 1, 
        STATE_ID = 2;
 
    public LinkChunkHandler ()
    {
        state = STATE_DEFAULT;
        _content = new StringBuffer ();
        fileNames = new LinkedList ();
        id = null;
    }


    /** Accessor for getting file name list.  The value returned
     *  is meaningful only after parsing. The value returned is
     *  guaranteed not to be null, but may be empty. */
    public List getFileNames ()
    {
        return fileNames;
    }
    
    
    /** Accessor for getting the ID element.  The value returned
     *  may be null, as the ID element is optional. */
    public String getID ()
    {
        return id;
    }



    /**
     *  Looks for the first element encountered.  Stores
     *  its name as the value to be returned by getRoot,
     *  qualified name by preference, local name if the
     *  qualified name isn't available.
     */
    public void startElement (String namespaceURI,
                String localName,
                String qualifiedName,
                Attributes atts) throws SAXException
    {
        if ("FILE".equals (qualifiedName)) {
            state = STATE_FILE;
        }
        else if ("ID".equals (qualifiedName)) {
            state = STATE_ID;
        }
    }


    /** 
     *  SAX parser callback method for PC text.
     */
    public void characters (char [] ch, int start, int length)
    throws SAXException
    {
        _content.append (ch, start, length);
    }


    /** 
     *  SAX parser callback method.
     */
    public void endElement (String namespaceURI, String localName,
                String rawName)
    throws SAXException
    {
        switch (state) {
            case STATE_FILE:
                fileNames.add (_content.toString ());
                break;
            case STATE_ID:
                id = _content.toString ();
                break;
            case STATE_DEFAULT:
            default:
                break;
        }
        state = STATE_DEFAULT;
        _content.setLength (0);
    }

}
