/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Cross Reference Box (JPX).
 * A Cross Reference Box may be found in a Codestream
 * Header, Compositing Layer Header, or Association box.
 * When it is encountered, the box to which it refers
 * should be substituted for the Cross Reference Box.
 * Interesting features of the box are that it
 * isn't all in one place, but is
 * scattered through multiple locations by a fragment list,
 * and it doesn't follow standard superbox rules.
 * 
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.7
 * 
 * @author Gary McGath
 *
 */
public class CrossRefBox extends JP2Box {

    DataInputStream fragStream;


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    or TopLevelBoxHolder
     */
    public CrossRefBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (! (_parentBox instanceof CodestreamHeaderBox ||
               _parentBox instanceof ComposLayerHdrBox ||
               _parentBox instanceof AssociationBox)) {
            wrongBoxContext ();
            return false;
        }
        initBytesRead ();
        hasBoxes = true;
        // Skip the box type
        _module.read4Chars (_dstrm);
        bytesLeft -= 4;
        JP2Box box = null;
        if (hasNext ()) {
            box = (JP2Box) next ();
        }
        if (!(box instanceof FragmentListBox)) {
            _repInfo.setMessage (new ErrorMessage 
                    ("Cross Reference Box does not contain Fragment List Box",
                     _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
        }
        box.readBox ();
        List fragList = ((FragmentListBox) box).getFragmentList();
        //App app = _module.getApp();
        JhoveBase base = _module.getBase ();
        int bufSize = base.getBufferSize ();
        fragStream = new DataInputStream
            (new FragmentInputStream (fragList, _raf, bufSize));
        finalizeBytesRead ();
        return false;
    }

    /** Returns a DataInputStream based on a FragmentInputStream
     * so that the fragments can be read as a single entity.
     */
    public DataInputStream getCrossRefStream ()
    {
       return fragStream;
    }


    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Cross Reference Box";
    }
}
