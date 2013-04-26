/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;
import java.util.*;
import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Implementation of the AIFF Instrument Chunk.
 *
 * @author Gary McGath
 *
 */
public class InstrumentChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public InstrumentChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts an Instrument property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException 
    {
        AiffModule module = (AiffModule) _module;
        int baseNote = ModuleBase.readUnsignedByte (_dstream, module);
        int detune = ModuleBase.readSignedByte (_dstream, module);
        int lowNote = ModuleBase.readUnsignedByte (_dstream, module);
        int highNote = ModuleBase.readUnsignedByte (_dstream, module);
        int lowVelocity = ModuleBase.readUnsignedByte (_dstream, module);
        int highVelocity = ModuleBase.readUnsignedByte (_dstream, module);
        int gain = module.readSignedShort (_dstream);
        Loop sustainLoop = readLoop (module);
        Loop releaseLoop = readLoop (module);
        
        List propList = new ArrayList (9);
        propList.add (new Property ("BaseNote",
                PropertyType.INTEGER,
                new Integer (baseNote)));
        propList.add (new Property ("Detune",
                PropertyType.INTEGER,
                new Integer (detune)));
        propList.add (new Property ("LowNote",
                PropertyType.INTEGER,
                new Integer (lowNote)));
        propList.add (new Property ("HighNote",
                PropertyType.INTEGER,
                new Integer (highNote)));
        propList.add (new Property ("LowVelocity",
                PropertyType.INTEGER,
                new Integer (lowVelocity)));
        propList.add (new Property ("HighVelocity",
                PropertyType.INTEGER,
                new Integer (highVelocity)));
        propList.add (new Property ("Gain",
                PropertyType.INTEGER,
                new Integer (gain)));
        propList.add (sustainLoop.loopProp("SustainLoop"));
        propList.add (releaseLoop.loopProp("ReleaseLoop"));
        module.addAiffProperty(new Property ("Instrument",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList));
        return true;
    }


    private Loop readLoop (AiffModule module) throws IOException
    {
        int playMode = module.readSignedShort(_dstream);
        int beginLoop = module.readUnsignedShort (_dstream);
        int endLoop = module.readUnsignedShort (_dstream);
        return new Loop (playMode, beginLoop, endLoop);
    }
    
    
    /* Local class for encapsulating the Loop structure */
    private class Loop {
        public int playMode;
        public int beginLoop;
        public int endLoop;
        
        public Loop (int playMode, int beginLoop, int endLoop)
        {
            this.playMode = playMode;
            this.beginLoop = beginLoop;
            this.endLoop = endLoop;
        }
        
        public Property loopProp (String name)
        {
            Property[] propArr = new Property[3];
            propArr[0] = _module.addIntegerProperty("PlayMode", playMode,
                    AiffStrings.LOOP_TYPE);
            propArr[1] = new Property ("BeginLoop",
                    PropertyType.INTEGER,
                    new Integer (beginLoop));
            propArr[2] = new Property ("EndLoop",
                    PropertyType.INTEGER,
                    new Integer (endLoop));
            return new Property (name,
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    propArr);
        }
    }
}
