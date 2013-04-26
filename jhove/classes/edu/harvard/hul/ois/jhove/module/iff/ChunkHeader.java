/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.iff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * This class encapsulates an IFF/AIFF chunk header.
 * 
 * @author Gary McGath
 *
 */
public class ChunkHeader {

    private ModuleBase _module;
    private RepInfo _repInfo;
    private long _size;              // This does not include the 8 bytes of header
    private String _chunkID;         // 4-character ID of the chunk
    
    /**
     *  Constructor.
     * 
     *  @param  module   The module under which the chunk is being read
     *  @param  info     The RepInfo object being used by the module
     */
    public ChunkHeader (ModuleBase module, RepInfo info)
    {
        _module = module;
        _repInfo = info;
    }
    
    
    /**
     *  Reads the header of a chunk.  If _chunkID is non-null,
     *  it's assumed to have already been read.
     */
    public boolean readHeader (DataInputStream dstrm) throws IOException
    {
        StringBuffer id = new StringBuffer(4);
        for (int i = 0; i < 4; i++) {
            int ch = ModuleBase.readUnsignedByte (dstrm, _module);
            if (ch < 32) {
                String hx = Integer.toHexString (ch);
                if (hx.length () < 2) {
                    hx = "0" + hx;
                }
                _repInfo.setMessage (new ErrorMessage
                    ("Invalid character in Chunk ID",
                     "Character = 0x" + hx,
                     _module.getNByte ()));
                _repInfo.setWellFormed (false);
                return false;
            }
            id.append((char) ch);
        }
        _chunkID = id.toString ();
        _size = ModuleBase.readUnsignedInt (dstrm, _module.isBigEndian (), _module); 
        return true;
    }
    
    
    /** Sets the chunk type, which is a 4-character code, directly. */
    public void setID (String id)
    {
        _chunkID = id;
    }
    
    /** Returns the chunk type, which is a 4-character code */
    public String getID ()
    {
        return _chunkID;
    }
    
    /** Returns the chunk size (excluding the first 8 bytes) */
    public long getSize ()
    {
        return _size;
    }
}
