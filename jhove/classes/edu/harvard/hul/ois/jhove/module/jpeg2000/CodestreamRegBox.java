/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Codestream Registration Box.
 * See ISO/IEC FCD15444-2: 2000, L.9.4.7
 * 
 * @author Gary McGath
 *
 */
public class CodestreamRegBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    (must be a ComposLayerHdrBox)
     */
    public CodestreamRegBox(RandomAccessFile raf, BoxHolder parent) {
        super(raf, parent);
    }

    /** Reads the box, putting appropriate information in
     *  the RepInfo object.  setModule, setBoxHeader,
     *  setRepInfo and setDataInputStream must be called
     *  before <code>readBox</code> is called. 
     *  <code>readBox</code> must completely consume the
     *  box, so that the next byte to be read by the
     *  DataInputStream is the <code>FF</code> byte of the next Box.
     */
    public boolean readBox() throws IOException {
        if (!(_parentBox instanceof ComposLayerHdrBox)) {
            wrongBoxContext();
            return false;
        }
        Property[] propArray = new Property[3];
        propArray[0] = new Property ("HorizontalGridSize",
                    PropertyType.INTEGER,
                    new Integer (_module.readUnsignedShort (_dstrm)));
        propArray[1] = new Property ("VerticalGridSize",
                    PropertyType.INTEGER,
                    new Integer (_module.readUnsignedShort (_dstrm)));
        int bytesLeft = (int) _boxHeader.getDataLength() - 4;
        
        // Each codestream entry is 6 bytes long (a short and 4 bytes)
        int nStreams = bytesLeft / 6;
        Property[] streamsProp = new Property[nStreams];
        for (int i = 0; i < nStreams; i++) {
            // Build a property for one codestream
            Property[] csProp = new Property[5];
            csProp[0] = new Property ("CodestreamNumber",
                    PropertyType.INTEGER,
                    new Integer (_module.readUnsignedShort (_dstrm)));
            csProp[1] = new Property ("HorizontalResolution",
                    PropertyType.INTEGER,
                    new Integer (ModuleBase.readUnsignedByte (_dstrm, _module)));
            csProp[2] = new Property ("VerticalResolution",
                    PropertyType.INTEGER,
                    new Integer (ModuleBase.readUnsignedByte (_dstrm, _module)));
            csProp[3] = new Property ("HorizontalOffset",
                    PropertyType.INTEGER,
                    new Integer (ModuleBase.readUnsignedByte (_dstrm, _module)));
            csProp[4] = new Property ("VerticalOffset",
                    PropertyType.INTEGER,
                    new Integer (ModuleBase.readUnsignedByte (_dstrm, _module)));

            streamsProp[i] = new Property ("Codestreams",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    csProp);
        }
        ((ComposLayerHdrBox) _parentBox).addCodestreamReg (new Property
                    ("CodestreamRegistration",
                     PropertyType.PROPERTY,
                     PropertyArity.ARRAY,
                     streamsProp));
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Codestream Registration Box";
    }
}
