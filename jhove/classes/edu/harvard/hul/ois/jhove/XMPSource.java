/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

//import java.io.InputStream;
import java.io.Reader;

import org.xml.sax.InputSource;
import java.io.IOException;

/**
 * Class for providing an InputSource to XMPHandler.
 * Only an InputSource based on a Reader is supported.
 * 
 * Each module can provide its own subclass of XMPSource.
 * The subclass must provide a way to
 * reset to the beginning and reread the data when makeProperty
 * is called.
 * 
 * @author Gary McGath
 *
 */
public abstract class XMPSource extends InputSource {

    /** The Reader on which the InputSource is based. */
    protected Reader _reader;
    

    /**
     * Constructor with Reader.
     */
    public XMPSource(Reader rdr) {
        super(rdr);
        _reader = rdr;
    }


    /**
     *  Generates a property from the underlying data.
     *  The beginning and ending processing instructions are
     *  stripped out.
     */
    public Property makeProperty () throws IOException
    {
        boolean maybePI = false;   // set to true for ?xpacket partial match
        boolean seenStart = false; // set to true after initial xpacket
        resetReader ();            // go back to the beginning
        StringBuffer textBuf = new StringBuffer ();
        StringBuffer xpacBuf = new StringBuffer ();
        for (;;) {
            int ch = _reader.read();
            if (ch < 0) {
                break;
            }
            if (maybePI) {
                xpacBuf.append((char) ch);
                if ("<?xpacket".equals (xpacBuf.toString ())) {
                    if (!seenStart) {
                        // This is the starting xpacket.  Clear away
                        // everything to the closing ?>
                        seenStart = true;
                        xpacBuf.setLength (0);
                        maybePI = false;
                        int prevCh = 0;
                        for (;;) {
                            ch = _reader.read ();
                            if (ch < 0 ||
                                 (prevCh == (int) '?' && ch == (int) '>')) {
                                break;
                            }
                            prevCh = ch;
                        }
                    }
                    else {
                        // This is the ending xpacket. Discard it.
                        // We're done.
                        break;
                    }
                }
                if (!"<?xpacket".startsWith(xpacBuf.toString ())) {
                    // Not an xpacket -- clear xpacBuf into the prop string
                    maybePI = false;
                    textBuf.append (xpacBuf);
                    xpacBuf.setLength (0);
                }
            }
            else {
                if (ch == '<') {
                    // This could be the start of an <?xpacket?>.
                    // Start buffering.
                    maybePI = true;
                    xpacBuf.append ((char) ch);
                }
                else {
                    // Just plain text.  Append it.
                    textBuf.append ((char) ch);
                }
            }
        }
        // Some XMP's end with lots of white space, so give
        // it a trim before returning.
        return new Property ("XMP",
                PropertyType.STRING,
                textBuf.toString ().trim ());
    }
    
    
    /**
     *  Causes reading to begin from the start again.
     *  Typically this means creating a new value for
     *  _reader that will start over.
     */
    protected abstract void resetReader ();

}
