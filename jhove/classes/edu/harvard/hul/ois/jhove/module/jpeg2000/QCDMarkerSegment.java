/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Class for the QCD (Quantization default) marker segment.
 * This comes either in the main header or
 * after an SOT. 
 *
 * @author Gary McGath
 *
 */
public class QCDMarkerSegment extends MarkerSegment {

    /**
     *   Constructor.
     */
    public QCDMarkerSegment() {
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
        int sqcd = ModuleBase.readUnsignedByte (_dstream, _module);
        // What follows depends on the value of sqcd in a messy way
        int sqcdLow = sqcd & 0X1F;
        int nspqcd;
        int spqcd[];
        switch (sqcdLow) {
            case 0:
            // no quantization -- byte entries in spqcd
            nspqcd = bytesToEat - 1;
            spqcd = new int[nspqcd];
            for (int i = 0; i < nspqcd; i++) {
                spqcd[i] = ModuleBase.readUnsignedByte (_dstream, _module);
            }
            break;
            
            case 1:
            // scalar derived (just 2 bytes of value)
            case 2:
            // scalar expounded
            nspqcd = (bytesToEat - 1) / 2;
            spqcd = new int[nspqcd];
            for (int i = 0; i < nspqcd; i++) {
                spqcd[i] = _module.readUnsignedShort (_dstream);
            }
            break;
            
            default:
            _repInfo.setMessage (new ErrorMessage
                    ("Unrecognized quantization type in QCD marker segment"));
            return false;    // reserved value
        }
        List propList = new ArrayList (2);
        propList.add (new Property ("QuantizationStyle",
                    PropertyType.INTEGER,
                    new Integer (sqcd)));
        propList.add (new Property ("StepValue",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    spqcd));
        MainOrTile cs = getMainOrTile ();
        cs.setQCDProperty (new Property ("QuantizationDefault",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList));
        return true;
    }

}
