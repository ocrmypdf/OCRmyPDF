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
 * Implementation of the AIFF Application Chunk.
 *
 * @author Gary McGath
 *
 */
public class ApplicationChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public ApplicationChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts an Application property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException 
    {
        AiffModule module = (AiffModule) _module;
        String applicationSignature = module.read4Chars (_dstream);
        byte[] data = new byte[(int) (bytesLeft - 4)];
        ModuleBase.readByteBuf (_dstream, data, _module);
        Property[] propArr = new Property[2];
        propArr[0] = new Property ("ApplicationSignature",
                PropertyType.STRING,
                applicationSignature);
        AESAudioMetadata aes = module.getAESMetadata ();
        aes.setAppSpecificData(applicationSignature);
        // If the application signature is 'pdos' or 'stoc',
        // then the beginning of the data area is a Pascal
        // string naming the application.  Otherwise, we
        // just report the raw data.  ('pdos' is for Apple II
        // applications, 'stoc' for the entire non-Apple world.)
        if ("stoc".equals (applicationSignature) ||
                "pdos".equals (applicationSignature)) {
            String appName = module.readPascalString(_dstream);
            bytesLeft -= appName.length() + 1;
            module.skipBytes (_dstream, (int) bytesLeft, module);
            propArr[1] = new Property ("ApplicationName",
                PropertyType.STRING,
                appName);
        }
        else {
            propArr[1] = new Property ("Data",
                PropertyType.BYTE,
                PropertyArity.ARRAY,
                data);
        }
        module.addAiffProperty (new Property ("Application",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                propArr));
        
        return true;
    }

}
