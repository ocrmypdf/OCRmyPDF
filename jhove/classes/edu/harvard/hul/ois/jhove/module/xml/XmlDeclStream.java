/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-4 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.xml;

import java.io.*;
import java.util.*;

/**
 * This class is layered under the InputSource for the XmlModule
 * so that it can detect an XML declaration and character references,
 * which aren't reported by other API's.  
 * 
 * This is called XmlDeclStream for historical reasons, though it's
 * no longer limited to that function.
 * 
 * @author Gary McGath
 */
public class XmlDeclStream extends FilterInputStream {
    private static final int CR = 0x0d; // '\r'
    private static final int LF = 0x0a; // '\n'

    
    private StringBuffer declBuf;
    private StringBuffer refBuf;
    private boolean seenChars;

    private String _version;
    private String _encoding;
    private String _standalone;
    
    /* List of Integers giving character references */
    private List<Integer> _charRefs;

    /* To try to determine line ending */
    protected boolean _lineEndCR;
    protected boolean _lineEndLF;
    protected boolean _lineEndCRLF;
    protected int _prevChar;
    
    public XmlDeclStream (InputStream strm) {
        super (strm);
        declBuf = null;
        seenChars = false;
        _charRefs = new LinkedList<Integer> ();
        
        // No line end types have been discovered.
        _lineEndCR = false;
        _lineEndLF = false;
        _lineEndCRLF = false;
        _prevChar = 0;
    }
    
    /**
     * Reads the next byte of data from this input stream.
     * Processes bytes as it reads them.
     */
    public int read () throws IOException 
    {
        int retval = super.read ();
        if (retval > 0) {
            process (retval);
        }
        return retval;
    }
    
    
    /**
     * Reads up to <code>byte.length</code> bytes of data from this 
     * input stream into an array of bytes.
     * Processes bytes as it reads them.
     */
    public int read (byte[] b) throws IOException 
    {
        int nbytes = super.read (b);
        for (int i = 0; i < nbytes; i++) {
            process ((int) b[i]);
        }
        return nbytes;
    }
    

    /**
     * Reads up to <code>len</code> bytes of data from this 
     * input stream into an array of bytes.
     * Processes bytes as it reads them.
     */
    public int read (byte[] b, int off, int len) throws IOException 
    {
        int nbytes = super.read (b, off, len);
        for (int i = off; i < off + nbytes; i++) {
            process ((int) b[i]);
        }
        
        return nbytes;
    }
    
   
    /**
     *  Returns the character references as a List
     *  of Integers.  No sorting or elimination of
     *  duplicates is done; this is just all the
     *  character references in the order they occurred. 
     */
    public List<Integer> getCharacterReferences ()
    {
        return _charRefs;
    }  
    
    
      
    /** Accessor functions. */
    
    /** Returns the version string. May be null (though it shouldn't
     *  be in well-formed XML). */
    public String getVersion ()
    {
        return _version;
    }
    
    
    /** Returns the encoding string. May be null. */
    public String getEncoding ()
    {
        return _encoding;
    }
    

    /** Returns the standalone string. May be null. */
    public String getStandalone ()
    {
        return _standalone;
    }

    
    /* Processes each byte which comes through, looking for an XML 
     * declaration.  When it has a complete one, parses out the
     * parameters and makes them available. 
     * 
     * The XML declaration must be the first thing in the file.
     */
    private void process (int b) 
    {
        /* Determine the line ending type(s). */
        checkLineEnd(b);
        _prevChar = b;
        
        if (!seenChars || declBuf != null) {
            if (declBuf == null && b == (int) '<') {
                declBuf = new StringBuffer ("<");
            }
            else if (declBuf != null) {
                declBuf.append ((char) b);
                if ((char) b == '>')  {
                    processDecl ();
                    declBuf = null;
                } 
            }
        }
        if (refBuf == null && b == (int) '&') {
            refBuf = new StringBuffer ("&");
        }
        else if (refBuf != null) {
            if (refBuf.length() == 1 && b != (int) '#') {
                // If & isn't followed by #, it's not a character
                // reference.
                refBuf = null;
            }
            else if (b == ';') {
                processRef ();
                refBuf = null;
            }
            else {
                refBuf.append ((char) b);
            }
        }
        seenChars = true;
    }
    
