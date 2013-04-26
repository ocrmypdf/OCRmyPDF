/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.iff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Abstract class for a chunk that contains other chunks.
 * It is assumed that the nested chunks come last in the chunk,
 * so that once you start reading chunks, reaching the end of
 * the superchunk is the indicator that there are no more chunks
 * to read.
 *
 * @author Gary McGath
 *
 */
public abstract class Superchunk extends Chunk {

    private RepInfo _repInfo;
    
    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     * @param info     RepInfo object for error reporting
     */
    public Superchunk (ModuleBase module,
            ChunkHeader hdr, 
            DataInputStream dstrm,
            RepInfo info)
    {
        super (module, hdr, dstrm);
	_repInfo = info;
    }
    
    /**
     *  Reads and returns the next ChunkHeader within this Chunk,
     *  and takes care of byte counting.  If this Chunk is exhausted,
     *  returns null.
     */
    public ChunkHeader getNextChunkHeader () throws IOException
    {
        if (bytesLeft <= 0) {
            return null;
        }
       Chunk chunk = null;
       ChunkHeader chunkh = new ChunkHeader (_module, _repInfo);
       if (!chunkh.readHeader(_dstream)) {
           return null;
       }
       int chunkSize = (int) chunkh.getSize ();
       bytesLeft -= chunkSize + 8;
       return chunkh;
    }
}
