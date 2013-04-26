/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;
//import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the AIFF Saxel (Sound Accelerator) Chunk.
 * 
 * The Saxel chunk has only a tentative and incomplete status in the
 * AIFF-C draft of 1991, and apparently nothing further was
 * ever done with it.  For purposes of extracting parameters,
 * we treat the description of the SaxelChunk and Saxels as
 * valid, while regarding the SaxelData as opaque.
 *
 * @author Gary McGath
 *
 */
public class SaxelChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public SaxelChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a "Saxels" property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     * 
     */
    public boolean readChunk(RepInfo info) throws IOException {
        AiffModule module = (AiffModule) _module;
        int numSaxels = module.readUnsignedShort (_dstream);
        bytesLeft -= 2;
        if (numSaxels == 0) {
            return true;     // trivial case
        }
        // Create a List of properties
        for (int i = 0; i < numSaxels; i++) {
            // Multiple saxel chunks are allowed, of which
            // each can have multiple saxels.  We put them
            // all together into a single saxel list in
            // the module.
            Property[] propArr = new Property[2];
            int id = module.readUnsignedShort (_dstream);
            int size = module.readUnsignedShort (_dstream);
            // Just skip the actual data.
            module.skipBytes (_dstream, size, module);
            
            // Build the property to add to the saxel list.
            propArr[0] = new Property ("ID",
                    PropertyType.INTEGER,
                    new Integer (id));
            propArr[1] = new Property ("Size",
                    PropertyType.INTEGER,
                    new Integer (size));
            module.addSaxel (new Property ("Saxel",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    propArr));
                    
        }
        return true;
    }

}
