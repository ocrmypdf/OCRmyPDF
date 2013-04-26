/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Color Group Box.
 * See ISO/IEC FCD15444-2: 2000, L.9.4.1
 * 
 * 
 * @author Gary McGath
 *
 */
public class ColorGroupBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    (must be a ComposLayerHdrBox)
     */
    public ColorGroupBox(RandomAccessFile raf, BoxHolder parent) {
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
        // A Color Group box consists of 0 or more color specification 
        // boxes.  It is allowed only in a Compositing Layer Header box.
        if (!(_parentBox instanceof ComposLayerHdrBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        int sizeLeft = (int) _boxHeader.getDataLength() ;
        BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        int state = 0;        // state variable for checking progress of boxes
        JP2Box box = null;
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }
            if (box instanceof ColorSpecBox) {
                if (!box.readBox ()) {
                    return false;
                }
            }
            else {
                box.skipBox ();
            }
        }
        
        finalizeBytesRead ();
        return false;
    }

    /** Adds a color spec property to the parent Compositing Layer
     *  Header Box. */
    protected void addColorSpec (Property p)
    {
        ((ComposLayerHdrBox) _parentBox).addColorSpec (p);
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Color Group Box";
    }
}
