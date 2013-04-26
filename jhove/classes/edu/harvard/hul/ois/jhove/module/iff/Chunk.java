/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.iff;

import edu.harvard.hul.ois.jhove.*;

import java.io.*;

/**
 * Abstract superclass for IFF/AIFF chunks.
 * 
 * @author Gary McGath
 *
 */
public abstract class Chunk {

    protected ModuleBase _module;
    protected long bytesLeft;
    protected DataInputStream _dstream;

    /**
     *  Constructor.
     * @param module   The Module under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the data are being read
     */
    public Chunk (ModuleBase module,
            ChunkHeader hdr, 
            DataInputStream dstrm)
    {
        _module = module;
        bytesLeft = hdr.getSize ();
        _dstream = dstrm;
    }
    
    
    /** Reads a chunk and puts appropriate information into
     *  the RepInfo object. 
     * 
     * @param    info  RepInfo object to receive information
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     * @throws JhoveException 
     * 
     */
    public abstract boolean readChunk (RepInfo info) throws IOException, JhoveException;
    
    /** Convert a byte buffer cleanly to an ASCII string.
     *  This is used for fixed-allocation strings in Broadcast
     *  WAVE chunks, and might have uses elsewhere.
     *  If a string is shorter than its fixed allocation, we're
     *  guaranteed only that there is a null terminating the string,
     *  and noise could follow it.  So we can't use the byte buffer
     *  constructor for a string.
     */
    protected String byteBufString (byte[] b)
    {
        StringBuffer sb = new StringBuffer (b.length);
        for (int i = 0; i < b.length; i++) {
            byte c = b[i];
            if (c == 0) {
                // Terminate when we see a null
                break;
            }
            sb.append((char) c);
        }
        return sb.toString ();
    }
}
