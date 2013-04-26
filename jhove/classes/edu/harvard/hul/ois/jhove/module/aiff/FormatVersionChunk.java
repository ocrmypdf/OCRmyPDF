/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

import java.io.*;
import java.util.*;

/**
 * Implementation of the AIFF Format Version Chunk.
 * This chunk occurs only in the AIFF/C variant.
 * 
 * @author Gary McGath
 *
 */
public class FormatVersionChunk extends Chunk {

    
    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public FormatVersionChunk (
            AiffModule module,
            ChunkHeader hdr, 
            DataInputStream dstrm)
    {
        super (module, hdr, dstrm);
    }
    
    /** Reads a chunk and puts a FormatVersion property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk (RepInfo info) throws IOException
    {
        AiffModule module = (AiffModule) _module;
        long timestamp = module.readUnsignedInt (_dstream);
        // The timestamp is in seconds since January 1, 1904.
        // We must convert to Java time.
        Date jTimestamp = module.timestampToDate (timestamp);
        module.addAiffProperty (new Property ("FormatVersion",
                PropertyType.DATE,
                jTimestamp));
        return true;
    }
}
