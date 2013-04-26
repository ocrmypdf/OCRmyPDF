/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Capture Resolution Box.
 * See I.5.3.7.1 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class CaptureResolutionBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public CaptureResolutionBox (RandomAccessFile raf, BoxHolder parent)
    {
        super (raf, parent);
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
        if (!(_parentBox instanceof ResolutionBox)) {
            wrongBoxContext ();
            return false;
        }
        initBytesRead ();
        ResolutionBox resBox = (ResolutionBox) _parentBox;

        // Vertical Capture grid resolution num & denom
        int vrcNum = _module.readUnsignedShort (_dstrm);
        int vrcDenom = _module.readUnsignedShort (_dstrm);
        
        // Horizontal Capture grid resolution num & denom
        int hrcNum = _module.readUnsignedShort (_dstrm);
        int hrcDenom = _module.readUnsignedShort (_dstrm);
        
        // Vertical and Horizontal capture grid exponents
        int vrcExp = ModuleBase.readUnsignedByte (_dstrm, _module);
        int hrcExp = ModuleBase.readUnsignedByte (_dstrm, _module);
        
        // We need to set resolution in NisoImageMetadata
        // as a Rational.  It seems unlikely that negative
        // exponents will be used (signifying resolutions
        // less than 1 dpi), so we figure the exponent into
        // the numerator.  Also, this resolution is in 
        // dots per meter, which isn't a NISO standard unit,
        // so we multiply the denominator by 100 to give
        // units per centimeter.
        Rational vrc = new Rational 
                    ((int) (vrcNum * Math.pow (10, vrcExp)),
                     vrcDenom * 100);
        Rational hrc = new Rational 
                    ((int) (hrcNum * Math.pow (10, hrcExp)),
                     hrcDenom * 100);
        NisoImageMetadata niso = _module.getCurrentNiso ();
        niso.setYSamplingFrequency (vrc);
        niso.setXSamplingFrequency (hrc);
        niso.setSamplingFrequencyUnit (3);
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Capture Resolution Box";
    }
}
