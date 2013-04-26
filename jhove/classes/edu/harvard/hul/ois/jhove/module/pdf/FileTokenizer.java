/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;

/**
 *
 * Tokenizer subclass which gets data from a RandomAccessFile.
 * @author Gary McGath
 *
 */
public class FileTokenizer extends Tokenizer {


    /** Current offset to start of bytes stored in _fileBuffer */
    private long _fileBufferPositionOffset;

    /** File buffer */
    private byte[] _fileBuffer;
    
    /** Size for file buffer */
    private static final int FILEBUFSIZE = 4096;

    /** Number of valid bytes in fileBuffer */
    private int _fileBufferBytes;

    /** Offset to next valid byte in fileBuffer */
    private int _fileBufferOffset;


    public FileTokenizer (RandomAccessFile file)
    {
        super ();
        _file  = file;
        _fileBufferPositionOffset = -1;
        _fileBuffer = new byte[FILEBUFSIZE];
        initFileBuffer ();
    }

    private void initFileBuffer ()
    {
        _fileBufferBytes = 0;
        _fileBufferOffset = 0;
    }


    /** Gets the current position in the file.  This method is
     *  aware of buffering. */
    public long getFilePos () throws IOException
    {
        return _fileBufferPositionOffset + _fileBufferOffset;
    }


    /** Gets a character from the file, using a buffer. */
    public int readChar () throws IOException
    {
        if (_fileBufferOffset >= _fileBufferBytes) {
            // If the byte size is 0, we can assume a seek was already
            // done, but otherwise we must seek safety.
            if (_fileBufferBytes > 0) {
                long newOffset = _fileBufferPositionOffset + _fileBufferOffset;
                _file.seek (newOffset);
                _fileBufferPositionOffset = newOffset;
            }
            _fileBufferBytes = _file.read(_fileBuffer);
            if (_fileBufferBytes <= 0) {
                throw new EOFException ();
            }
            _fileBufferOffset = 0;
        }
        return (int) (_fileBuffer[_fileBufferOffset++] & 0XFF);
    }

    /**
     *  Set the Tokenizer to a new position in the file.
     *
     *  @param  offset  The offset in bytes from the start of the file.
     */
    public void seek (long offset)
        throws IOException
    {
        if (_fileBufferPositionOffset >= 0 &&
                offset >= _fileBufferPositionOffset &&
                offset < _fileBufferPositionOffset + _fileBufferBytes) {
            // Reposition within the buffer
            _fileBufferOffset = (int) (offset - _fileBufferPositionOffset);
        }
        else {
            _file.seek (offset);
            initFileBuffer ();
            _fileBufferPositionOffset = offset;
        }
        seekReset (offset);
    }


    /**
     *   Back up a byte so it will be read again.
     */
    public void backupChar ()
    {
        _fileBufferOffset--;
    }

    /** Streams can occur only in files, not in streams,
     *  so some of the initialization of a stream object 
     *  goes here.
     */
    protected void initStream (Stream token) throws IOException
    {
        token.setOffset (getFilePos ());
    }


    /** Sets the offset of a Stream to the current file position.
     *  Only the file-based tokenizer can do this, which is why this
     *  overrides the Tokenizer method. 
     */
    protected void setStreamOffset (Stream token) throws IOException
    {
        if (token.getOffset() < 0) {
            token.setOffset (getFilePos ());
        }
    }

}
