/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Graphics Technology Standard Output Box.
 * This box holds an ICC color profile.
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.15.1
 * 
 * @author Gary McGath
 *
 */
public class GTSOBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public GTSOBox(RandomAccessFile raf, BoxHolder parent) {
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
        initBytesRead ();
        // Short of pulling out the bytes and somehow
        // analyzing them, about all we can do is report
        // the presence and length of the profile.  
        
        // There can be only one GTSO box within the file,
        // which seems oddly limiting compared to the rest
        // of JPEG 2000.  But it makes this simple.
        long propSize = _boxHeader.getDataLength ();
        Property sizeProp = new Property ("ProfileLength",
                PropertyType.LONG,
                new Long (propSize));
        _module.addProperty (new Property 
                ("GraphicsTechnologyStandardOutput",
                 PropertyType.PROPERTY,
                 sizeProp));
        _module.skipBytes (_dstrm, (int) propSize, _module);
        finalizeBytesRead ();
        return true;
    }

}
