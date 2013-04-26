/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.*;
//import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Superclass for the very similar Note and Label chunks.
 *
 * @author Gary McGath
 *
 */
public abstract class SimpleTextChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public SimpleTextChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads the text item, and returns a Property containing the
     * cue point ID and the text. */
    protected Property readTextProp (WaveModule module, String propName) 
                    throws IOException
    {
        long cueID = module.readUnsignedInt (_dstream);
        bytesLeft -= 4;
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String txt = new String (buf);
        Property[] propArr = new Property[2];
        propArr[0] = new Property ("CuePointID",
                PropertyType.LONG,
                new Long (cueID));
        propArr[1] = new Property ("Text",
                PropertyType.STRING,
                txt);
        return new Property (propName,
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                propArr); 
    }

}
