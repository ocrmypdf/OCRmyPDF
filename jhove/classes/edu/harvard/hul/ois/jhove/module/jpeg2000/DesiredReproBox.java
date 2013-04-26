/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;

/**
 *
 * Desired Reproductions Box (JPX).
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.15
 * 
 * @author Gary McGath
 *
 */
public class DesiredReproBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public DesiredReproBox(RandomAccessFile raf, BoxHolder parent) {
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
        // Oddly enough, this box is NOT required to be
        // at the top level of the file.  However, there
        // can be only one in the file.
        // It can have multiple subboxes, but the only
        // significant one is the Graphics Technology
        // Standard Output box, which simply holds an
        // ISO profile.
        
        initBytesRead ();
        int sizeLeft = (int) _boxHeader.getDataLength() ;
        BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        JP2Box box = null;
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }
            if (box instanceof GTSOBox) {
                if (!box.readBox ()) {
                    return false;
                }
            }
            else {
                box.skipBox ();
            }
        }

        // There is a NISO property for reporting the
        // profile name.  I should figure out how to
        // extract the name of a profile.
        
        finalizeBytesRead ();
        return false;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Desired Reproductions Box";
    }
}
