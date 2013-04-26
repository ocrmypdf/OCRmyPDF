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
 * Implementation of the AIFF Audio Recording Chunk.
 *
 * The data bytes are put into an uninterpreted byte array
 * Property.  These are specified in the AES Recommended
 * Practice for Digital Audio Engineering - Serial Transmission 
 * Format for Linearly Represented Digital Audio Data, 
 * Section 7.1, Channel Status Data.
 * 
 * @author Gary McGath
 *
 */
public class AudioRecChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public AudioRecChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts an AudioRecording property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        AiffModule module = (AiffModule) _module;
        if (bytesLeft != 24) {
            // This chunk must always have exactly 24 bytes data
            info.setMessage (new ErrorMessage
                    ("Audio Recording Chunk is incorrect size",
                     module.getNByte ()));
            info.setWellFormed (false);
            return false;
        }
        byte[] buf = new byte[24];
        ModuleBase.readByteBuf (_dstream, buf, module);
        module.addAiffProperty (new Property ("AudioRecording",
                PropertyType.BYTE,
                PropertyArity.ARRAY,
                buf));
        return true;
    }

}
