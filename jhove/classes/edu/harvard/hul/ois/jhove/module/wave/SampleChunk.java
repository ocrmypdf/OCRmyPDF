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
 * Implementation of the WAVE Sample (or Sampler) Chunk, which
 * gives information about a MIDI sample.
 *
 * @author Gary McGath
 *
 */
public class SampleChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public SampleChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a Sample property into
     *  the RepInfo object. 
     * 
     *  It isn't clear whether multiple
     *  Sample chunks are allowed (representing different sound samples
     *  for different notes or note ranges).  This module assumes
     *  they are, so it constructs a Samples property, consisting
     *  of a list of Sample properties.
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        // read MMA manufacturer and product codes (which we probably won't
        // try to resolve)
        long manufacturer = module.readUnsignedInt (_dstream);
        long product = module.readUnsignedInt (_dstream);
        // sample time in nanoseconds
        long samplePeriod = module.readUnsignedInt (_dstream);
        // read midi unity note (1-127, so why does it get 4 bytes?)
        long unityNote = module.readUnsignedInt (_dstream);
        // MIDI pitch fraction.  This is apparently a fixed-point
        // number representing a value between 0 and 1.
        long pitchFraction = module.readUnsignedInt (_dstream);
        // Get SMPTE format.  Maximum value is 30, but it also gets 4 bytes.
        long smpteFormat = module.readUnsignedInt (_dstream);
        // SMPTE offset consists of four values in a confusing mix
        // of signed and unsigned data.  The web page I'm working from
        // says the frame offset is an unsigned value from 0 to -1.
        int sampleOffsetHour = ModuleBase.readSignedByte (_dstream, module);
        int sampleOffsetMinute = ModuleBase.readUnsignedByte (_dstream, module);
        int sampleOffsetSecond = ModuleBase.readUnsignedByte (_dstream, module);
        int sampleOffsetFrames = ModuleBase.readSignedByte (_dstream, module);
                     // Or should it be unsigned??
        Property[] smpteArr = new Property[4];
        smpteArr[0] = new Property ("Hour", PropertyType.INTEGER,
                new Integer (sampleOffsetHour));
        smpteArr[1] = new Property ("Minute", PropertyType.INTEGER,
                new Integer (sampleOffsetMinute));
        smpteArr[2] = new Property ("Second", PropertyType.INTEGER,
                new Integer (sampleOffsetSecond));
        smpteArr[3] = new Property ("Frames", PropertyType.INTEGER,
                new Integer (sampleOffsetFrames));

        int nLoops = (int) module.readUnsignedInt (_dstream);
        long extraBytes = module.readUnsignedInt (_dstream);  // no. of extra bytes after loops
        
        // Build an array of loop properties
        Property[] loopProps = new Property[nLoops];
        for (int i = 0; i < nLoops; i++) {
            long cuePoint = module.readUnsignedInt (_dstream);
            int type = (int) module.readUnsignedInt (_dstream);
            int start = (int) module.readUnsignedInt (_dstream);
            int end = (int) module.readUnsignedInt (_dstream);
            long fraction = module.readUnsignedInt (_dstream);
            long playCount = module.readUnsignedInt (_dstream);
            
            // Build the loop property.
            Property[] lp = new Property[6];
            lp[0] = new Property ("CuePointID", PropertyType.LONG,
                    new Long (cuePoint));
            lp[1] = new Property ("Type", PropertyType.INTEGER,
                    new Integer (type));
            lp[2] = new Property ("Start", PropertyType.INTEGER,
                    new Integer (start));
            lp[3] = new Property ("End", PropertyType.INTEGER,
                    new Integer (end));
            lp[4] = new Property ("Fraction", PropertyType.LONG,
                    new Long (fraction));
            lp[5] = new Property ("PlayCount", PropertyType.LONG,
                    new Long (playCount));
            loopProps[i] = new Property ("Loop",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    lp);
        }
        
        Property[] propArr = new Property[9];
        propArr[0] = new Property ("Manufacturer", PropertyType.LONG,
                    new Long (manufacturer));
        propArr[1] = new Property ("Product", PropertyType.LONG,
                    new Long (product));
        propArr[2] = new Property ("SamplePeriod", PropertyType.LONG,
                    new Long (samplePeriod));
        propArr[3] = new Property ("UnityNote", PropertyType.LONG,
                    new Long (unityNote));
        propArr[4] = new Property ("PitchFraction", PropertyType.LONG,
                    new Long (pitchFraction));
        propArr[5] = new Property ("SMPTEFormat", PropertyType.LONG,
                    new Long (smpteFormat));
        propArr[6] = new Property ("SMPTEOffset", PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    smpteArr);
        propArr[7] = new Property ("Loops", PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    loopProps);
        propArr[8] = new Property ("ExtraDataBytes", PropertyType.LONG,
                    new Long (extraBytes));
        module.addSample (new Property ("Sample",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    propArr));
        // Skip the extra data bytes that follow
        // the loop data.
        module.skipBytes (_dstream, (int) extraBytes, _module);
        
        
        return true;
    }
}
