/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Image Header Box.
 * See I.5.3.1 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class ImageHeaderBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ImageHeaderBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (!(_parentBox instanceof JP2HeaderBox)) {
            _repInfo.setMessage (new ErrorMessage
                ("ImageHeader Box in illegal context", _module.getFilePos ()));
            return false;
        }
        initBytesRead ();
        if (_boxHeader.getLength() != 22) {
            _repInfo.setMessage (new ErrorMessage
                ("Image Header Box is incorrect size", _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
        }
        
        // If this is called from a JP2 Header, we set values
        // in _defaultNiso, otherwise we set them in the image's
        // Niso metadata.  Question: where do we get the codestream?
        NisoImageMetadata niso;
        if (_parentBox instanceof CodestreamHeaderBox) {
            Codestream cs = ((CodestreamHeaderBox) _parentBox).getCodestream ();
            niso = cs.getNiso ();
        }
        else {
            niso = _module.getDefaultNiso ();
        }
        
        long height = _module.readUnsignedInt (_dstrm);
        niso.setImageLength (height);
        long width = _module.readUnsignedInt (_dstrm);
        niso.setImageWidth (width);
        int nc = _module.readUnsignedShort (_dstrm);
        if (nc == 0) {
            _repInfo.setMessage (new ErrorMessage
                    ("ImageHeader Box haz zero components", _module.getFilePos ()));
            return false;   
        }
        niso.setSamplesPerPixel(nc);
        int bpc = ModuleBase.readUnsignedByte(_dstrm, _module);
        if (bpc != 255) {
            // If the value is 255, use the BPC box.
            int[] bits = new int[nc];
            int bps = (bpc & 0X7F) + 1;
            for (int i = 0; i < nc; i++) {
                bits[i] = bps;
            }
            // The high-order bit of bpc is 1 if the samples have
            // signed values (!).  What do we do with it?
            niso.setBitsPerSample(bits);
        }
        int compression = ModuleBase.readUnsignedByte (_dstrm, _module);
        if (compression == 7) {
            niso.setCompressionScheme (34712);  // JPEG 2000
        }
        
        int unk = ModuleBase.readUnsignedByte (_dstrm, _module);
        _module.addProperty (new Property ("ColorspaceUnknown",
                PropertyType.BOOLEAN,
                new Boolean (unk != 0)));
        
        int ipr = ModuleBase.readUnsignedByte (_dstrm, _module);
        // This just says whether there is an IPR box.
        // Do we need to do anything with it?
        finalizeBytesRead ();
        _module.setImageHeaderSeen (true);
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Image Header Box";
    }
}
