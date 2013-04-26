/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;
import java.util.zip.*;

/**
 * An enhancement of InflaterInputStream to support Predictor and Columns.
 * How complicated does this get?  Do I need to read the whole thing before I can
 * "predict" anything?
 * 
 * @author Gary McGath
 *
 */
public class PdfFlateInputStream extends FilterInputStream {

    private InflaterInputStream iis;
    private PdfDictionary decodeParms;
    private int predictor;
    private int columns;
    /* bits per component */
    private int bpc;
    /* colors -- the term is being used in some idiosyncratic sense */
    private int colors;

    /* Number of bytes to hold last column of previous row, if needed */
    private int colBytes;
    /* Length of the total row, including space for last column.
     * (Actual length of a predictive row is rowLen - colBytes) */
    private int rowLen;
    /* Two row buffers for double buffering */
    private byte[] rowBuf;
    private byte[] rowBuf2;
    private int rowBufOff;    // aka linei_
    private boolean eof;

    /* offset to next available byte */
    private int iisBufOff;
    /* byte array read from IIS */
    private byte[] iisBuf;
    /* Allocation size for iisBuf */
    private final static int IISBUF_SIZE = 4096;
    /* iisBufLen -- number of bytes of valid data in iisBuf */
    private int iisBufLen;
    /* End of file indicator for IIS stream */
    private boolean iisEof;
    
    /**
     * Constructor with null DecodeParms dictionary
     * 
     * @param is    InputStream to be inflated
     */
    public PdfFlateInputStream(InputStream is) {
        this (is, null);
    }
    
    /**
     * Constructor with specified DecodeParms dictionary
     * 
     * @param is    InputStream to be inflated
     * @param parms DecodeParms dictionary.
     *              May be null, in which case this is equivalent
     *              to the one-parameter constructor.
     * 
     */
    public PdfFlateInputStream (InputStream is, PdfDictionary parms)
    {
        super(is);
        iis = new InflaterInputStream (is);
        /* Set default values */
        predictor = 1;   // no prediction
        columns = 1;  
        bpc = 8;
        colors = 1;

        decodeParms = parms;
        iisBuf = new byte [IISBUF_SIZE];
        iisBufLen = 0;
        iisBufOff = 0;
        iisEof = false;
        eof = false;
        if (parms != null) {
            /* Extract relevant dictionary defs */
            try {
                PdfSimpleObject pred = (PdfSimpleObject) parms.get ("Predictor");
                if (pred != null) {
                    predictor = pred.getIntValue();
                }
            }
            catch (Exception e) {}
            try {
                PdfSimpleObject col = (PdfSimpleObject) parms.get ("Columns");
                if (col != null) {
                    columns = col.getIntValue();
                }
            }
            catch (Exception e) {}
            try {
                PdfSimpleObject bitsper = (PdfSimpleObject) parms.get ("BitsPerComponent");
                if (bitsper != null) {
                    bpc = bitsper.getIntValue();
                }
            }
            catch (Exception e) {}
        }
        /* Calculate byte counts */
        if (predictor != 1) {
            colBytes = (colors * bpc + 7) / 8;
            rowLen = (columns * colors * bpc + 7) / 8 + colBytes;
            rowBuf = new byte[rowLen];
            rowBuf2 = new byte[rowLen];
            rowBufOff = rowLen;
        }
    }

    /** Reads one byte from the stream.
     *  Returns -1 if end of file is reached.
     */
    public int read() throws IOException 
    {
        if (eof) {
            return -1;
        }
        if (predictor == 1) {
            return readIISByte ();
        }
        if (rowBufOff == rowLen) {
            // Starting out, or previous row exhausted.
            readRow ();
            if (eof) {
                return -1;
            }
        }
        return rowBuf[rowBufOff++] & 0XFF;
    }
    
    /** Reads the specified number of bytes into a buffer.
     *  Returns the number of bytes actually read, or -1 if
     *  end of file has been reached. */
    public int read (byte[] b) throws IOException
    {
        /* Need to read a byte at a time till we have something to expand */
        return read (b, 0, b.length);
    }

    /** Reads the specified number of bytes into a buffer
     *  with offset and length specified.
     *  Returns -1 if end of file has been reached.
     *  No matter how much is requested, this will only return one
     *  row's worth of data at most. 
     */
    public int read (byte[] b, int off, int len) throws IOException
    {
        if (eof) {
            return -1;
        }
        if (predictor == 1) {
            // predictor of 1 means no predictor.
            //return iis.read (b, off, len);
            // That can't be right, can it?
            return readIISBytes(b, off, len);
        }
        if (rowBufOff == rowLen) {
            // Starting out, or previous row exhausted.
            readRow ();
            if (eof) {
                return -1;
            }
        }
        if (len > rowLen - rowBufOff) {
            /* Return no more than a row's worth, regardless */
            len = rowLen - rowBufOff;
        }
        for (int i = 0; i < len; i++) {
            b[off + i] = rowBuf[rowBufOff++];
        }
        return len;
    }
    
