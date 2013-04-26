/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

//import java.io.InputStream;
import java.io.*;
import edu.harvard.hul.ois.jhove.XMLWrapperStream;

//import edu.harvard.hul.ois.jhove.XMPSource;

/**
 * Class for providing an InputSource to XMPHandler.
 * Only an InputSource based on a Reader is supported.
 *
 *  @author Gary McGath
 *
 */
public final class PdfXMPSource 
    extends edu.harvard.hul.ois.jhove.XMPSource {

    private PdfStream _stream;
    private RandomAccessFile _raf;
    protected String _encoding;
    
    /**
     * Constructor based on Stream object. 
     * Since a double read may be necessary, we have
     * one version without encoding (before it's known),
     * and another with encoding. 
     * 
     * @param stream   PDFStream containing the XMP
     * @param raf      The RandomAccessFile object underlying the PDF
     */
    public PdfXMPSource(PdfStream stream, 
            RandomAccessFile raf)
            throws UnsupportedEncodingException {
        super (new InputStreamReader 
                (new XMLWrapperStream 
                 (new StreamInputStream (stream, raf),
                    "XMP", "1.0", null, null)));
        //super(rdr);
        _stream = stream;
        _raf = raf;
    }



    /**
     * Constructor based on Stream object with 
     * encoding specified. 
     * 
     * @param stream   PDFStream containing the XMP
     * @param raf      The RandomAccessFile object underlying the PDF
     * @param encoding The character encoding to use
     */
    public PdfXMPSource(PdfStream stream, 
            RandomAccessFile raf,
            String encoding)
            throws UnsupportedEncodingException {
        super (new InputStreamReader 
            (new StreamInputStream (stream, raf), encoding));
        //super(rdr);
        _stream = stream;
        _raf = raf;
        _encoding = encoding;
    }


    /* (non-Javadoc)
     * 
     * Resets the reader by reinitializing it from the PdfStream.
     * 
     * @see edu.harvard.hul.ois.jhove.XMPSource#resetReader()
     */
    protected void resetReader() {
        try {
            if (_encoding == null) {
                _reader = new InputStreamReader 
                   (new StreamInputStream (_stream, _raf));
            }
            else {
                _reader = new InputStreamReader 
                    (new StreamInputStream 
                        (_stream, _raf), _encoding);
            }
        }
        catch (UnsupportedEncodingException e) {
            // Has no business happening if it didn't the first time.
        }
    }

}
