/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the TLM (tile length) marker segment.
 * This may occur only in the main header.
 * 
 * @author Gary McGath
 *
 */
public class TLMMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public TLMMarkerSegment() {
        super();
    }

    /**
     * Processes the marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     */
    protected boolean process(int bytesToEat) throws IOException {
        int ztlm = ModuleBase.readUnsignedByte (_dstream, _module);
        int stlm = ModuleBase.readUnsignedByte (_dstream, _module);
        int st = (stlm & 0X30) >> 4;
        int sp = (stlm & 0X40) >> 6;
        
        int partLength = (sp == 1) ? 4 : 2;
        switch (st) {
            // case 0: add nothing
            case 1:
            partLength += 1;
            break;
            case 2:
            partLength += 2;
            break;
            case 3:
            _repInfo.setMessage (new ErrorMessage ("Invalid ST value in TLM marker segment"));
            return false;      // invalid st value
        }
        
        int nParts = (bytesToEat - 2) / partLength;
        // Make sure it's an even multiple
        if (nParts * partLength != bytesToEat - 2) {
            return false;
        }
        if (_ccs.getCurTile () != null) {
            return false;      // not permitted in a tile
        }
        for (int i = 0; i < nParts; i++) {
            List<Property> tpList = new ArrayList<Property> (2);
            // The TileIndex property is given only if st != 0
            if (st != 0) {
                int ttlm;
                if (st == 1) {
                    ttlm = ModuleBase.readUnsignedByte (_dstream, _module);
                }
                else {
                    ttlm = _module.readUnsignedShort (_dstream);
                }
                tpList.add (new Property ("Index",
                            PropertyType.INTEGER,
                            new Integer (ttlm)));
            }
            int length;
            if (sp == 1) {
                length = (int) _module.readUnsignedInt (_dstream);
            }
            else {
                length = (int) _module.readUnsignedShort (_dstream);
            }
            tpList.add (new Property ("Length",
                            PropertyType.INTEGER,
                            new Integer (length)));
            _cs.addTileLength (new Property ("TilePartLength",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            tpList));
        }
        return true;
    }

}
