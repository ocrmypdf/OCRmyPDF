/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * UUID Box.
 * See I.7.3.1 in ISO/IEC 15444-1:2000
 * 
 * @author Gary McGath
 *
 */
public class UUIDListBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public UUIDListBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (!(_parentBox instanceof UUIDInfoBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();

        int nUUID = _module.readUnsignedShort (_dstrm);
        if ((16 * nUUID + 2) != _boxHeader.getDataLength()) {
            wrongBoxSize ();
            return false;
        }
        byte[][] uuids = new byte[nUUID][];
        for (int i = 0; i < nUUID; i++) {
            ModuleBase.readByteBuf (_dstrm, uuids[i], _module);
        }
        if (_parentBox instanceof UUIDInfoBox) {
            ((UUIDInfoBox) _parentBox).setUUIDList (uuids);
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "UUID List Box";
    }
}
