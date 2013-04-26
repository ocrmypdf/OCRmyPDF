/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

import java.io.DataInputStream;
import java.io.IOException;


/**
 * Implementation of the AIFF Sound Data Chunk.
 *
 * @author Gary McGath
 *
 */
public class SoundDataChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public SoundDataChunk (AiffModule module, ChunkHeader hdr,
			   DataInputStream dstrm)
    {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a SoundData property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info)
	throws IOException
    {
        AiffModule module = (AiffModule) _module;
        Property[] propArray = new Property[3];
        long offset = module.readUnsignedInt (_dstream);
        long blockSize = module.readUnsignedInt (_dstream);
        propArray[0] = new Property ("Offset", PropertyType.LONG,
				     new Long (offset));
        propArray[1] = new Property ("BlockSize", PropertyType.LONG,
				     new Long (blockSize));
        propArray[2] = new Property ("DataLength", PropertyType.LONG,
				     new Long (bytesLeft - 8));
        module.addAiffProperty(new Property ("SoundData",
					     PropertyType.PROPERTY,
					     PropertyArity.ARRAY,
					     propArray));
        // This must be called precisely at this point in reading the
        // data stream to produce an accurate result.
        module.markFirstSampleOffset (offset);
        module.skipBytes (_dstream, (int) (bytesLeft - 8), module);

        return true;
    }
}
