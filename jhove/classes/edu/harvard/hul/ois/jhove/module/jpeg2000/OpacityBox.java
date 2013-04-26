/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Opacity Box (JPX).
 * See ISO/IEC FCD15444-2: 2000, L.9.4.6
 * 
 * 
 * @author Gary McGath
 *
 */
public class OpacityBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public OpacityBox(RandomAccessFile raf, BoxHolder parent) {
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
        initBytesRead ();
        
        List propList = new ArrayList (4);
        
        App app = _module.getApp ();
        int otyp = ModuleBase.readUnsignedByte (_dstrm, _module);
        propList.add (_module.addIntegerProperty ("Type",
                    otyp,
                    JP2Strings.opacityTypeStr));
        if (otyp > 2) {
            _repInfo.setMessage (new ErrorMessage
                    ("Invalid OTyp field in Opacity Box",
                     _module.getFilePos ()));
            _repInfo.setValid (false);
            return false;
        }
        
        // The documentation of the Opacity Box is self-contradictory
        // with regard to what OTyp values are
        // followed by NCH and CV[n] fields.  (There is also 
        // a reference to an unspecified "PR" field.)
        // The only safe course is to see if there are any more bytes.
        int bytesLeft = (int) _boxHeader.getDataLength () - 1;
        if (bytesLeft > 0) {
            int nch = ModuleBase.readUnsignedByte (_dstrm, _module);
            // The size in bytes of the channel-key values 
            // depends on the bit depth of the corresponding
            // channel, but it's simpler to calculate it based
            // on the bytes remaining.
            int[] keys = new int[nch];
            int keysize = (bytesLeft - 1) / nch;
            for (int i = 0; i < nch; i++) {
                int chkey = 0;
                for (int j = 0; j < keysize; j++) {
                    chkey = (chkey << 8) + 
                            ModuleBase.readUnsignedByte (_dstrm, _module);
                }
                keys[i] = chkey;
            }
            propList.add (new Property ("ChromaKeyValues",
                        PropertyType.INTEGER,
                        PropertyArity.ARRAY,
                        keys));
        }
        ((ComposLayerHdrBox) _parentBox).addOpacity
                (new Property ("Opacity",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        propList));
        
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Opacity Box";
    }
}
