/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the WAVE Data Chunk.
 * 
 * Data Chunks may occur either at the top level (i.e., under the RIFF
 * chunk) or under a data list chunk.  There can be only one top-level
 * Data Chunk.
 *
 * @author Gary McGath
 *
 */
public class DataChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public DataChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }
    
    /* We may want to have another constructor which sets a parent chunk. */

    /** Reads a chunk and puts a Data property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        Property lenProp = new Property ("DataLength",
                PropertyType.LONG,
                new Long (bytesLeft));
        // The behavior will be different if we are reading this under
        // a 'wavl' chunk.
        
        // If we have PCM compression, the number of samples is given
        // by the number of bytes divided by the sample blocking; otherwise
        // we use the Fact chunk to count samples.
        if (module.getCompressionCode() == FormatChunk.WAVE_FORMAT_PCM) {
            module.addSamples (bytesLeft / module.getBlockAlign ());
        }
        module.addWaveProperty(new Property ("Data",
                PropertyType.PROPERTY,
                lenProp));
        // This must be called precisely at this point in reading the
        // data stream to produce an accurate result.
        module.markFirstSampleOffset ();
        module.skipBytes (_dstream, (int) bytesLeft, module);
        return true;
    }

}
