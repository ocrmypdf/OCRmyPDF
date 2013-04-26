/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * XML Box.
 * See I.7.1 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class XMLBox extends JP2Box {

    private String xmlData;

    

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public XMLBox (RandomAccessFile raf, BoxHolder parent)
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
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();
        
        byte[] bbuf = new byte[len];
                
        ModuleBase.readByteBuf (_dstrm, bbuf, _module);
        xmlData = new String (bbuf);
        if (_parentBox == null) {
            _module.addXML (xmlData);
        }
        
        finalizeBytesRead ();
        return true;                
    }

    /** Returns a Property which describes the Box, for use
     *  by Association boxes and perhaps others.
     */
    protected Property getSelfPropDesc () 
    {
        return new Property (DESCRIPTION_NAME,
                PropertyType.STRING,
                xmlData);
    }


    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "XML Box";
    }
}
