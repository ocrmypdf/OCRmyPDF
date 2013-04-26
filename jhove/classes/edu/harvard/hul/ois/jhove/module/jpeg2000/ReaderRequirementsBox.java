/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Reader requirements box (JPX).
 * See L.9.1 in ISO/IEC FCD15444-2:2000.
 *
 * @author Gary McGath
 *
 */
public class ReaderRequirementsBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ReaderRequirementsBox(RandomAccessFile raf, BoxHolder parent) {
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
        final String badRR = "Invalid data in Reader Requirements box";
        if (_parentBox != null) {
            wrongBoxContext();
System.out.println ("READBOX parentBox != null");
System.out.flush ();
            return false;
        }
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();
        
        int maskLength = ModuleBase.readUnsignedByte (_dstrm, _module);
        // maskLength specifies the size of FUAM and DCM, and may be
        // 1, 2, 4 or 8
        long fuam;     // fully understand aspects mask
        long dcm;      // decode completely mask
        switch (maskLength) {
            case 1:
            fuam = ModuleBase.readUnsignedByte (_dstrm, _module);
            dcm = ModuleBase.readUnsignedByte (_dstrm, _module);
            break;
            
            case 2:
            fuam = _module.readUnsignedShort (_dstrm);
            dcm = _module.readUnsignedShort (_dstrm);
            break;
            
            case 4:
            fuam = _module.readUnsignedInt (_dstrm);
            dcm = _module.readUnsignedInt (_dstrm);
            break;
            
            case 8:
            fuam = _module.readSignedLong (_dstrm);
            dcm = _module.readSignedLong (_dstrm);
            break;
            
            default:
            _repInfo.setMessage (new ErrorMessage (badRR, _module.getFilePos ()));
            _repInfo.setWellFormed (false);
System.out.println ("READBOX default");
System.out.flush ();
            return false;
        }
        
        // nsf (number of standard flags)
        int nsf = _module.readUnsignedShort (_dstrm);
        for (int i = 0; i < nsf; i++) {
            int sf = _module.readUnsignedShort (_dstrm);
        }
        // Table L-13, which gives legal values of the 
        // SF field, has a completely blank "value" column!
        // Presumably SF stands for "science fiction."
        
        _module.skipBytes (_dstrm, 
                (int) (len - (_module.getFilePos () - startBytesRead)), _module);
        finalizeBytesRead ();
        _module.setRReqSeen (true);
System.out.println ("READBOX seen=true");
System.out.flush ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Reader Requirements Box";
    }
}
