/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;
import java.util.*;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * 
 * This implements any of the subchunks of the ListInfoChunk
 * (a LIST chunk with a list type of INFO).
 * All such chunks are identical in format, consisting of a
 * null-terminated string.  About 17 chunk ID's are recognized;
 * others will be ignored.
 * 
 * @author Gary McGath
 *
 */
public class ListInfoTextChunk extends Chunk {

    private ListInfoChunk _parent;
    private List _listInfoProps;
    String _chunkID;
    
    /**
     * Constructor.
     * 
     * @param module        The WaveModule under which this was called
     * @param hdr           The header for this chunk
     * @param dstrm         The stream from which the WAVE data are being read
     * @param listInfoProps A List of the Properties associated with the
     *                      ListInfoChunk
     * @param parent        The ListInfoChunk within which this Chunk occurs
     */
    public ListInfoTextChunk(
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm,
            List listInfoProps,
            ListInfoChunk parent) {
        super(module, hdr, dstrm);
        _parent = parent;
        _chunkID = hdr.getID ();
        _listInfoProps = listInfoProps;
    }


    /** Reads a chunk and.....
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, module);
        String txt = new String (buf);
        txt = txt.trim ();    // remove trailing null
        String propName = null;
        
        // Add the string to the property list if we can identify it.
        if ("IARL".equals (_chunkID)) {
            propName = "ArchivalLocation";
        }
        else if ("IART".equals (_chunkID)) {
            propName = "Artist";
        }
        else if ("ICMS".equals (_chunkID)) {
            propName = "Commissioned";
        }
        else if ("ICMT".equals (_chunkID)) {
            propName = "Comments";
        }
        else if ("ICOP".equals (_chunkID)) {
            propName = "Copyright";
        }
        else if ("ICRD".equals (_chunkID)) {
            propName = "CreationDate";
        }
        else if ("ICRP".equals (_chunkID)) {
            propName = "Cropped";
        }
        else if ("IDIM".equals (_chunkID)) {
            propName = "Dimensions";
        }
        else if ("IDPI".equals (_chunkID)) {
            propName = "DotsPerInch";
        }
        else if ("IENG".equals (_chunkID)) {
            propName = "Engineer";
        }
        else if ("IGNR".equals (_chunkID)) {
            propName = "Genre";
        }
        else if ("IKEY".equals (_chunkID)) {
            propName = "Keywords";
        }
        else if ("ILGT".equals (_chunkID)) {
            propName = "Lightness";
        }
        else if ("IMED".equals (_chunkID)) {
            propName = "Medium";
        }
        else if ("INAM".equals (_chunkID)) {
            propName = "Name";
        }
        else if ("IPLT".equals (_chunkID)) {
            propName = "PaletteSetting";
        }
        else if ("IPRD".equals (_chunkID)) {
            propName = "Product";
        }
        else if ("ISBJ".equals (_chunkID)) {
            propName = "Subject";
        }
        else if ("ISFT".equals (_chunkID)) {
            propName = "Software";
        }
        else if ("ISHP".equals (_chunkID)) {
            propName = "Sharpness";
        }
        else if ("ISRC".equals (_chunkID)) {
            propName = "Source";
        }
        else if ("ISRF".equals (_chunkID)) {
            propName = "SourceForm";
        }
        else if ("ITCH".equals (_chunkID)) {
            propName = "Technician";    // making this a scratch file?
        }
        if (propName != null) {
            _listInfoProps.add (new Property (propName,
                    PropertyType.STRING, txt));
        }
        else {
            info.setMessage (new InfoMessage
                ("Chunk type '" + _chunkID + "' in List Info Chunk ignored"));
        }
        return true;
    }

}
