/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * UUID Box.
 * See I.7.2 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 * @see UUIDInfoBox
 * @see UUIDListBox
 */
public class UUIDBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public UUIDBox (RandomAccessFile raf, BoxHolder parent)
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
        // The UUID box consists of a 16-byte UUID field
        // and a variable-size data field.  Both are binary
        // data, so we make them byte array properties.
        Property parray[] = new Property[2];
        
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();
        if (_boxHeader.getLength() != 0 && len < 16) {
            wrongBoxSize ();
            return false;
        }
        byte[] uuid = new byte[16];
        ModuleBase.readByteBuf (_dstrm, uuid, _module);
        parray[0] = new Property ("UUID",
                PropertyType.BYTE,
                PropertyArity.ARRAY,
                uuid);
        
        // Whatever is left is the data field.
        // This gets difficult if the length field is
        // 0, implying that the rest of the file is used.
        int dataLen = len - 16;
        if (dataLen > 0) {
            byte[] dataBytes = new byte[dataLen];
            ModuleBase.readByteBuf (_dstrm, dataBytes, _module);
            parray[1] = new Property ("Data",
                PropertyType.BYTE,
                PropertyArity.ARRAY,
                dataBytes);
        }
        else {
            // No data -- put in a FALSE property just as placeholder
            parray[1] = new Property ("Data",
                PropertyType.BOOLEAN,
                Boolean.FALSE);
        }
        _module.addUUID (new Property ("UUIDBox",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    parray));
                
        finalizeBytesRead ();
        return true;                
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "UUID Box";
    }
}
