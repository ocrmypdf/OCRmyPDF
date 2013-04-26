/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/


package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;


/** A StreamInputStream is an InputStream which provides the bytes
 *  from a PdfStream. It reads bytes from the PdfStream's underlying
 *  file starting at the beginning of the stream data and providing
 *  as many bytes as are indicated by its length.  No filters are
 *  applied; just the raw data is read.
 *  
 */
public class StreamInputStream extends InputStream {

    private RandomAccessFile _file;
    private long _startPos;
    private long _curPos;
    private long _length;
    
    public StreamInputStream (PdfStream pdfStream, RandomAccessFile file) 
    {
        _file = file;
        Stream strm = pdfStream.getStream ();
        _startPos = strm.getOffset ();
        _curPos = _startPos;
        _length = strm.getLength ();
        try {
            file.seek (_startPos);
        }
        catch (IOException e) {}
    }
 
 
    /** 
     *  Return one byte from the stream.
     *  When the end of the stream is reached, returns -1.
     */   
    public int read () throws IOException
    {
        if (_curPos - _startPos >= _length) {
            return -1;
        }
        else {
            _curPos++;
            int ch = _file.read ();
            return ch;
        }
    }
}