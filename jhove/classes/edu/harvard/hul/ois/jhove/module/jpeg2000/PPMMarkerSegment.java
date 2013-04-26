/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 *  Class for the PPM (Packed packet headers, main header)
 *  marker segment.  I'm assuming for the present that the
 *  full details of packet headers is getting deeper into
 *  the bits than we want, so it just checks some basic
 *  information.  There can be multiple PPM marker segments.
 *
 * @author Gary McGath
 *
 */
public class PPMMarkerSegment extends MarkerSegment {

    /**
     * Constructor.
     */
    public PPMMarkerSegment() {
        super();
        _ccs.setPPMSeen (true);
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
        // Get index of this segment
        int zppm = ModuleBase.readUnsignedByte (_dstream, _module);
        --bytesToEat;
        
        while (bytesToEat > 0) {
            // Number of bytes of Ippm info in the ith tile part
            long nppm = _module.readUnsignedInt (_dstream);
            bytesToEat -= 4;
            if (nppm > bytesToEat) {
                _repInfo.setMessage(new ErrorMessage 
                        ("Invalid length for tile-part header in PPM packet"));
                return false;
            }
            _cs.addPPMLength (nppm);
            _module.skipBytes (_dstream, (int) nppm, _module);
            bytesToEat -= nppm;
        }
        return true;
    }
}
