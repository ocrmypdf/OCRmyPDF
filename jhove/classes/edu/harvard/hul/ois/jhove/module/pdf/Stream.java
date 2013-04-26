/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

//import edu.harvard.hul.ois.jhove.*;
import java.io.*;
//import java.util.*;
//import java.util.zip.InflaterInputStream;

/**
 *  Class to encapsulate a stream token.  The content of the
 *  stream is not saved, only its length and starting offset.
 */
public class Stream
    extends Token
{
    /** Length of stream. */
    private long _length;
    
    /** Starting offset in file. */
    private long _offset;
    
    /** Number of bytes read so far. */
    private int _bytesRead;

    /** Filters which apply to this stream. */
    private Filter[] _filters;
    
    /** InputStream which incorporates all the filters. */
    private InputStream _inStream;
    
    /** Byte array which contains the raw file data for reading. */
    private byte[] _sdata;

    /** Constructor. */
    public Stream ()
    {
        super ();
        _length = 0;
        _offset = -1;
        _filters = new Filter[0];
        _bytesRead = 0;
        _sdata = null;
    }

    /** Returns the length of the stream.  This is 0, unless
     *  the Stream's setLength method has been called. 
     */
    public long getLength ()
    {
        return _length;
    }

    /**
     *  Sets the length field.
     *  This should be the length of the stream proper 
     *  (not counting its dictionary) before filtering, in other words,
     *  the number of bytes stored in the file. 
     */
    public void setLength (long length)
    {
        _length = length;
    }

    /** Returns the current offset in the stream.  This is -1, unless
     *  the Stream's setOffset method has been called. 
     */
    public long getOffset ()
    {
        return _offset;
    }

    /**
     *  Sets the offset field.
     */
    public void setOffset (long offset)
    {
        _offset = offset;
    }
    
    
    /** Sets the array of filters used by the stream.
     *  This must be called before initRead.
     */
    public void setFilters (Filter[] filters) 
    {
        _filters = filters;
    }


    /** Prepares for reading the Stream. 
     *  If the filter List includes one which we don't support, throws a
     *  PdfException.  This supports the abbreviated filter names
     *  in Appendix H of the PDF spec. */
    public void initRead (RandomAccessFile raf) 
            throws IOException, PdfException 
    {
        _bytesRead = 0;
        raf.seek(_offset);
        //InputStream is = new RAFInputStream (raf);
        /* We can't easily resume reading a filtered stream if we
         * seek elsewhere in the file, so the only really
         * safe bet is to read it all into memory first.
         * Fortunately, _length tells us the number of raw
         * bytes we need to read.  This also saves rereading
         * when we need to reset the stream. */
        if (_sdata == null) {
            _sdata = new byte[(int) _length];
            int ln = 0;
            while (ln < _length) {
                int n = raf.read (_sdata, ln, (int) (_length - ln));
                if (n <= 0) {
                    break;
                }
                ln += n;
            }
        }
        InputStream is = new ByteArrayInputStream (_sdata);
        for (int i = 0; i < _filters.length; i++) {
            Filter filt = (Filter) _filters[i];
            String filtName = filt.getFilterName ();
            FilterInputStream fis = null;
            /* ASCIIHex-, ASCII85- and RunLengthDecode are currently
             * just stubs.  If we ever really need them, we should
             * consider grabbing the implementations in PDFBox on
             * SourceForge, which should (hint to third-party developers
             * if you need them) just drop into place with
             * the addition of an include. */
            if ("ASCIIHexDecode".equals (filtName) || "AHx".equals (filtName)) {
                is = new AsciiHexFilterStream (is);
            }
            else if ("ASCII85Decode".equals (filtName) || "A85".equals (filtName)) {
                is = new Ascii85FilterStream (is);
            }
            else if ("FlateDecode".equals (filtName) || "Fl".equals (filtName)) {
                // InflaterInputStream does only part of the job. 
                // PdfFlateInputStream enhances it with Predictor support.
                is = new PdfFlateInputStream (is, filt.getDecodeParms());
            }
            else if ("RunLengthDecode".equals (filtName) || "RL".equals (filtName)) {
                is = new RunLengthFilterStream (is);
            }
        }
        _inStream = is;
    }
    
    
    /** Reads a byte from the Stream, applying the Filters if any.
     */
    public int read() throws IOException 
    {
        
        int val = _inStream.read();
        if (val >= 0) {
            ++_bytesRead;
        }
        return val;
    }
    
    /** Reads a sequence of bytes from the Stream, applying the
     *  Filters if any. 
     */
    public int read (byte[] b) throws IOException
    {
        int n = _inStream.read (b);
        if (n > 0) {
            _bytesRead += n;
        }
        return n;
    }
    
    /** Skips a specified number of bytes in the stream. */
    public long skipBytes (long n) throws IOException
    {
        long val = _inStream.skip(n);
        _bytesRead += val;
        return val;
    }

    /** Reads an ASCII string, which may be preceded by white space.
     *  Will eat the first white space character after the ASCII
     *  string. */
    public int readAsciiInt () throws IOException, PdfException
    {
        boolean digitSeen = false;
        int val = 0;
        for (;;) {
            char c = (char) read ();
            if (Character.isDigit(c)) {
                digitSeen = true;
                val = val * 10 + (c - '0');
            }
            else if (digitSeen) {
                /* Non-digit after a digit; we're done */
                break;
            }
            else if (!Character.isWhitespace(c)) {
                throw new PdfMalformedException 
                    ("Malformed ASCII number in stream");
            }
        }
        return val;
    }
    
    /** Advances to a specified offset in the stream.  The offset
     *  is defined as the number of decompressed bytes which
     *  precede the position in the stream.  Returns <code>true</code>
     *  if the advance is successful, <code>false</code> if the
     *  point has already been passed or some other failure occurs.
     */
    public boolean advanceTo (int offset) throws IOException {
        if (offset < _bytesRead) {
            return false;   // can't get there from here
        }
        else {
            while (_bytesRead < offset) {
                if (skipBytes (offset - _bytesRead) <= 0) {
                    break;
                }
            }
            return true;
        }
    }
}
