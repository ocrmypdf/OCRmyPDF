/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;
import java.io.*;

/**
 * Chunk for Exif version information.
 * This chunk may occur only within a LIST chunk of type
 * "exif".
 *
 * @author Gary McGath
 *
 */
public class ExifVersionChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public ExifVersionChunk(
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts information into the superchunk's
     *  Exif property. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        if (bytesLeft != 4) {
            info.setMessage (new ErrorMessage
                ("Incorrect length for Exif Version Chunk"));
            info.setWellFormed (false);
            return false;
        }
        byte[] buf = new byte[4];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String txt = new String (buf);
        module.getExifInfo ().setExifVersion(txt);
        return true;
    }

}
