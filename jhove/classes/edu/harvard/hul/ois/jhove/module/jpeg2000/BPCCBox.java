/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Bits Per Component box.
 * See I.5.3.2 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class BPCCBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public BPCCBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (!(_parentBox instanceof JP2HeaderBox ||
              _parentBox instanceof CodestreamHeaderBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();
        int[] bits = new int[len];
        for (int i = 0; i < len; i++) {
            bits[i] = ModuleBase.readUnsignedByte (_dstrm, _module);
        }
        NisoImageMetadata niso;
        niso = _module.getCurrentNiso ();
        niso.setBitsPerSample (bits);
        
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Bits Per Component Box";
    }
}
