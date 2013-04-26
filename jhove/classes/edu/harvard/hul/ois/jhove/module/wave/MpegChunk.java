/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.IOException;

import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
import java.util.*;

/**
 * Implementation of the WAVE MPEG Audio Extension Chunk.
 *
 * @author Gary McGath
 *
 */
public class MpegChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public MpegChunk (
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts an MPEG Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        int soundInformation = module.readUnsignedShort(_dstream);
        int frameSize = module.readUnsignedShort (_dstream);
        int ancillaryDataLength = module.readUnsignedShort (_dstream);
        int ancillaryDataDef = module.readUnsignedShort (_dstream);
        module.skipBytes (_dstream, 4, module);     // reserved
        
        List propList = new ArrayList ();
        propList.add (module.buildBitmaskProperty(soundInformation,
                "SoundInformation",
                WaveStrings.SOUND_INFORMATION_1,
                WaveStrings.SOUND_INFORMATION_0));
        propList.add (new Property ("FrameSize",
                PropertyType.INTEGER,
                new Integer (frameSize)));
        propList.add (new Property ("AncillaryDataLength",
                PropertyType.INTEGER,
                new Integer (ancillaryDataLength)));
        propList.add (module.buildBitmaskProperty(ancillaryDataDef,
                "AncillaryDataDef",
                WaveStrings.ANCILLARY_DEF_1,
                WaveStrings.ANCILLARY_DEF_0));
        module.addWaveProperty (new Property ("MPEG",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList));
        return true;
    }

}
