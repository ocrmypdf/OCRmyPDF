/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the AIFF MIDI Chunk.
 *
 * @author Gary McGath
 *
 */
public class MidiChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public MidiChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts an MIDI property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        AiffModule module = (AiffModule) _module;
        if (bytesLeft == 0) {
            return true;    // dubious, but call it legal
        }
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, _module);
        module.addMidi (new Property ("MIDI",
                    PropertyType.BYTE,
                    PropertyArity.ARRAY,
                    buf));
        return true;
    }

}