    public long skip (long n) throws IOException {
        return skipIISBytes(n);
    }
    
    /* Takes bytes from the input buffer and turn them into bytes in the output buffer.
     * Returns the number of bytes available.
     */
    private int processBytes ()
    {
        int avail = 0;
        
        return avail;
    }
    
    /* Reads a row's worth of data and stores in rowBuf. */
    private void readRow () throws IOException
    {
        /* Swap rowBuf and rowBuf2 */
        byte[] r = rowBuf;
        rowBuf = rowBuf2;
        rowBuf2 = r;
        rowBufOff = colBytes;
        
        // Ignore weird predictor of 15 for now
        if (predictor >= 10) {
            // throw one byte away
            readIISByte ();
        }
        int off = colBytes;
        while (off < rowLen) {
            int n = readIISBytes(rowBuf, off, rowLen - off);
            if (n > 0) {
                off += n;
            }
            else { 
                eof =true; 
                return; 
            }
        }
        switch (predictor) {
            case 1:
            case 10:
                break;
            case 2:
                // TIFF predictor
            case 11:
                // Sub -- left
                for (int i = colBytes; i < rowLen; i++) {
                    rowBuf[i] += rowBuf[i-colBytes];
                }
                break;
            case 12:    
                // Up -- above
                for (int i = colBytes; i < rowLen; i++) {
                    rowBuf[i] += rowBuf2[i]; 
                }
                break;
            case 13:
                // Average -- (left + above) / 2
                for (int i = colBytes; i < rowLen; i++) {
                    rowBuf[i] += ((rowBuf[i - colBytes] & 0xFF) + 
                                  (rowBuf2[i] & 0xFF)) / 2;
                }
                break;
            case 14:    // Paeth -- closest of left, above, upper-left
                for (int i=0+colBytes; i < rowLen; i++) {
                    int a = rowBuf[i - colBytes] & 0XFF;
                    int b = rowBuf2[i] & 0XFF;
                    int c = rowBuf2[i - colBytes] & 0XFF;
                    int p = a + b - c;
                    int pa = Math.abs(p - a);
                    int pb = Math.abs(p - b);
                    int pc = Math.abs(p - c);

                    int val;
                    if (pa<=pb && pa<=pc) {
                        val = a;
                    }
                    else if (pb<=pc) {
                        val = b;
                    }
                    else {
                        val = c;
                    }

                    rowBuf[i] += (byte)val;
                }
                break;
            case 15:    // optimum -- per line determination
                break;
        }
    }
    
    /** Get an "inflated" byte.  We do buffering here
     *  for efficiency. */
    private int readIISByte ()
             throws IOException
    {
        // iisBufOff -- offset to next available byte
        // iisBuf -- byte array read from IIS
        // iisBufLen -- number of bytes of valid data in iisBuf
        if (iisBufOff >= iisBufLen && !iisEof) {
            readIIS ();
        }
        if (iisEof) {
            return -1;
        }
        return (int) (iisBuf[iisBufOff++] & 0XFF);
    }
    
    /** Get a bufferload of bytes. */
    private int readIISBytes (byte[] buf, int off, int len) 
             throws IOException
    {
        if (iisBufOff >= iisBufLen && !iisEof) {
            readIIS ();
        }
        if (iisEof) {
            return -1;
        }
        /* We don't attempt to optimize across buffer boundaries */
        if (iisBufLen - iisBufOff < len) {
            len = iisBufLen - iisBufOff;
        }
        for (int i = off; i < off + len; i++) {
            buf[i] = iisBuf[iisBufOff++];
        }
        return len;
    } 
    
    /** Skip a specified number of bytes. */
    private long skipIISBytes (long n) throws IOException {
        if (iisBufOff >= iisBufLen && !iisEof) {
            readIIS ();
        }
        if (iisEof) {
            return -1;
        }
        if (iisBufLen - iisBufOff < n) {
            n = iisBufLen + iisBufOff;
        }
        iisBufOff += n;
        return n;
    }
    
    /** Fill up the IIS buffer.  Should be called only by
     *  other IIS buffer-specific routines. */
    private int readIIS () throws IOException
    {
        if (iisEof) {
            return -1;
        }
        int n = iis.read (iisBuf);
        iisBufOff = 0;
        iisBufLen = n;
        if (n <= 0) {
            iisEof = true;
        }
        return n;
    }
}
