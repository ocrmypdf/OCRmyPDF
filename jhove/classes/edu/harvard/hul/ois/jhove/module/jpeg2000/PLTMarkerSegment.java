/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
//import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the PLT Marker segment. This gives packet lengths at
 * the tile level. 
 *
 * @author Gary McGath
 *
 */
public class PLTMarkerSegment extends MarkerSegment {

    /**
     * Constructor.
     */
    public PLTMarkerSegment() {
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
        Tile tile = _ccs.getCurTile ();
        if (tile == null) {
            _repInfo.setMessage (new ErrorMessage
                    ("PLT marker segment not allowed in codestream header"));
            return false;    // a tile (SOT) is required
        }
        int zplt = ModuleBase.readUnsignedByte (_dstream, _module);
        --bytesToEat;
        // As with PLM, each iplt can have a different 
        // length.  This allows unlimited packet lengths --
        // or to be exact, the maximum length is 2 ^ (7 * 255) if there's
        // only one packet.  For this implementation, we limit the maximum
        // packet length to 2 ^ 63.
        while (bytesToEat > 0) {
            long pktLen = 0;
            for (;;) {
                int pkByte = ModuleBase.readUnsignedByte (_dstream, _module);
                if (--bytesToEat < 0) {
                    // bytes of a number can't cross marker segment boundaries
                    _repInfo.setMessage (new ErrorMessage
                            ("Packet length in PLT marker segment crosses segment boundaries"));
                    return false;
                }
                pktLen = (pktLen << 7) | (pkByte | 0X7F);
                if ((pkByte & 0X80) == 0) {
                    break;
                }
                tile.addPacketLength (pktLen);
            }
        }
        return true;
    }

}
