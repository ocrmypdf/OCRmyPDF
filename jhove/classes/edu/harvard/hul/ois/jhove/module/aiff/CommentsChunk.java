/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Implementation of the AIFF Comments Chunk.
 *
 * @author Gary McGath
 *
 */
public class CommentsChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public CommentsChunk (AiffModule module, ChunkHeader hdr,
			  DataInputStream dstrm)
    {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a Comments property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info)
	throws IOException
    {
        AiffModule module = (AiffModule) _module;
        int numComments = module.readUnsignedShort (_dstream);
        bytesLeft -= 2;
        if (numComments == 0) {
            return true;     // trivial case
        }
        // Create a List of comment properties
        List<Property> comments = new ArrayList<Property> (numComments);
        for (int i = 0; i < numComments; i++) {
            long timestamp = module.readUnsignedInt (_dstream);
            Date jTimestamp = module.timestampToDate (timestamp);
            int marker = module.readSignedShort (_dstream);
            int count = module.readUnsignedShort (_dstream);
            bytesLeft -= 8;
            byte[] buf = new byte[count];
            ModuleBase.readByteBuf(_dstream, buf, module);
            bytesLeft -= count;
            /* Ensure that each byt is a printable ASCII character. */
            for (int j=0; j<buf.length; j++) {
                if (buf[j] < 32 || buf[j] > 127) {
                    buf[j] = 32;
                }
            }
            String comment = new String (buf, "ASCII");
            
            // Build the property for one comment
            Property[] comAr = new Property[2];
            comAr[0] = new Property ("Timestamp",
                        PropertyType.DATE,
                        jTimestamp);
            comAr[1] = new Property ("CommentText",
                        PropertyType.STRING,
                        comment);
            comments.add (new Property ("Comment",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        comAr));
        }
        module.addAiffProperty(new Property ("Comments",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        comments));

        return true;
    }
}
