/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;

/**
 * Composition options box (JPX).
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.10.1
 * 
 * @author Gary McGath
 *
 */
public class CompOptionsBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public CompOptionsBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (!(_parentBox instanceof CompositionBox)) {
            wrongBoxContext ();
            return false;
        }
        initBytesRead ();
        if (_boxHeader.getDataLength () != 10) {
            wrongBoxSize ();
            return false;
        }
        CompositionBox parent = (CompositionBox) _parentBox;
        parent.setHeight (_module.readUnsignedInt (_dstrm));
        parent.setWidth (_module.readUnsignedInt (_dstrm));
        parent.setLoop (_module.readUnsignedShort (_dstrm));
        
        finalizeBytesRead ();
        return true;
    }

}
