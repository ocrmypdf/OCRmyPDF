/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the QCC (Quantization component) marker segment.
 * May occur in the main or the tile part header.  In the
 * main header it overrides the QCD for the specified
 * component.  In the tile part header it overrides the
 * QCD for the component in the tile part.
 *
 * @author Gary McGath
 *
 */
public class QCCMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public QCCMarkerSegment() {
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
    protected boolean process(int bytesToEat)
	throws IOException
    {
        int compIdxBytes =  nCompBytes();
        if (compIdxBytes == 0) {
            // QCC found before SIZ
            _repInfo.setMessage (new ErrorMessage 
                    ("QCC marker segment at wrong position in codestream"));
            return false;
        }
        int compIdx;
        int bytesEaten;
        // size of Ccoc field depends on number of components
        if (compIdxBytes < 257) {
            compIdx = ModuleBase.readUnsignedByte (_dstream, _module);
            bytesEaten = 1;
        }
        else{
            compIdx = _module.readUnsignedShort (_dstream);
            bytesEaten = 2;
	}
        int sqcc = ModuleBase.readUnsignedByte (_dstream, _module);
        bytesEaten++;
        
        int sqccLow = sqcc & 0X1F;
        int nspqcc;
        int spqcc[];
        switch (sqccLow) {
	case 0:
	    // no quantization -- byte entries in spqcd
	    nspqcc = bytesToEat - bytesEaten;
	    spqcc = new int[nspqcc];
	    for (int i = 0; i < nspqcc; i++) {
		spqcc[i] = ModuleBase.readUnsignedByte (_dstream, _module);
	    }
	    break;
            
	case 1:
            // scalar derived (just 2 bytes of value)
	case 2:
            // scalar expounded
            nspqcc = (bytesToEat - bytesEaten) / 2;
            spqcc = new int[nspqcc];
            for (int i = 0; i < nspqcc; i++) {
                spqcc[i] = _module.readUnsignedShort (_dstream);
            }
            break;
	default:
            _repInfo.setMessage (new ErrorMessage
                    ("Unrecognized quantization type in QCC marker segment"));
            return false;    // reserved value
        }

        MainOrTile cs = getMainOrTile ();
        List propList = new ArrayList (2);
        propList.add (new Property ("QuantizationStyle",
                    PropertyType.INTEGER,
                    new Integer (sqcc)));
        propList.add (new Property ("StepValue",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    spqcc));
        cs.setCompProperty (compIdx,
                    new Property ("QuantizationComponent",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            propList));
        return true;
    }

}
