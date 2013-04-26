/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.IOException;
import java.io.InputStream;

/**
 * This class serves to provide an InputStream for an XML
 * fragment (e.g., embedded XMP metadata).  
 * 
 * @author Gary McGath
 */
public class XMLWrapperStream extends InputStream 
{
    
    private String xmlDecl;
    private String rootStart;
    private String rootEnd;
    private int strIndex;
    private int state;

    /* Values for state */    
    private final static int DECL = 0,
        ROOT_START = 1,
        CONTENT = 2,
        ROOT_END = 3;

    private InputStream _wrappedStream;

    /**
     *  Constructor.
     *  
     *  @param wrappedStream       The stream which this stream will subsume.
     *  @param rootName            The name of the root element.  May be null 
     *                             if <code>wrappedStream</code> already contains a root element.
     *  @param version             The XML version.  Should be null or "1.0" unless 
     *                             there's a really good reason.
     *  @param encoding            The name of the character encoding. May be null.
     *  @param standalone          The value of the <code>standalone</code> attribute.  May be null.
     */
    public XMLWrapperStream (InputStream wrappedStream, 
            String rootName,
            String version,
            String encoding,
            String standalone) 
    {
        _wrappedStream = wrappedStream;
        xmlDecl = "<?xml version='";
        if (version == null) {
            xmlDecl += "1.0'";   
        }
        else {
            xmlDecl += version + "'";
        }
        if (encoding != null) {
            xmlDecl += " encoding='" + encoding + "' ";   
        }
        if (standalone != null) {
            xmlDecl += " standalone='" + standalone + "' ";
        }
        xmlDecl += "?>";
        state = DECL;
        strIndex = 0;
        
        if (rootName != null) {
            rootStart = "<" + rootName + ">";
            rootEnd = "</" + rootName + ">";
        }
        else {
            rootStart = "";
            rootEnd = "";
        }
    }
    
    /**
     *  Constructor.  Equivalent to 
     *                <code>XMLWrapperStream (wrappedStream, null, null, null, null)</code>
     *  
     *  @param wrappedStream       The stream which this stream will subsume.
     */
    public XMLWrapperStream (InputStream wrappedStream)
    {
        this (wrappedStream, null, null, null, null);
    }

    /**
     *  Constructor.  Equivalent to 
     *                <code>XMLWrapperStream (wrappedStream, rootName, null, null, null)</code>
     *  
     *  @param wrappedStream       The stream which this stream will subsume.
     *  @param rootName            The name of the root element.  May be null.
     */
    public XMLWrapperStream (InputStream wrappedStream, String rootName)
    {
        this (wrappedStream, rootName, null, null, null);
    }
    
    
    /** 
     * Get a byte.  Successive calls will return the
     * XML declaration, then the wrapped stream.
     * 
     * @see java.io.InputStream#read()
     */
    public int read() throws IOException 
    {
        int retval;
        if (state == DECL) { 
            if (strIndex >= xmlDecl.length()) {
                // We have finished the declaration string now.
                state = ROOT_START;
                strIndex = 0;
            }
            else {
                // We haven't finished returning the declaration string.
                return (int) xmlDecl.charAt(strIndex++);
            }
        }
        
        // Each state can fall through to the next
        
        if (state == ROOT_START) {
            if (strIndex >= rootStart.length()) {
                // We have finished the root element start now.
                state = CONTENT;
            }
            else {
            return (int) rootStart.charAt(strIndex++);
            }
        }
             
        if (state == CONTENT) {
            // Metadata alleged stream doesn't look remotely like metadata --
            // probably looking at wrong part of file!
            retval = _wrappedStream.read ();
            if (retval == -1) {
                state = ROOT_END;
                strIndex = 0;
            }
            else {
                return retval;
            }
        }
            
        // Must be ROOT_END if it gets here
        if (strIndex >= rootEnd.length()) {
            // We have finished the root element end and the document now.
            return -1;
        }
        else {
            return (int) rootEnd.charAt(strIndex++);
        }
        
     }

}
