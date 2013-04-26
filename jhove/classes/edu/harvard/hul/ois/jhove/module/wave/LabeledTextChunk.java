/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * 
 * The Labelled Text Chunk, which can occur only in an Associated Data
 * List.
 * 
 * @author Gary McGath
 *
 */
public class LabeledTextChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public LabeledTextChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) 
    {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts an MPEG Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException 
    {
        WaveModule module = (WaveModule) _module;
        long cuePointID = module.readUnsignedInt (_dstream);
        long sampleLength = module.readUnsignedInt (_dstream);
        long purposeID = module.readUnsignedInt (_dstream);
        int country = module.readUnsignedShort (_dstream);
        int language = module.readUnsignedShort (_dstream);
        int dialect = module.readUnsignedShort (_dstream);
        int codePage = module.readUnsignedShort (_dstream);
        byte[] buf = new byte[(int) (bytesLeft - 20)];
        ModuleBase.readByteBuf(_dstream, buf, module);
        String text = new String (buf).trim ();
        
        // Make the information into a Property.
        List plist = new ArrayList (10);
        plist.add (new Property ("CuePointID", PropertyType.LONG,
                new Long (cuePointID)));
        plist.add (new Property ("SampleLength", PropertyType.LONG,
                new Long (sampleLength)));
        plist.add (new Property ("PurposeID", PropertyType.LONG,
                new Long (purposeID)));
        plist.add (new Property ("Country", PropertyType.INTEGER,
                new Integer (country)));
        plist.add (new Property ("Language", PropertyType.INTEGER,
                new Integer (language)));
        plist.add (new Property ("Dialect", PropertyType.INTEGER,
                new Integer (dialect)));
        plist.add (new Property ("CodePage", PropertyType.INTEGER,
                new Integer (codePage)));
        plist.add (new Property ("Text", PropertyType.STRING,
                text));
        module.addLabeledText(new Property ("LabeledTextItem",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                plist));
        return true;
    }
}
