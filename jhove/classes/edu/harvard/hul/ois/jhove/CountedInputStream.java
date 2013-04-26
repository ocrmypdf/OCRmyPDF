/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;

/**
 * A FilterInputStream which passes only a specified
 * number of bytes, then returns an EOF condition.
 *
 * @author Gary McGath
 *
 */
public class CountedInputStream extends FilterInputStream {

    private int bytesLeft;
    
    /**
     * @param instrm       The InputStream being counted
     * @param count        The number of bytes to be allowed
     */
    public CountedInputStream(InputStream instrm, int count) {
        super(instrm);
        bytesLeft = count;
    }


    /** Reads a single byte from the stream and decrements
     *  the count of remaining bytes.  If the count
     *  is exhausted, returns -1 to signify end of file. */
    public int read() throws IOException {
        if (bytesLeft <= 0) {
            return -1;
        }
        else {
            int ch = super.read ();
            if (ch != -1) {
                --bytesLeft;
            }
            return ch;
        }
    }


    /**
     * Reads some number of bytes from the input stream and
     * stores them into the buffer array b. The number of
     * bytes actually read is returned as an integer.
     * 
     * The number of bytes read will not exceed the number
     * of bytes remaining in the count.  The count is
     * decremented by the number of bytes actually read.
     */
    public int read(byte[] b) throws IOException 
    {
        int len = b.length;
        int bytesRead;
        if (len <= bytesLeft) {
            // Limit doesn't affect us, do normal read
            bytesRead = super.read (b);
        }
        else {
            // Limit the read to bytesLeft
            bytesRead = super.read (b, 0, bytesLeft);
        }
        bytesLeft -= bytesRead;
        return bytesRead;
    }


    /**
     * Reads up to len bytes of data from the input stream 
     * into an array of bytes. An attempt is made to read as 
     * many as len bytes, but a smaller number may be read, 
     * possibly zero. The number of bytes actually read is
     * returned as an integer.
     * 
     * The number of bytes read will not exceed the number
     * of bytes remaining in the count.  The count is
     * decremented by the number of bytes actually read.
     */
    public int read(byte[] b, int off, int len) throws IOException 
    {
        int bytesRead;
        if (len <= bytesLeft) {
            // Limit doesn't affect us, do normal read
            bytesRead = super.read (b, off, len);
        }
        else {
            bytesRead = super.read (b, off, bytesLeft);
        }
        bytesLeft -= bytesRead;
        return bytesRead;
    }

    /**
     *  Skips n bytes.
     *  Decrements the count by the number of bytes
     *  actually skipped.
     */
    public long skip (long n) throws IOException {
        long bytesRead = super.skip (n);
        if (bytesLeft < bytesRead) {
            bytesLeft = 0;
        }
        else {
            bytesLeft -= bytesRead;
        }
        return bytesRead;
    }
}
