/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
//import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;

/**
 * Class for the COC (Coding style component) marker segment.
 * May occur in the main or the tile part header.  In the
 * main header it overrides the COD for the specified
 * component.  In the tile part header it overrides the
 * COD for the component in the tile part.
 * 
 * @author Gary McGath
 *
 */
public class COCMarkerSegment extends MarkerSegment {

    /**
     *  Constructor.
     */
    public COCMarkerSegment() {
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
            // COC found before SIZ
            _repInfo.setMessage (new ErrorMessage 
                    ("COC marker segment at wrong position in codestream"));
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
        int codeStyle = ModuleBase.readUnsignedByte (_dstream, _module);

        // The SPcoc parameters
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
        
        // Build a property and attach it to the appropriate component.  This
        // may be a component of the codestream or of a tile part.  The
        // number of components is apparently established only by the SIZ
        // marker segment and never changes for tiles or tile parts.
        MainOrTile cs = getMainOrTile ();
        List<Property> propList = new ArrayList<Property> (10);
        propList.add (new Property ("CodingStyle",
                    PropertyType.INTEGER,
                    new Integer (codeStyle)));
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
        propList.add (new Property ("PrecinctSize",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    precSize));
        cs.setCompProperty (compIdx,
                    new Property ("COC",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            propList));

        return true;
    }

}
