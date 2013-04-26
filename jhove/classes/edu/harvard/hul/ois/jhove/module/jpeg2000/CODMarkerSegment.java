/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
//import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;

/**
 *  Class for the COD (coding style default) marker segment.
 * This comes either in the main header or
 * after an SOT and describes the functions
 * used to code the entire tile. 
 * 
 * @author Gary McGath
 *
 */
public class CODMarkerSegment extends MarkerSegment {

    public CODMarkerSegment ()
    {
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
    protected boolean process (int bytesToEat) throws IOException
    {
        int codeStyle = ModuleBase.readUnsignedByte (_dstream, _module);
        
        // The SGcod parameter, 32 bits
        int progOrder = ModuleBase.readUnsignedByte (_dstream, _module);
        int nLayers = _module.readUnsignedShort (_dstream);
        int mcTrans = ModuleBase.readUnsignedByte (_dstream, _module);
        
        // The SPcod parameters
        int nDecomp = ModuleBase.readUnsignedByte (_dstream, _module);
        int codeBlockWid = ModuleBase.readUnsignedByte (_dstream, _module);
        int codeBlockHt = ModuleBase.readUnsignedByte (_dstream, _module);
        int codeBlockStyle = ModuleBase.readUnsignedByte (_dstream, _module);
        int xform = ModuleBase.readUnsignedByte (_dstream, _module);
        int precSize[] = null;
        if ((codeStyle & 1) != 0) {
            // The first parameter (8 bits) corresponds to the
            // N(L)LL subband.  Each successive parameter corresponds
            // to each successive resolution level in order.
            // I think that means the number of bytes equals the
            // number of resolution levels + 1 -- but where do I get
            // the number of resolution levels?  Based on the (highly
            // confusing) information about the marker segment length,
            // that must be the same as the number of decomposition
            // levels.
            precSize = new int[nDecomp + 1];
            for (int i = 0; i < nDecomp + 1; i++) {
                precSize[i] = ModuleBase.readUnsignedByte (_dstream, _module);
            }
        }
        MainOrTile cs = getMainOrTile ();
        
        // Set values for the tile or codestream
        List propList = new ArrayList (12);
        propList.add (new Property ("CodingStyle",
                    PropertyType.INTEGER,
                    new Integer (codeStyle)));
        propList.add (new Property ("ProgressionOrder",
                    PropertyType.INTEGER,
                    new Integer (progOrder)));
        propList.add (new Property ("NumberOfLayers",
                    PropertyType.INTEGER,
                    new Integer (nLayers)));
        propList.add (new Property ("MultipleComponentTransformation",
                    PropertyType.INTEGER,
                    new Integer (mcTrans)));
        propList.add (new Property ("NumberDecompositionLevels",
                    PropertyType.INTEGER,
                    new Integer (nDecomp)));
        propList.add (new Property ("CodeBlockWidth",
                    PropertyType.INTEGER,
                    new Integer (codeBlockWid)));
        propList.add (new Property ("CodeBlockHeight",
                    PropertyType.INTEGER,
                    new Integer (codeBlockHt)));
        propList.add (new Property ("CodeBlockStyle",
                    PropertyType.INTEGER,
                    new Integer (codeBlockStyle)));
        propList.add (new Property ("Transformation",
                    PropertyType.INTEGER,
                    new Integer (xform)));
        if (precSize != null) {
            propList.add (new Property ("PrecinctSize",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    precSize));
        }
        cs.setCODProperty (new Property ("CodingStyleDefault",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList));

        return true;
    }

}
