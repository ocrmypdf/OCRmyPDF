/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Default Display Resolution Box.
 * See I.5.3.7.2 in ISO/IEC 15444-1:2000
 * 
 * @author Gary McGath
 *
 */
public class DDResolutionBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public DDResolutionBox (RandomAccessFile raf, BoxHolder parent)
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
        initBytesRead ();
        if (!(_parentBox instanceof ResolutionBox)) {
            wrongBoxContext();
            return false;
        }
        // The information consists of two values, horizontal and
        // vertical, with numerator, denominator, and exponent,
        // in dots per meter.  Not clear whether to present this 
        // as raw data, turn it into a dots/cm rational, or what.
        // I'll put it up as raw data for now.
        ResolutionBox rb = (ResolutionBox) _parentBox;
        List vresList = new ArrayList(3);
        List hresList = new ArrayList(3);
        vresList.add (new Property ("Numerator",
                PropertyType.INTEGER,
                new Integer (_module.readUnsignedShort (_dstrm))));
        vresList.add (new Property ("Denominator",
                PropertyType.INTEGER,
                new Integer (_module.readUnsignedShort (_dstrm))));
        hresList.add (new Property ("Numerator",
                PropertyType.INTEGER,
                new Integer (_module.readUnsignedShort (_dstrm))));
        hresList.add (new Property ("Denominator",
                PropertyType.INTEGER,
                new Integer (_module.readUnsignedShort (_dstrm))));
        vresList.add (new Property ("Exponent",
                PropertyType.INTEGER,
                new Integer (ModuleBase.readSignedByte (_dstrm, _module))));
        hresList.add (new Property ("Exponent",
                PropertyType.INTEGER,
                new Integer (ModuleBase.readSignedByte (_dstrm, _module))));
        // The three properties for each direction are subsumed into
        // a property.
        Property hres = new Property ("HorizResolution",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                hresList);
        Property vres = new Property ("VertResolution",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                vresList);
        // And the two resolution properties are subsumed into
        // one property for the Module.
        Property[] topProps = new Property[2];
        topProps[0] = hres;
        topProps[1] = vres;
        _module.addProperty(new Property ("DefaultDisplayResolution",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                topProps));
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Default Display Resolution Box";
    }
}
