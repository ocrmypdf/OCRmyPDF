/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Class for the RGN (region of interest) marker segment.
 * This comes either in the main header or
 * after an SOT. 
 *
 * @author Gary McGath
 *
 */
public class RGNMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public RGNMarkerSegment() {
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
        int compIdxBytes =  nCompBytes();
        if (compIdxBytes == 0) {
            // RGN found before SIZ
            _repInfo.setMessage (new ErrorMessage 
                    ("RGN marker segment at wrong position in codestream"));
            return false;
        }
        int compIdx;
        // size of Ccoc field depends on number of components
        if (compIdxBytes < 257) {
            compIdx = ModuleBase.readUnsignedByte (_dstream, _module);
        }
        else{
            compIdx = _module.readUnsignedShort (_dstream);
        }
        int srgn = ModuleBase.readUnsignedByte (_dstream, _module);
        int sprgn = ModuleBase.readUnsignedByte (_dstream, _module);
        MainOrTile cs = getMainOrTile ();

        List propList = new ArrayList (2);
        propList.add (new Property ("ROIStyle", 
                    PropertyType.INTEGER,
                    new Integer (srgn)));
        propList.add (new Property ("ROIParameter",
                    PropertyType.INTEGER,
                    new Integer (sprgn)));
        cs.setCompProperty (compIdx,
                    new Property ("RegionOfInterest",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            propList));

        return true;
    }

}
