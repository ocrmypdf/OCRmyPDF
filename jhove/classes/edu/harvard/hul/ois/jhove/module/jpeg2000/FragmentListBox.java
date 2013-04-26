/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Fragment List Box (JPX).
 * Subbox of Fragment Table box or Cross-Reference box.
 * See L.9.6.1 in ISO/IEC FCD15444-2:2000.
 *
 * @author Gary McGath
 *
 */
public class FragmentListBox extends JP2Box {

    private List<long[]> _fragmentList;
    

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box.
     *                    The parent may be a FragmentTableBox
     *                    or a CrossReferenceBox.
     */
    public FragmentListBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (!_module.isJP2HdrSeen()) {
            _repInfo.setMessage (new ErrorMessage 
                (noJP2Hdr, _module.getFilePos ()));
            return false;
        }
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();

        int nFrags = _module.readUnsignedShort (_dstrm);
        if (_boxHeader.getLength () != 0 && len != 14 * nFrags + 2) {
            _repInfo.setMessage 
                (new ErrorMessage ("Fragment Table has invalid length", _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
        }
        _fragmentList = new ArrayList<long[]> (nFrags);
        for (int i = 0; i < nFrags; i++) {
            long offset = _module.readSignedLong (_dstrm);
            long fragLen = _module.readUnsignedInt (_dstrm);
            int dataRef = _module.readUnsignedShort (_dstrm);

            // If dataRef is nonzero, the stream is outside the file,
            // and all we can do is report the reference.  In fact,
            // if any of the fragments are outside the file, we 
            // have to punt.  So we should collect all the
            // fragments and then read the stream.

            if (dataRef != 0) {
                _fragmentList = null;   // no can do fragments
                _repInfo.setMessage (new InfoMessage 
                    ("Document references an external file", _module.getFilePos()));
            }
            else if (_fragmentList != null) {
                long[] frag = new long[2];
                frag[0] = offset;
                frag[1] = fragLen;
                _fragmentList.add (frag);
            }
        }
        finalizeBytesRead ();
        return true;                
    }


    /** Returns the fragment list.  If there are external references
     *  to fragments, returns null; in this case, a warning message
     *  has been added to the RepInfo object. */
    protected List getFragmentList ()
    {
        return _fragmentList;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Fragment List Box";
    }
}
