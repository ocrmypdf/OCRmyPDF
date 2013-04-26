/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;
import java.io.*;
import java.util.*;

/**
 * Encapsulation of a JPEG 2000 codestream.
 * 
 * This is based on the information in Appendix A of
 * ISO/IEC 15444-1:2000(E).  That standard "does not 
 * include a definition of compliance or conformance."
 * 
 * @author Gary McGath
 *
 */
public class ContCodestream {
    
    private Codestream _codestream;
    private long _length;
    private Jpeg2000Module _module;
    private DataInputStream _dstream;
//    private List _tileParts;
    private List<Tile> _tiles;
    private long _tileLeft;
    
    /* Tile for which we have most recently seen an unclosed SOT */
    private Tile _curTile;
    
    /* Set to true when a PPM marker segment is found */
    private boolean ppmSeen;
    
    /* Constants defining codestream markers */
    private final static int
        SOC = 0X4F,             // start of codestream
        COD = 0X52,             // coding style default
        COC = 0X53,             // coding style component
        TLM = 0X55,             // tile-part lengths
        PLM = 0X57,             // packet length, main header
        PLT = 0X58,             // packet length, tile-part header
        QCD = 0X5C,             // quantization default
        QCC = 0X5D,             // quantization component
        RGN = 0X5E,             // region of interest
        POC = 0X5F,             // progression order change
        PPM = 0X60,             // Packed packet headers, main header
        PPT = 0X61,             // packed packet headers, tile-part header
        CRG = 0X63,             // component registration
        COM = 0X64,             // comment
        SOT = 0X90,             // start of tile part
        SOP = 0X91,             // start of packet
        EPH = 0X92,             // end of packet header
        SOD = 0X93,             // start of data
        EOC = 0XD9,             // end of codestream
        SIZ = 0X51;             // image and tile size
    
    /**
     *  Constructor.
     * 
     *  @param length   Length of the codestream, exclusive of the
     *                  box header.  If the codestream box has a length
     *                  field of 0, pass 0 for this parameter.
     */
    public ContCodestream (Jpeg2000Module module, 
            DataInputStream dstream,
            long length)
    {
        _module = module;
        _dstream = dstream;
        _length = length;
        _tiles = new LinkedList<Tile> ();
        //_tileParts = new LinkedList ();   // Do I want both lists?
        ppmSeen = false;
    }



    /** Reading a codestream generates various bits of information about
     *  the image.  These are made available after reading through
     *  accessor functions.
     * 
     *  @param   cs     The image which this codestream defines.
     *                  Must have a non-null <code>codestream</code> 
     *                  field.
     *  
     *  @param   info   The RepInfo object which accumulates information
     *                  about the document.  Used for reporting errors.
     * 
     *  @return  True if no fatal errors detected, 
     *           false if error prevents safe continuation
     */
    public boolean readCodestream (Codestream cs, RepInfo info) 
                throws IOException
    {
        final String badStream = "Ill-formed codestream";
        _codestream = cs;
        long lengthLeft = _length;
        _tileLeft = 0;
        boolean socSeen = false;  // flag to note an SOC marker has been seen
        
        // length may be 0, signifying that we go till EOF
        if (lengthLeft == 0) {
            lengthLeft = Long.MAX_VALUE;
        }
        try {
            while (lengthLeft > 0) {
                // "Marker segments" are followed by a length parameter,
                // but "markers" aren't.  
                int ff = ModuleBase.readUnsignedByte (_dstream, _module);
                if (ff != 0XFF) {
                    info.setMessage (new ErrorMessage (badStream));
                    info.setWellFormed (false);
                    return false;
                }
                int marker = ModuleBase.readUnsignedByte (_dstream, _module);
                if (marker == 0X4F) {
                    // we got the SOC marker, as expected
                    socSeen = true;
                }
                MarkerSegment ms = MarkerSegment.markerSegmentMaker (marker);
                ms.setCodestream (cs);
                ms.setContCodestream (this);
                ms.setDataInputStream (_dstream);
                ms.setRepInfo (info);
                ms.setModule (_module);
                int markLen = ms.readMarkLen ();
                if (!ms.process (markLen == 0 ? 0 : markLen - 2)) {
                    info.setMessage (new ErrorMessage 
                        ("Invalid marker segment"));
                        info.setWellFormed (false);
                        return false;
                }
                // markLen includes the marker length bytes, 
                // but not the marker bytes
   
                if (!(ms instanceof Marker)) {
                    lengthLeft -= markLen + 2;
                    // Count down on the bytes in a tile if we're in one
                    if (_tileLeft > 0) {
                        _tileLeft -= markLen + 2;
                    }
                }
                else {
                    // It's a plain marker -- no length data.
                    lengthLeft -= 2;
                    if (_tileLeft > 0) {
                        _tileLeft -= 2;
                    }
                    if (marker == SOD) {
                        // 0X93 is SOD, which is followed by a bitstream.
                        // We skip the number of bytes not yet deducted from _tileLeft
                        _module.skipBytes (_dstream, (int) _tileLeft, _module);
                        lengthLeft -= _tileLeft;
                        _tileLeft = 0;
                    }
                    else if (marker == EOC) {
                        break;      // end of codestream
                    }
                }
            }
        }
        catch (EOFException e) {
            // we're done
        }
        if (!socSeen) {
            info.setMessage (new ErrorMessage (badStream));
            info.setWellFormed (false);
            return false;
        }
        _codestream.setTiles (_tiles);
        return true;
    }
    
    
    /** Returns the list of tiles.  The elements are Tile objects. */
    public List<Tile> getTiles ()
    {
        return _tiles;
    }
    
    /** Set the number of bytes remaining in the current tile.
     *  For use by MarkerSegment subclasses.
     */
    protected void setTileLeft (long tileLeft)
    {
        _tileLeft = tileLeft;
    }



    
    /** Gets the tile whose index is idx. */
    protected Tile getTile (int idx)
    {
        // If we haven't reached this index before, add a tile.
        // Tiles are supposed to be added sequentially, but
        // PIAV.
        while (_tiles.size () <= idx) {
            _tiles.add (new Tile ());
        }
        return (Tile) _tiles.get (idx);
    }
    
    /** Sets the value of curTile. */
    protected void setCurTile (Tile tile)
    {
        _curTile = tile;
    }
    
    /** Sets the value of the ppmSeen flag, signifying that
     *  a PPM marker segment has been encountered. */
    protected void setPPMSeen (boolean b)
    {
        ppmSeen = b;
    }
    
    
    /** Gets the value of curTile.  May be null. */
    protected Tile getCurTile ()
    {
        return _curTile;
    }
    
    /** Returns the value of the ppmSeen flag, signifying that
     *  a PPM marker segment has been encountered. */
    protected boolean isPPMSeen ()
    {
        return ppmSeen;
    }

    
    /* Based on marker code, return true if this is a marker
     * segment (i.e., it has parameters).  The documentation
     * isn't fully clear, but I think the only way to determine
     * what is a marker is to enumerate all values that are
     * markers. */
    private static boolean isSegment (int marker) 
    {
        if ((marker >= 0X30 && marker <= 0X3F) ||
                marker == SOC ||       // start of codestream
                marker == EPH ||       // end of packet header
                marker == SOD ||       // start of data
                marker == EOC) {       // end of codestream
            return false;
        }
        return true;
    }
}
