/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Intellectual Property Rights box.
 * See I.6 in ISO/IEC 15444-1:2000
 * 
 * The spec says nothing about the content of the IPR box,
 * so the generated Property reports it as a sequence of bytes.
 *
 * @author Gary McGath
 *
 */
public class IPRBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public IPRBox (RandomAccessFile raf, BoxHolder parent)
    {
        super (raf);
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
        int len = (int) _boxHeader.getDataLength ();
        byte[] bytes = new byte[len];
        for (int i = 0; i < len; i++) {
            bytes[i] = (byte) ModuleBase.readUnsignedByte (_dstrm, _module);
        }
        _module.addProperty (new Property ("IntellectualPropertyRights",
                        PropertyType.BYTE,
                        PropertyArity.ARRAY,
                        bytes));
        finalizeBytesRead ();
        return true;                
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Intellectual Property Rights Box";
    }
}
