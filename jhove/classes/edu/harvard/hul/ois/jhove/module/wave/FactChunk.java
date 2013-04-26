/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the WAVE Fact Chunk.
 * The Fact chunk contains information specific to the
 * compression scheme.
 *
 * @author Gary McGath
 *
 */
public class FactChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public FactChunk(
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a Fact Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        Property sizeProp = new Property ("Size",
                PropertyType.LONG,
                new Long(bytesLeft));
        module.addWaveProperty (new Property ("Fact",
                PropertyType.PROPERTY,
                sizeProp));
        long numSamples = module.readUnsignedInt (_dstream);
        module.addSamples (numSamples);
        bytesLeft -= 4;
        module.skipBytes (_dstream, (int) bytesLeft, module);
        return true;
    }

}
