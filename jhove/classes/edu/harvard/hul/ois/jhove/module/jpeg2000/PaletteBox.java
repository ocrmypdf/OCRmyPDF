/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Palette box.
 * See I.5.3.4 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class PaletteBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public PaletteBox (RandomAccessFile raf, BoxHolder parent)
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
        if (!(_parentBox instanceof JP2HeaderBox)) {
            _repInfo.setMessage (new ErrorMessage
                ("Image Header Box in illegal context", _module.getFilePos ()));
            return false;
        }
        initBytesRead ();
        //_module.setPaletteSeen (true);
        int len = (int) _boxHeader.getDataLength ();
        long startNByte = _module.getFilePos();   
        // Track how many bytes to skip

        int ne = _module.readUnsignedShort (_dstrm);
        // 2 bytes have been read
        if (ne < 1 || ne > 1024) {
            _repInfo.setMessage (new ErrorMessage
                ("Palette must have 1 to 1024 entries", _module.getFilePos()));
            _repInfo.setValid (false);  // But keep going anyway
        }
        Property[] subProp = new Property[4];
        subProp[0] = new Property ("Entries", PropertyType.INTEGER,
                new Integer (ne));
        
        int nc = ModuleBase.readUnsignedByte (_dstrm, _module);
        // 3 bytes have been read
        int bytesRead = 3;
        subProp[1] = new Property ("Components", PropertyType.INTEGER,
                new Integer (nc));

        // Each component can, in principle, have a different bit depth,
        // and each can separately be signed or unsigned.
        int[] bpc = new int [nc];
        boolean[] cmpsigned = new boolean [nc];
        for (int i = 0; i < nc; i++) {
            int b = ModuleBase.readUnsignedByte (_dstrm, _module);
            cmpsigned[i] = ((b & 0X80) != 0);
            bpc[i] = (b & 0X7F) + 1;
        }
        bytesRead += nc;
        
        subProp[2] = new Property ("BitDepth", PropertyType.INTEGER,
                PropertyArity.ARRAY, bpc);
        
        // Now the actual component value arrays.  Skip this if
        // ne is out of bounds.
        if (ne > 1024 || ne < 1) {
            subProp[3] = new Property ("Values", PropertyType.STRING,
                    "Invalid");
        }
        else {
            Property[] cprop = new Property[nc];
            for (int i = 0; i < nc; i++) {
                int[] c = new int[ne];
                for (int j = 0; j < ne; j++) {
                    c[j] = ModuleBase.readUnsignedByte (_dstrm, _module);
                }
                cprop[i] = new Property ("Component",
                        PropertyType.INTEGER,
                        PropertyArity.ARRAY,
                        c);
            }
            subProp[3] = new Property ("Values", PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        cprop);
            bytesRead += nc * ne;
        }
        Property palProp = new Property ("Palette",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        subProp);
        if (_parentBox instanceof CodestreamHeaderBox) {
            Codestream cs = ((CodestreamHeaderBox) _parentBox).getCodestream ();
            cs.setPaletteProperty (palProp);
        }
        else {
            _module.addProperty (palProp);
        }
        // Skip any bytes we haven't read
        _module.skipBytes (_dstrm, 
                (int) (len - (_module.getFilePos() - startNByte)), _module);

        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Palette Box";
    }
}
