/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
//import java.util.*;

/**
 * Implementation of the WAVE AXML Chunk, which
 * contains arbitrary XML metadata, as specified in
 * <cite>Specification of the Broadcast Wave Format:
 * A format for audio data files in broadcasting;
 * Supplement 5: &lt;axml&gt; Chunk</cite>
 * (European Broadcasting Union)
 *
 * @author Gary McGath
 *
 */
public class AXMLChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public AXMLChunk (
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts a BroadcastAudioExtension Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        byte[] bbuf = new byte[(int) bytesLeft];
                
        ModuleBase.readByteBuf (_dstream, bbuf, _module);
        String xmlData = new String (bbuf);
        module.addWaveProperty (new Property ("XML", 
                PropertyType.STRING,
                xmlData));
        return true;
    }
}
