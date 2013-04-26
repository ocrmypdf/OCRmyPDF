/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;

/**
 * An InputStream layered on top of a RandomAccessFile.
 * This is useful for a Module which has requirements that
 * force it to use a RandomAccessFile, but is usually
 * accessed sequentially.
 * 
 * An RAFInputStream maintains its own position information
 * in the file, so multiple RAFInputStreams in the same file
 * will work without interference.  However, this class is
 * not thread-safe.
 * 
 * @author Gary McGath
 *
 */
public class RAFInputStream extends InputStream {

    /* The file on which the stream is based */
    private RandomAccessFile _raf;
    
    /* Size of fileBuf */
    private int fileBufSize;
    
    /* Buffer for reading from the file */
    private byte[] fileBuf;
    
    /* Offset for reading next byte from filebuf */
    private int fileBufPos;
    
    /* Number of valid bytes in fileBuf */
    private int fileBufBytes;
    
    /* Position in file for next read from RandomAccessFile */
    private long fileOffset;
    
    /* EOF flag */
    boolean eof;
    
    /**
     *  Constructor with default buffer size.
     *  The stream starts at the current position of the
     *  RandomAccessFile.
     * 
     *  @param   raf   The file on which the
     *                 stream is to be based.
     */
    public RAFInputStream(RandomAccessFile raf) {
        super();
        _raf = raf;
        fileBufSize = 65536;  // pick a size, any size
        init ();
    }


    /**
     *  Constructor with buffer size.
     *  The stream starts at the current position of the
     *  RandomAccessFile.
     * 
     *  @param   raf         The file on which the
     *                       stream is to be based.
     * 
     *  @param   bufferSize  The buffer size to be used.
     *                       If less than or equal to 0, the
     *                       default buffer size is used.
     */
    public RAFInputStream(RandomAccessFile raf, int bufferSize) {
        super();
        _raf = raf;
        fileBufSize = (bufferSize <= 0 ? 65536 : bufferSize);
        init ();
    }

    private void init ()
    {
        fileBufBytes = 0;
        fileBufPos = 0;
        fileBuf = new byte[fileBufSize];
        try {
            fileOffset = _raf.getFilePointer ();
        }
        catch (IOException e) {}
        eof = false;
        
    }
    /**
     *  Reads a single byte from the file.
     */
    public int read() throws IOException {
        if (eof) {
            return -1;
        }
        if (fileBufPos >= fileBufBytes) {
            // Need to read another bufferful
            _raf.seek (fileOffset);
            fileBufBytes = _raf.read (fileBuf);
            fileBufPos = 0;
            if (fileBufBytes <= 0) {
                // No more in file
                eof = true;
                return -1;
            }
            else {
                fileOffset += fileBufBytes;
            }
        }
        return ((int) fileBuf[fileBufPos++] & 0XFF);
    }
    
    /**
     * Reads some number of bytes from the input stream and
     * stores them into the buffer array b. The number of
     * bytes actually read is returned as an integer.
     */
    public int read (byte[] b) throws IOException
    {
        int bytesToRead = b.length;
        int bytesRead = 0;
        for (;;) {
            // See how many bytes are available in fileBuf.
            int fbAvail = fileBufBytes - fileBufPos;
            if (fbAvail <= 0) {
                // Need to read another bufferful
                _raf.seek (fileOffset);
                fileBufBytes = _raf.read (fileBuf);
                fileBufPos = 0;
                if (fileBufBytes <= 0) {
                    // No more in file -- return what we have
                    eof = true;
                    return bytesRead;
                }
                fbAvail = fileBufBytes;
                fileOffset += fileBufBytes;
            }
            if (fbAvail > bytesToRead) {
                // We have more than enough bytes.
                fbAvail = bytesToRead;
            }
            for (int i = 0; i < fbAvail; i++) {
                b[bytesRead++] = fileBuf[fileBufPos++];
                bytesToRead--;
            }
            if (bytesToRead == 0) {
                return bytesRead;
            }
        }
    }

    /**
     * Reads up to len bytes of data from the input stream 
     * into an array of bytes. An attempt is made to read as 
     * many as len bytes, but a smaller number may be read, 
     * possibly zero. The number of bytes actually read is
     * returned as an integer.
     * 
     */
    public int read(byte[] b, int off, int len) throws IOException 
    {
        int bytesToRead = len;
        int bytesRead = 0;
        for (;;) {
            // See how many bytes are available in fileBuf.
            int fbAvail = fileBufBytes - fileBufPos;
            if (fbAvail <= 0) {
                // Need to read another bufferful
                _raf.seek (fileOffset);
                fileBufBytes = _raf.read (fileBuf);
                fileBufPos = 0;
                if (fileBufBytes <= 0) {
                    // No more in file -- return what we have
                    eof = true;
                    return bytesRead;
                }
                fbAvail = fileBufBytes;
                fileOffset += fileBufBytes;
            }
            if (fbAvail > bytesToRead) {
                // We have more than enough bytes.
                fbAvail = bytesToRead;
            }
            for (int i = 0; i < fbAvail; i++) {
                b[off + bytesRead++] = fileBuf[fileBufPos++];
                bytesToRead--;
            }
            if (bytesToRead == 0) {
                return bytesRead;
            }
        }
    }


    /** Skips some number of bytes.
     * 
     *  @return  The number of bytes actually skipped.
     */
    public long skip (long n) throws IOException 
    {
        // If the range of the skip lies
        // within the current buffer, we just adjust
        // the buffer offset.
        int bytesLeft = fileBufBytes - fileBufPos;
        if (bytesLeft > n) {
            fileBufPos += (int) n;
        }
        else {
            // doesn't fit within the buffer.            
            // Set up to seek to the new position.
            //long curPos = _raf.getFilePointer ();
            if (fileOffset + n - bytesLeft  > _raf.length ()) {
                fileOffset = _raf.length ();
            }
            //seek (curPos + n - bytesLeft);
            else {
                fileOffset += n - bytesLeft;
            }
            fileBufBytes = 0;   // Invalidate current buffer
        }
        return n;
    }
    
    
    
    /**
     *  Returns the RandomAccessFile object.
     */
    public RandomAccessFile getRAF ()
    {
        return _raf;
    }


    /**  Positions the stream to a different point in the file.
     *   This invalidates the buffer.
     */
    public void seek (long offset) throws IOException
    {
        _raf.seek (offset);
        fileBufBytes = 0;
        fileBufPos = 0;
        eof = false;
    }
    
    /**  Returns the current position in the file.  
     *   What is reported is the position of the byte
     *   in the file which was last extracted from
     *   the buffer.
     */
    public long getFilePos () throws IOException
    {
        return _raf.getFilePointer() -
                (fileBufBytes - fileBufPos);
    }
}
