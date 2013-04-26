/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;
//import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;

/**
 * Class for the SOT (start of tile-part) marker segment.
 * 
 * @author Gary McGath
 *
 */
public class SOTMarkerSegment extends MarkerSegment {

    /**
     * Constructor
     * 
     */
    public SOTMarkerSegment() 
    {
    }


    /** Process the marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     */
    protected boolean process (int bytesToEat) throws IOException
    {
        int tileIndex = _module.readUnsignedShort (_dstream);
        long tileLeft = _module.readUnsignedInt (_dstream);
        _ccs.setTileLeft (tileLeft);
        int tilePartIndex = 
                ModuleBase.readUnsignedByte (_dstream, _module);
        int numTileParts = 
                ModuleBase.readUnsignedByte (_dstream, _module);
        
        Tile tile = _ccs.getTile (tileIndex);
        _ccs.setCurTile (tile);
        TilePart tp = new TilePart (tile, tilePartIndex);
        tile.addTilePart (tp);
        tp.setLength (tileLeft);
        // Shouldn't be anything left, but...
        if (bytesToEat > 8) {
            _module.skipBytes (_dstream, bytesToEat - 8, _module);
        }
        return true;
    }



}
