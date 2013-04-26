/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;
import java.util.*;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Implementation of the WAVE LIST chunk.
 * 
 * Two chunk types, 'exif' and 'INFO', are supported;
 * other list types will be reported as unknown
 * and treated as an error.  
 *
 * @author Gary McGath
 *
 */
public class ListInfoChunk extends Superchunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     * @param info     RepInfo object for error reporting
     */
    public ListInfoChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm,
        RepInfo info) {
        super(module, hdr, dstrm, info);
    }

    /** Reads a chunk and puts appropriate information into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     * 
     */
    public boolean readChunk(RepInfo info) throws IOException 
    {
        boolean isInfo = false;
        boolean isExif = false;
        String typeID = ((WaveModule) _module).read4Chars(_dstream);
        bytesLeft -= 4;
        if ("INFO".equals (typeID)) {
            return readInfoChunk (info);
        }
        else if ("exif".equals (typeID)) {
            return readExifChunk (info);
        }
        else if ("adtl".equals (typeID)) {
            return readAdtlChunk (info);
        }
        else {
            info.setMessage (new ErrorMessage ("Unknown list type " +
                    typeID + " in List Chunk", 
                    _module.getNByte()));
            info.setWellFormed (false);
            return false;
        }
    }

    private boolean readInfoChunk (RepInfo info) throws IOException
    {
        List listInfoProps = new LinkedList ();
        WaveModule module = (WaveModule) _module;
        // The set of subchunks is somewhat
        // open-ended, but apparently all are identical in format, consisting
        // of a null-terminated string.  These are subsumed under
        // ListInfoTextChunk.  We accumulate them into a List of Properties.
        for (;;) {
            ChunkHeader chunkh = getNextChunkHeader ();
            if (chunkh == null) {
                break;
            }
            Chunk chunk = null;
            String id = chunkh.getID();
            int chunkSize = (int) chunkh.getSize ();
            chunk = new ListInfoTextChunk (_module, chunkh, 
                        _dstream, listInfoProps, this);
            
            if (chunk == null) {
                _module.skipBytes (_dstream, (int) chunkSize, _module);
                info.setMessage (new InfoMessage
                    ("Chunk type '" + id + "' in List Info Chunk ignored"));
            }
            else {
                try {
                    if (!chunk.readChunk (info)) {
                        return false;
                    }
                }
                catch (JhoveException e) {
                    info.setMessage(new ErrorMessage (e.getMessage()));
                    info.setWellFormed (false);
                    return false;
                }
            }
            if ((chunkSize & 1) != 0) {
                // Must come out to an even byte boundary
                _module.skipBytes (_dstream, 1, _module);
                --bytesLeft;
            }
        }
        if (!listInfoProps.isEmpty ()) {
            module.addListInfo (listInfoProps);
        }
        return true;
    }

    /*  The Exif chunk, unlike the Info chunk, has subchunks which aren't
     *  homogeneous.  */
    private boolean readExifChunk (RepInfo info) throws IOException
    {
        List exifProps = new LinkedList ();
        WaveModule module = (WaveModule) _module;
        module.setExifInfo (new ExifInfo ());
        for (;;) {
            ChunkHeader chunkh = getNextChunkHeader ();
            if (chunkh == null) {
                break;
            }
            Chunk chunk = null;
            String id = chunkh.getID();
            int chunkSize = (int) chunkh.getSize ();
            
            if ("ever".equals (id)) {
                chunk = new ExifVersionChunk (_module, chunkh, _dstream);
            }
            else if ("erel".equals (id) ||
                     "etim".equals (id) ||
                     "ecor".equals (id) ||
                     "emdl".equals (id)) {
                chunk = new ExifStringChunk (_module, chunkh, _dstream);
            }
            else if ("emnt".equals (id)) {
                
            }
            else if ("eucm".equals (id)) {
            
            }
            if (chunk == null) {
                _module.skipBytes (_dstream, (int) chunkSize, _module);
                info.setMessage (new InfoMessage
                    ("Chunk type '" + id + "' in Associated Data Chunk ignored"));
            }
            else {
                try {
                    if (!chunk.readChunk (info)) {
                        return false;
                    }
                }
                catch (JhoveException e) {
                    info.setMessage(new ErrorMessage (e.getMessage()));
                    info.setWellFormed (false);
                    return false;
                }
            }
        }        
        return false;
    }

    /** Reads the chunk and its nested chunks, and puts appropriate
     *  properties into the RepInfo object.
     *
     *  @return   <code>false</code> if the chunk or a nested chunk
     *            is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readAdtlChunk(RepInfo info)
	throws IOException
    {
        WaveModule module = (WaveModule) _module;
       
        for (;;) {
            ChunkHeader chunkh = getNextChunkHeader ();
            if (chunkh == null) {
                break;
            }
            Chunk chunk = null;
            // The chunk list can include Labels, Notes, and
	    // Labelled Text.
            String id = chunkh.getID();
            int chunkSize = (int) chunkh.getSize ();
            if (id.equals ("labl")) {
                chunk = new LabelChunk (_module, chunkh, _dstream);
            }
            else if (id.equals ("note")) {
                chunk = new NoteChunk (_module, chunkh, _dstream);
            }
            else if (id.equals ("ltxt")) {
                chunk = new LabeledTextChunk (_module, chunkh, _dstream);
            }
           
            if (chunk == null) {
                _module.skipBytes (_dstream, (int) chunkSize, _module);
                info.setMessage (new InfoMessage ("Chunk type '" + id +
				  "' in Associated Data Chunk ignored"));
            }
            else {
                try {
                    if (!chunk.readChunk (info)) {
                        return false;
                    }
                }
                catch (JhoveException e) {
                    info.setMessage(new ErrorMessage (e.getMessage()));
                    info.setWellFormed (false);
                    return false;
                }
            }
            if ((chunkSize & 1) != 0) {
                // Must come out to an even byte boundary
                _module.skipBytes (_dstream, 1, _module);
                --bytesLeft;
            }
        }
        return true;
    }
}
