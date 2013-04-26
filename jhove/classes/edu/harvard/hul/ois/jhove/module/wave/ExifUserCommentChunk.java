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
 * This class encapsulates the Exif User Comment chunk.
 *
 * @author Gary McGath
 *
 */
public class ExifUserCommentChunk extends Chunk {
    
    // 8-byte codes for encodings;  all the existing recognized
    // encodings are representable as ASCII strings with null
    // padding.  "UNICODE" doesn't specify whether it's UTF-8, 
    // UTF-16, or UTF-32.
    private final static String asciiDes = "ASCII";
    private final static String jisDes = "JIS";
    private final static String unicodeDes = "UNICODE";


    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public ExifUserCommentChunk(
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
    public boolean readChunk(RepInfo info) throws IOException 
    {
        WaveModule module = (WaveModule) _module;
        if (bytesLeft < 8) {
            info.setMessage (new ErrorMessage
                ("Exif User Comment Chunk is too short"));
            info.setWellFormed (false);
            return false;
        }
        // Read the 8-byte encoding designation.
        byte[] buf = new byte[8];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String encoding = new String (buf).trim ();
        bytesLeft -= 8;
        
        String charset = null;
        
        // Here we have to do some guessing if the character set isn't
        // ASCII.  There are three different Unicode encodings and
        // even more JIS variants.
        if (asciiDes.equals (encoding)) {
            charset = "US-ASCII";
        }
        else if (jisDes.equals (encoding)) {
            charset = "EUC_JP";
        }
        else if (unicodeDes.equals (encoding)) {
            charset = "UTF-16";
        }
        // Read the comment itself.
        buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String text = null;
        try {
            if (charset != null) {
                text = new String (buf, charset);
            }
        }
        catch (Exception e) {
            // If we can't decode the charset, punt to default.
        }
        if (text == null) {
            text = new String (buf);
        }
        ExifInfo exif = module.getExifInfo ();
        module.getExifInfo ().setUserComment (text);
        return true;
    }
}
