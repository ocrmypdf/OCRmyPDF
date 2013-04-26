/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Codestream Header box.
 * This is similar to a JP2HeaderBox, and has many of the same subboxes,
 * but applies to a single codestream.
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.3
 * 
 * @author Gary McGath
 *
 */
public class CodestreamHeaderBox extends JP2Box {

    private Codestream curCodestream;
    

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   Must be null or the TopLevelBoxHolder
     */
    public CodestreamHeaderBox(RandomAccessFile raf, BoxHolder parent) {
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
        if (_parentBox != null) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        hasBoxes = true;

        int nch = _module.getNCodestreamHeaders () + 1;
        _module.setNCodestreams (nch);
        curCodestream = _module.getCodestream (nch);

        int sizeLeft = (int) _boxHeader.getDataLength() ;
        BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        int state = 0;        // state variable for checking progress of boxes
        JP2Box box = null;
        while (hasNext ()) {
            box = (JP2Box) next ();            
            if (state == 0 && box instanceof LabelBox) {
                state = 1;
                if (!box.readBox ()) {
                    return false;
                }
                curCodestream.setLabelProperty (new Property ("Label",
                                PropertyType.STRING,
                                ((LabelBox) box).getLabel ()));
                
                // Read the next box
                box = (JP2Box) next ();
                if (box == null) {
                    break;
                }
            }
            // First box, except perhaps for the label box,
            // is the image header.
            else if (state <= 1) {
                if (box instanceof ImageHeaderBox) {
                    state = 2;
                    if (!box.readBox ()) {
                        return false;
                    }
                }
                else {
                    _repInfo.setMessage (new ErrorMessage
                        ("First box of Codestream Header must be image header", 
                                _module.getFilePos ()));
                    _repInfo.setWellFormed (false);
                    return false;
                }
            }
            else {
                if (box instanceof BPCCBox ||
                    box instanceof PaletteBox ||
                    box instanceof ComponentMapBox ||
                    box instanceof ROIBox) {
                        if (!box.readBox ()) {
                            return false;
                        }
                }
                else {
                    // Other boxes are legal; skip over them
                    box.skipBox ();
                }
            }
        }
        finalizeBytesRead ();
        return true;
    }
    
    /** Returns the associated Codestream object. */
    protected Codestream getCodestream ()
    {
        return curCodestream;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Codestream Header Box";
    }
}
