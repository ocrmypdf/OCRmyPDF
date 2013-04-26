/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;

/**
 * Tokenizer subclass which gets data from an object stream.
 *
 * @author Gary McGath
 *
 */
public class StreamTokenizer extends Tokenizer {

    /** Source from which to read bytes. */
    private Stream _stream;
    
    /** Backup flag. */
    private boolean _backupFlag;
    
    /** Last character read.  Will be returned again if _backupFlag
     *  is true. */
    private int _lastChar;
    
    private static final String NO_STREAM = 
        "Streams may not be embedded in object streams";

    public StreamTokenizer (RandomAccessFile file, Stream stream)
    {
        super ();
        _file = file;
        _stream = stream;
        _backupFlag = false;
    }

    /** Streams can occur only in files, not in streams,
     *  so this should never be called.
     */
    protected void initStream (Stream token) 
        throws IOException, PdfException
    {
        throw new PdfMalformedException (NO_STREAM);
    }

    /** Gets a character from the file, using a buffer. */
    public int readChar () throws IOException
    {
        if (_backupFlag) {
            _backupFlag = false;
            return _lastChar;
        }
        else {
            _lastChar = _stream.read ();
            return _lastChar;
        }
    }

    /**
     *  Set the Tokenizer to a new position in the stream.
     *
     *  @param  offset  The offset in bytes from the start of the stream.
     */
    public void seek (long offset)
        throws IOException, PdfException
    {
        // Advancing in the stream is easy.  Backing up requires starting
        // the stream over.
        if (!_stream.advanceTo ((int) offset)) {
            _stream.initRead (_file);
            _stream.advanceTo ((int) offset);
        }
        seekReset (_stream.getOffset());
    }

    /** Sets the offset of a Stream to the current file position.
     *  Only the file-based tokenizer can do this, so this should never
     *  be called. 
     */
    protected void setStreamOffset (Stream token) 
        throws IOException, PdfException
    {
        throw new PdfMalformedException (NO_STREAM);
    }


    /**
     *   Back up a byte so it will be read again.
     */
    public void backupChar ()
    {
        _backupFlag = true;
    }

}
