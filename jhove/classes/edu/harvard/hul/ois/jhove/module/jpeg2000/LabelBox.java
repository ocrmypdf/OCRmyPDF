/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Label box.
 * A Label box does nothing in itself; it simply makes its
 * label string available for its superbox.
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.13
 * 
 * @author Gary McGath
 *
 */
public class LabelBox extends JP2Box {

    /* The label text. */
    private String _label;
    

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public LabelBox(RandomAccessFile raf, BoxHolder parent) {
        super(raf, parent);
    }

    /** Reads the box, saving the label text.  
     *  setModule, setBoxHeader,
     *  setRepInfo and setDataInputStream must be called
     *  before <code>readBox</code> is called. 
     *  <code>readBox</code> must completely consume the
     *  box, so that the next byte to be read by the
     *  DataInputStream is the <code>FF</code> byte of the next Box.
     */
    public boolean readBox() throws IOException {
        if (_parentBox == null) {
            wrongBoxContext();
            return false;
        }
        byte[] byteBuf = new byte [(int) _boxHeader.getDataLength()];
        ModuleBase.readByteBuf (_dstrm, byteBuf, _module);
        _label = new String (byteBuf, "UTF-8");
        return true;
    }


    /** Returns the label string. Valid only after
     *  <code>readBox()</code> has been called. 
     */
    protected String getLabel ()
    {
        return _label;
    }

    /** Returns a Property which describes the Box, for use
     *  by Association boxes and perhaps others.
     */
    protected Property getSelfPropDesc () 
    {
        return new Property (DESCRIPTION_NAME,
                PropertyType.STRING,
                _label);
    }



    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Label Box";
    }
}