    /* We have the first thing to be enclosed in angle
     * brackets in declBuf.  See if it's an XML declaration,
     * and if so, extract the interesting information. 
     */
    private void processDecl ()
    {
        String decl = declBuf.toString ();
        if (!decl.startsWith ("<?xml") ||
            !decl.endsWith ("?>")) {
            declBuf = null;
        }
        else {
            // get version, encoding, standalone
            int off;
            int off1 = 0;
            off = decl.indexOf ("version");
            if (off > 0) {
                _version = extractParam (decl, off);
                off1 = off;
            }
            
            // Use of off1 enforces order of attributes
            off = decl.indexOf ("encoding", off1);
            if (off > 0) {
                _encoding = extractParam (decl, off);
                off1 = off;
            }
            
            off = decl.indexOf ("standalone", off1);
            if (off > 0) {
                _standalone = extractParam (decl, off);
            }
        }
    }
    
    
    /* We have a character reference -- or at least something
     * that looks vaguely like one -- in refBuf.  This includes
     * the initial &# but not the final semicolon.
     * 
     * According to the w3c documentation, the 'x' which indicates
     * a hexadecimal value must be lower case, but the 
     * hexadecimal digits may be upper or lower case.
     */
    private void processRef ()
    {
        boolean isHex = (refBuf.charAt (2) == 'x');
        int val = 0;
        // Copy refBuf to a local variable so we can make sure
        // it gets nulled however we return.
        StringBuffer refBuf1 = refBuf;
        refBuf = null;
        if (isHex) {
            for (int i = 3; i < refBuf1.length (); i++) {
                char ch = Character.toUpperCase (refBuf1.charAt (i));
                if (ch >= 'A' && ch <= 'F') {
                    val = 16 * val + ((int) ch - 'A' + 10);
                }
                else if (ch >= '0' && ch <= '9') {
                    val = 16 * val + ((int) ch - '0');
                }
                else {
                    return;        // invalid character in hex ref
                }
            }
        }
        else {
            // better be decimal
            for (int i = 2; i < refBuf1.length (); i++) {
                char ch = refBuf1.charAt (i);
                if (ch >= '0' && ch <= '9') {
                    val = 10 * val + ((int) ch - '0');
                }
                else {
                    return;        // invalid character in hex ref
                }
            }
        }
        _charRefs.add (new Integer (val));
    }
    
    
    
    /* extract a parameter (after an equal sign)
     * from a string, after the offset off. */
    private String extractParam (String str, int off)
    {
        int equIdx = str.indexOf ('=', off);
        if (equIdx == -1) {
            return null;
        }
        // The parameter may be in single or double quotes,
        boolean singleQuote = false;
        boolean doubleQuote = false;
        int startOff = -1;
        for (int i = equIdx + 1; i < str.length(); i++) {
            char ch = str.charAt (i);
            if (Character.isWhitespace(ch)) {
                if (startOff < 0) {
                    continue;
                }
                else if (!singleQuote && !doubleQuote) {
                    // white space, and not in quotes.
                    return str.substring(startOff, i + 1);
                }
            }
            else if (ch == '\'' && !doubleQuote) {
                if (!singleQuote) {
                    // Start of single-quoted string
                    singleQuote = true;
                    startOff = i + 1;
                }
                else {
                    // End of single-quoted string
                    return str.substring (startOff, i);
                }
            }
            else if (ch == '"' && !singleQuote) {
                if (!doubleQuote) {
                    // Start of double-quoted string
                    doubleQuote = true;
                    startOff = i + 1;
                }
                else {
                    // End of double-quoted string
                    return str.substring (startOff, i);
                }
            }
            else if (startOff < 0) {
                // Non-whitespace character, start of unquoted string
                startOff = i;
            }
        }
        return null;        // fell off end without finding a valid string
    }
    /* Accumulate information about line endings. ch is the
    current character, and _prevChar the one before it. */
     protected void checkLineEnd (int ch)
     {
        if (ch == LF) {
             if (_prevChar == CR) {
                 _lineEndCRLF = true;
             }
             else {
                 _lineEndLF = true;
             }
         }
         else if (_prevChar == CR) {
            _lineEndCR = true;
        }
     }

     public String getKindOfLineEnd() {
         if (_lineEndCR || _lineEndLF || _lineEndCRLF) {
             if (_lineEndCRLF) {
                 return "CRLF";
             }
             if (_lineEndCR) {
                 return "CR";
             }
             if (_lineEndLF) {
                 return "LF";
             }
         }
         return null;
     }
     
    
}
