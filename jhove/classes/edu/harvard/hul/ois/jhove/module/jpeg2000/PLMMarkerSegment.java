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
 * Class for the PLM Marker segment. This gives packet lengths at
 * the header level. 
 * 
 * @author Gary McGath
 *
 */
public class PLMMarkerSegment extends MarkerSegment {

    // A tile part may extend across several marker segments.
    // we store the remainder statically here.
    static int nplmLeft;
    
    /**
     * Constructor.
     */
    public PLMMarkerSegment() {
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
        int zplm = ModuleBase.readUnsignedByte (_dstream, _module);
        --bytesToEat;
        if (zplm == 0) {
            nplmLeft = 0;
        }
        // Whether there is an nplm, giving the number of bytes
        // of iplm information for the tile part, depends on whether
        // the previous nplm has been counted out.  This is actually
        // quite excessive, since nplm can't be any bigger than 255.
        // Who DESIGNED this silly marker segment anyway?
        if (nplmLeft == 0) {
            nplmLeft = ModuleBase.readUnsignedByte (_dstream, _module);
            --bytesToEat;
        }
        
        // To add to the complications, each iplm can have a different 
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
                            ("Packet length in PLM marker segment crosses segment boundaries"));
                    return false;
                }
                pktLen = (pktLen << 7) | (pkByte | 0X7F);
                if ((pkByte & 0X80) == 0) {
                    break;
                }
                _cs.addPacketLength (pktLen);
            }
        }
        
        return true;
    }

}
