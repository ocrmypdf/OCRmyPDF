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
 * Class for encapsulating Exif chunks whose content consists of
 * a null-terminated ASCII string.  
 *
 * @author Gary McGath
 *
 */
public class ExifStringChunk extends Chunk {

    private String id;


    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public ExifStringChunk(
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
        id = hdr.getID();
    }

    /** Reads a chunk and puts information into the superchunk's
     *  Exif property. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String txt = new String (buf).trim ();
        ExifInfo exif = module.getExifInfo ();
        if ("erel".equals (id)) {
            exif.setRelatedImageFile(txt);
        }
        else if ("etim".equals (id)) {
            exif.setTimeCreated (txt);
        }
        else if ("ecor".equals (id)) {
            exif.setManufacturer(txt);
        }
        else if ("emdl".equals (id)) {
            exif.setModel (txt);
        }
        module.getExifInfo ().setRelatedImageFile(txt);
        return true;
    }

}
