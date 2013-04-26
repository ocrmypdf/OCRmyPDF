/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 *  Class for the PPT (Packed packet headers, tile-part header)
 *  marker segment.  Similar to the PPM marker segment, but
 *  applicable to tile parts rather than the main header.
 *
 * @author Gary McGath
 *
 */
public class PPTMarkerSegment extends MarkerSegment {

    /**
     * Constructor.
     */
    public PPTMarkerSegment() {
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
    protected boolean process(int bytesToEat) throws IOException 
    {
        if (_ccs.isPPMSeen ()) {
            _repInfo.setMessage (new ErrorMessage
                    ("PPT and PPM not allowed in same codestream"));
            return false;
        }
        Tile tile = _ccs.getCurTile ();
        if (tile == null ) {
            _repInfo.setMessage (new ErrorMessage
                    ("PPT not allowed in codestream header"));
            return false;
        }
        
        int zppt = ModuleBase.readUnsignedByte (_dstream, _module);
        --bytesToEat;
        while (bytesToEat > 0) {
            // Number of bytes of Ippm info in the ith tile part
            long nppt = _module.readUnsignedInt (_dstream);
            bytesToEat -= 4;
            if (nppt > bytesToEat) {
                _repInfo.setMessage(new ErrorMessage 
                        ("Invalid length for tile-part header in PPM packet"));
                return false;
            }
            tile.addPPTLength (nppt);
            _module.skipBytes (_dstream, (int) nppt, _module);
            bytesToEat -= nppt;
        }

        return true;
    }
}
