/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Channel Definition Box.
 * See I.5.3.6 in ISO/IEC 15444-1:2000
 * and ISO/IEC FCD15444-2: 2000, L.9.4.5
 *
 * @author Gary McGath
 *
 */
public class ChannelDefBox extends JP2Box {


    /**
     *  Constructor with superbox.
     */
    public ChannelDefBox (RandomAccessFile raf, BoxHolder parent)
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
        if (!(_parentBox instanceof JP2HeaderBox ||
              _parentBox instanceof CodestreamHeaderBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();

        int nchan = _module.readUnsignedShort (_dstrm);
        len -= 2;
        Property[] chans = new Property[nchan];
        for (int i = 0; i < nchan; i++) {
            Property[] cprop = new Property[3];
            int cidx = _module.readUnsignedShort (_dstrm);
            cprop[0] = new Property ("ChannelIndex",
                        PropertyType.INTEGER,
                        new Integer (cidx));
            int typ = _module.readUnsignedShort (_dstrm);
            cprop[1] = _module.addIntegerProperty ("ChannelType", typ,
                    JP2Strings.ctypStr,
                    JP2Strings.ctypIdx);
            int assoc = _module.readUnsignedShort (_dstrm);
            len -= 6;
            
            // The interpretation of the assoc field depends
            // on the color space, so we just report it as
            // an integer.
            cprop[2] = new Property ("ChannelAssociation",
                        PropertyType.INTEGER,
                        new Integer (assoc));
            chans[i] = new Property ("Channel",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        cprop);
        }
        
        _module.skipBytes (_dstrm, (int) len, _module);

        Property prop = new Property ("ChannelDefinition",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                chans);
        if (_parentBox instanceof JP2HeaderBox) {
            _module.addProperty (prop);
        }
        else if (_parentBox instanceof ComposLayerHdrBox) {
            ((ComposLayerHdrBox) _parentBox).addChannelDef (prop);
        }
   
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Channel Definition Box";
    }
}
