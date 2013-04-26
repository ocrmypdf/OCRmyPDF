/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the POC (Progression order change) marker segment.
 * May occur in the main or the tile part header.
 *
 * @author Gary McGath
 *
 */
public class POCMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public POCMarkerSegment() {
        super();
    }

    /** Process the marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     * 
     *  @return                <code>true</code> if segment is well-formed,
     *                         <code>false</code> otherwise.
     */
    protected boolean process(int bytesToEat) throws IOException {
        int compIdxBytes =  nCompBytes();
        if (compIdxBytes == 0) {
            _repInfo.setMessage (new ErrorMessage 
                    ("POC marker segment at wrong position in codestream"));
            // POC found before SIZ
            return false;
        }
        // The number of bytes per change depends on whether component
        // indices take one or two bytes.
        int changeSize = compIdxBytes < 257 ? 7 : 9;    // number of bytes per change
        int nChanges = bytesToEat / changeSize;
        // Make sure it's an even multiple
        if (changeSize * nChanges != bytesToEat) {
            _repInfo.setMessage (new ErrorMessage 
                    ("Invalid size for POC marker segment"));
            return false;
        }
        Property[] changes = new Property[nChanges];
        for (int i = 0; i < nChanges; i++) {
            int rspoc = _module.readUnsignedShort (_dstream); // resolution level idx
            int cspoc;
            // size of Ccoc field depends on number of components
            if (compIdxBytes < 257) {
                cspoc = ModuleBase.readUnsignedByte (_dstream, _module);
            }
            else{
                cspoc = _module.readUnsignedShort (_dstream);
            }
            int lyepoc = _module.readUnsignedShort (_dstream);
            int repoc = ModuleBase.readUnsignedByte (_dstream, _module);
            int cepoc;
            if (compIdxBytes < 257) {
                cepoc = ModuleBase.readUnsignedByte (_dstream, _module);
            }
            else {
                cepoc = _module.readUnsignedShort (_dstream);
            }
            int ppoc = ModuleBase.readUnsignedByte (_dstream, _module);
            Property[] propArr = new Property[5];
            propArr[0] = new Property ("StartResolutionLevelIndex",
                        PropertyType.INTEGER,
                        new Integer (rspoc));
            propArr[1] = new Property ("ComponentIndex",
                        PropertyType.INTEGER,
                        new Integer (cspoc));
            propArr[2] = new Property ("LayerIndex",
                        PropertyType.INTEGER,
                        new Integer (lyepoc));
            propArr[3] = new Property ("EndResolutionLevelIndex",
                        PropertyType.INTEGER,
                        new Integer (cepoc));
            propArr[4] = new Property ("ProgressionOrder",
                        PropertyType.INTEGER,
                        new Integer (ppoc));
            changes[i] = new Property ("Change",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        propArr);
        }
        MainOrTile cs = getMainOrTile ();
        cs.setPOCProperty (new Property ("ProgressionOrderChange",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        changes));
        
        return true;
    }

}
