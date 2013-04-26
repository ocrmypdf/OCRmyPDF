/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the SIZ marker segment.  This is a mandatory marker
 * in the main header, and provides information about the
 * uncompressed image such as the width and height of the
 * reference grid, the width and height of the tiles, the number
 * of components, component bit depth, and the separation of
 * component samples with respect to the reference grid.
 * 
 * @author Gary McGath
 *
 */
public class SIZMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public SIZMarkerSegment() {
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
     */
    protected boolean process (int bytesToEat) throws IOException
    {
        int rsiz = _module.readUnsignedShort (_dstream);
        // rsiz = capabilities needed to decode
        int xsiz = (int) _module.readUnsignedInt (_dstream);
        // width of reference grid
        int ysiz = (int) _module.readUnsignedInt (_dstream);
        // height of reference grid
        int xosiz = (int) _module.readUnsignedInt (_dstream);
        // horizontal offset to left side of image area
        int yosiz = (int) _module.readUnsignedInt (_dstream);
        // vertical offset to top of image area
        int xtsiz = (int) _module.readUnsignedInt (_dstream);
        // width of one reference tile
        int ytsiz = (int) _module.readUnsignedInt (_dstream);
        // height of one reference tile
        int xtosiz = (int) _module.readUnsignedInt (_dstream);
        // horizontal offset to left side of first tile
        int ytosiz = (int) _module.readUnsignedInt (_dstream);
        // vertical offset to top of first tile
        int csiz = _module.readUnsignedShort (_dstream);
        // number of components
        _cs.setNumComponents (csiz);
        int ssiz[] = new int [csiz];
        // precision and sign of samples
        for (int i = 0; i < csiz; i++) {
            ssiz[i] = ModuleBase.readUnsignedByte (_dstream, _module);
        }
        // number of bits per component
        int xrsiz[] = new int [csiz];
        // precision and sign of samples
        for (int i = 0; i < csiz; i++) {
            xrsiz[i] = ModuleBase.readUnsignedByte (_dstream, _module);
        }
        // horizontal sample separation

        int yrsiz[] = new int [csiz];
        for (int i = 0; i < csiz; i++) {
            yrsiz[i] = ModuleBase.readUnsignedByte (_dstream, _module);
        }
        // vertical sample separation
        
        
        // For now, just assemble the info into a SIZ property and
        // hand it to the Codestream.
        List plist = new ArrayList (13);
        plist.add (new Property ("Capabilities",
                PropertyType.INTEGER,
                new Integer (rsiz)));
        plist.add (new Property ("XSize",
                PropertyType.INTEGER,
                new Integer (xsiz)));
        plist.add (new Property ("YSize",
                PropertyType.INTEGER,
                new Integer (ysiz)));
        plist.add (new Property ("XOSize",
                PropertyType.INTEGER,
                new Integer (xosiz)));
        plist.add (new Property ("YOSize",
                PropertyType.INTEGER,
                new Integer (yosiz)));
        plist.add (new Property ("XTSize",
                PropertyType.INTEGER,
                new Integer (xtsiz)));
        plist.add (new Property ("YTSize",
                PropertyType.INTEGER,
                new Integer (ytsiz)));
        plist.add (new Property ("XTOSize",
                PropertyType.INTEGER,
                new Integer (xtosiz)));
        plist.add (new Property ("YTOSize",
                PropertyType.INTEGER,
                new Integer (ytosiz)));
        plist.add (new Property ("CSize",
                PropertyType.INTEGER,
                new Integer (csiz)));
        plist.add (new Property ("SSize",
                PropertyType.INTEGER,
                PropertyArity.ARRAY,
                ssiz));
        plist.add (new Property ("XRSize",
                PropertyType.INTEGER,
                PropertyArity.ARRAY,
                xrsiz));
        plist.add (new Property ("YRSize",
                PropertyType.INTEGER,
                PropertyArity.ARRAY,
                yrsiz));
        _cs.setSIZProperty(new Property ("ImageAndTileSize",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                plist));
        return true;
    }
}
