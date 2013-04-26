/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2006 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.IOException;
import java.io.*;

/**
 * A ChecksumInputStream is a FilterInputStream with the added
 * functionality of calculating checksums as it goes.  
 * 
 * The idea of replacing this with java.util.zip.CheckedInputStream
 * looks very tempting, but we need the byte count, which
 * CheckedInputStream doesn't provide.
 * 
 * @author Gary McGath
 *
 */
public class ChecksumInputStream extends FilterInputStream {

    private InputStream subsumedStream;
    private Checksummer _cksummer;
    private long _nBytes;
    
    /**
     *  Constructor.
     * 
     *  @param stream   Stream to be filtered
     *  @param cksummer Object to calculate checksum on the bytes
     *                  as they are read
     */
    public ChecksumInputStream(InputStream stream, Checksummer cksummer) {
        super (stream);
        subsumedStream = stream;
        _cksummer = cksummer;
        _nBytes = 0;
    }

    /**
     *  Reads a byte from the subsumed stream, updating
     *  the byte count and the checksums.
     */
    public int read() throws IOException {
        int ch = subsumedStream.read ();
        if (ch >= 0) {
            _nBytes++;
            if (_cksummer != null) {
                _cksummer.update (ch);
            }
        }
        return ch;
    }

    /**
     * Reads some number of bytes from the input stream and
     * stores them into the buffer array b. The number of
     * bytes actually read is returned as an integer.
     * 
     * All bytes read are fed through the checksummer.
     */
    public int read(byte[] b) throws IOException 
    {
        int len = subsumedStream.read (b);
        // Careful here -- don't want to add -1 bytes at EOF
        if (len > 0) {
	    if (_cksummer != null) {
		_cksummer.update (b);
	    }
            _nBytes += len;
        }
        return len;
    }
    
    /**
     * Reads up to len bytes of data from the input stream 
     * into an array of bytes. An attempt is made to read as 
     * many as len bytes, but a smaller number may be read, 
     * possibly zero. The number of bytes actually read is
     * returned as an integer.
     * 
     * All bytes read are fed through the checksummer.
     */
    public int read(byte[] b, int off, int len) throws IOException 
    {
        len = subsumedStream.read (b, off, len);
        // Careful here -- don't want to add -1 bytes at EOF
        if (len > 0) {
            if (_cksummer != null) {
		_cksummer.update (b, off, len);
            }
            _nBytes += len;
        }
        return len;
    }
    
    /**
     *  Skips n bytes.
     *  Reads them and feeds them through the checksummer.
     */
    public long skip (long n) throws IOException {
        long nret = 0;
        while (n > 0) {
            // grab the data in reasonable buffer-sized chunks.
            int bufsize = (int) (n > 8192 ? 8192 : n);
            byte[] buf = new byte[bufsize];
            int nread = read (buf);
            if (nread <= 0) {
                break;
            }
            nret += nread;
            n -= nread;
        }
        return nret;
    }
    
    /**
     *  Closes the subsumed stream.
     */
    public void close () throws IOException
    {
        subsumedStream.close();
    }
    
    /**
     *  Returns the byte count to date on the stream.
     *  This returns the number of bytes read.
     *  Because of buffering, this is not a reliable
     *  indicator of how many bytes have actually been processed.
     */
    public long getNBytes ()
    {
        return _nBytes;
    }
    
    /**
     *  Returns the Checksummer object.
     */
    public Checksummer getChecksummer ()
    {
        return _cksummer;
    }
}
