/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;

/**
 * A FragmentInputStream provides an interface by which
 * the scattered fragments of a Fragment List Box can
 * be read as a single stream.  Only fragments within
 * the originating file are supported, not fragments
 * in external files.
 *
 * @author Gary McGath
 *
 */
public class FragmentInputStream extends InputStream {

    private List<long []> _fragments;
    private RandomAccessFile _raf;
    private ListIterator<long []> fragIterator;
    private long curFragment[];
    byte[] fragBuffer;
    
    /* Offset within fragBuffer.  -1 indicates fragBuffer
     * does not contain valid data. */
    private int bufOffset;
    
    /* Offset in the file from the start of the current fragment. */
    private int fragOffset;
    
    /* Size allocated to the buffer. */
    private int _bufSize;

    /* Bytes of actual data in the buffer. */
    private int bufBytes;
    
    /**
     *  @param    fragments  List of fragment entries.
     *            Each fragment entry is an array of two longs,
     *            with fragment[0] being the length and
     *            fragment[1] the offset.
     */
    public FragmentInputStream(List<long []> fragments, RandomAccessFile raf) 
    {
        super();
        _fragments = fragments;
        _raf = raf;
        init (-1);
    }
    
    public FragmentInputStream (List<long []> fragments, 
                RandomAccessFile raf,
                int bufSize)
    {
        super ();
        _fragments = fragments;
        _raf = raf;
        init (bufSize);
    }
    
    private void init (int bufSize)
    {
        fragIterator = _fragments.listIterator ();
        // If no buffer size was specified, assign a default
        // size.
        if (bufSize <= 0) {
            bufSize = 8192;
        }
        _bufSize = bufSize;
        fragBuffer = new byte[bufSize];
        bufOffset = 0;
        bufBytes = 0;
    }

    /**
     * Returns the next byte from the stream, buffering each fragment
     * in turn until the last fragment is exhausted.
     * 
     * @return   The next byte of the stream, or -1 to indicate no
     *           more bytes are available.
     */
    public int read() throws IOException {
        if (bufOffset >= bufBytes) {
            // We need a fresh buffer read.
            if (curFragment == null || fragOffset >= curFragment[1]) {
                // We need a new fragment.
                if (fragIterator.hasNext ()) {
                    curFragment =  fragIterator.next ();
                    fragOffset = 0;
                }
                else {
                    // No more data available.
                    return -1;
                }
            }
            _raf.seek(curFragment[0] + fragOffset);
            bufBytes = _raf.read(fragBuffer);
            fragOffset += bufBytes;
            bufOffset = 0;
        }
        return fragBuffer[bufOffset++];
    }

}
