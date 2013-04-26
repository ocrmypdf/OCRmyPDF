/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;


/**
 * Data Entry URL Box.
 * 
 * @author Gary McGath
 *
 */
public class DataEntryURLBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public DataEntryURLBox(RandomAccessFile raf, BoxHolder parent) {
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
        for (int i = 0; i < 4; i++) {
            // version and flags must be 0.
            // If they aren't, keep going, since we can.
            int v = ModuleBase.readUnsignedByte (_dstrm, _module);
            if (v != 0) {
                _repInfo.setMessage (new ErrorMessage
                    ("Unrecognized version or flag value in Data Entry URL Box",
                     _module.getFilePos ()));
                _repInfo.setValid (false);
                break;
            }
        }
        // The URL is encoded as a null-terminated string
        // of UTF-8 characters.
        List byteList = new ArrayList (512);
        for (;;) {
            int b = ModuleBase.readUnsignedByte(_dstrm, _module);
            if (b == 0) {
                break;
            }
            byteList.add (new Byte ((byte) b));
        }
        // Turn the Byte List into a byte array.  (Is there a better
        // way to do this?)
        ListIterator li = byteList.listIterator ();
        byte byteArr[] = new byte[byteList.size ()];
        int j = 0;
        while (li.hasNext ()) {
            byteArr[j] = ((Byte)li.next ()).byteValue ();
        }
        String s = new String (byteArr, "UTF-8");
        if (_parentBox instanceof UUIDInfoBox) {
            UUIDInfoBox uu = (UUIDInfoBox) _parentBox;
            uu.setURL (s);
        }

        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Data Entry URL Box";
    }
}
