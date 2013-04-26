/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.List;

/**
 * Fragment Table Box (JPX).
 * See L.9.6 in ISO/IEC FCD15444-2:2000.
 * @author Gary McGath
 *
 */
public class FragmentTableBox extends JP2Box {

    
    
    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    or TopLevelBoxHolder
     */
    public FragmentTableBox (RandomAccessFile raf, BoxHolder parent)
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
        boolean retval = true;
        initBytesRead ();
        hasBoxes = true;
        //int state = 0;        // state variable for checking progress of boxes
        JP2Box box = (JP2Box) next ();
        if (box == null) {
            return false;       // empty box can't be right
        }
        // OK, how do I deal with subboxes?  Should be able to handle
        // them the same way as in the module, except that a different
        // set of boxes is acceptable.  The dispatcher (in BoxHeader?)
        // may need to be given a list of boxes that are acceptable for
        // any given context.  For the top-level module, the list
        // should probably (maybe) be in BoxHeader, but for boxes, the
        // list of acceptable subboxes must be provided explicitly.
        // Maybe an additional argument in the BoxHeader constructor.
        if (box instanceof FragmentListBox) {
            FragmentListBox fbox = (FragmentListBox) box;
            if (!fbox.readBox ()) {
                return false;
            }
            List fragList = fbox.getFragmentList();
            // fragList will be null if external files are referenced.
            if (fragList != null) {
                //App app = _module.getApp();
                JhoveBase base = _module.getBase ();
                int bufSize = base.getBufferSize ();
                FragmentInputStream fragStream = 
                    new FragmentInputStream (fragList, _raf, bufSize);
                DataInputStream dfstrm = new DataInputStream (fragStream);
                int ncs = _module.getNCodestreams () + 1;
                _module.setNCodestreams (ncs);
                Codestream curCodestream = _module.getCodestream (ncs);
                long len = 
                    _boxHeader.getLength () == 0 ?
                    0 : _boxHeader.getDataLength ();
                ContCodestream ccs = 
                    new ContCodestream (_module, dfstrm, len);
                // Oh, FOOBAR.  This creates another situation in which
                // we can't count the bytes being read. Buf if we're
                // going to a random access file, that may all be
                // rendered moot anyway.   
                retval = ccs.readCodestream (curCodestream, _repInfo);    
            }            
        }
        else {
            _repInfo.setMessage (new ErrorMessage 
                ("Invalid fragment table", _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
        }
        finalizeBytesRead ();
        return retval;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Fragment Table Box";
    }
}
