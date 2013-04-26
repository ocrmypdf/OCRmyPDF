/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Continuous codestream box.
 * See I.5.4 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class ContCodestreamBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ContCodestreamBox (RandomAccessFile raf, BoxHolder parent)
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
     * 
     *  The reading and interpretation of the actual codestream 
     *  occurs within the execution of readBox.
     */
    public boolean readBox() throws IOException {
        initBytesRead ();
        
        // Must come after the JP2 header
        if (!_module.isJP2HdrSeen()) {
            _repInfo.setMessage (new ErrorMessage 
                (noJP2Hdr, _module.getFilePos ()));
            return false;
        }
        int ncs = _module.getNCodestreams () + 1;
        _module.setNCodestreams (ncs);
        Codestream curCodestream = _module.getCodestream (ncs);
        long len = 
            _boxHeader.getLength () == 0 ?
            0 : _boxHeader.getDataLength ();
        ContCodestream ccs = 
            new ContCodestream (_module, _dstrm, len);    
        boolean retval = ccs.readCodestream (curCodestream, _repInfo);                
        finalizeBytesRead ();
        return retval;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Contiguous Codestream Box";
    }
}
