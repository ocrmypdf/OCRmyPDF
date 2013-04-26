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
 * Implementation of the WAVE Instrument Chunk, which
 * gives information about a MIDI instrument.  Similar to
 * the Sample chunk or the AIFF Instrument chunk, but simpler
 * than either.
 *
 * @author Gary McGath
 *
 */
public class InstrumentChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public InstrumentChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts an Instrument property into
     *  the RepInfo object. 
     * 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        int unshiftedNote = ModuleBase.readUnsignedByte (_dstream, _module);
        int fineTune = ModuleBase.readSignedByte (_dstream, _module);
        int gain = ModuleBase.readSignedByte (_dstream, _module);
        int lowNote = ModuleBase.readUnsignedByte (_dstream, _module);
        int highNote = ModuleBase.readUnsignedByte (_dstream, _module);
        int lowVelocity = ModuleBase.readUnsignedByte (_dstream, _module);
        int highVelocity = ModuleBase.readUnsignedByte (_dstream, _module);
        
        Property[] propArr = new Property[7];
        propArr[0] = new Property ("UnshiftedNote", PropertyType.INTEGER,
                    new Integer (unshiftedNote));
        propArr[1] = new Property ("FineTune", PropertyType.INTEGER,
                    new Integer (fineTune));
        propArr[2] = new Property ("Gain", PropertyType.INTEGER,
                    new Integer (gain));
        propArr[3] = new Property ("LowNote", PropertyType.INTEGER,
                    new Integer (lowNote));
        propArr[4] = new Property ("HighNote", PropertyType.INTEGER,
                    new Integer (highNote));
        propArr[5] = new Property ("LowVelocity", PropertyType.INTEGER,
                    new Integer (lowVelocity));
        propArr[6] = new Property ("HighVelocity", PropertyType.INTEGER,
                    new Integer (highVelocity));
        module.addWaveProperty (new Property ("Instrument",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    propArr));
        return true;
    }
}
