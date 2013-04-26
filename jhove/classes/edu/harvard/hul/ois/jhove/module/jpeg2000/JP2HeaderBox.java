/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * JP2 Header Box.
 * See I.5.3 in ISO/IEC 15444-1:2000
 * and ISO/IEC FCD15444-2: 2000, L.9.2
 * 
 *
 * @author Gary McGath
 *
 */
public class JP2HeaderBox extends JP2Box {


    /**
     *  Constructor with superbox.
     */
    public JP2HeaderBox (RandomAccessFile raf, BoxHolder parent)
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
        initBytesRead ();
        hasBoxes = true;
        //int sizeLeft = (int) _boxHeader.getDataLength ();
        if (_module.isJP2HdrSeen ()) {
            _repInfo.setMessage (new ErrorMessage
                        ("Multiple JP2 Header Boxes not allowed",
                         _module.getFilePos ()));
            // Skip the redundant box and set invalid flag,
            // but keep going.
            _repInfo.setValid (false);
            if (_boxHeader.getLength () != 0) {
                _module.skipBytes (_dstrm, 
                    (int) _boxHeader.getDataLength (), 
                    _module);
            }
        }
        _module.setJP2HdrSeen (true);
        
        // In JP2 format, this must come before the Contiguous
        // Codestream
        if (_module.getNCodestreams () > 0) {
            _module.setJP2Compliant (false);
        }
        
        // The JP2 header consists of a variety of boxes,
        // so we keep reading boxes till we run out of bytes.
        //BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        int state = 0;        // state variable for checking progress of boxes
        JP2Box box = null;
        boolean hasCMap = false;
        boolean hasPalette = false;
        while (hasNext ()) {
            box = (JP2Box) next ();
            
            // A JPX, but not a JP2, can have a Label Box
            // before the Image header.
            if (state == 0 && box instanceof LabelBox) {
                state = 1;
                _module.setJP2Compliant (false);
                //box = new LabelBox (this);
                if (!box.readBox ()) {
                    return false;
                }
                _module.addProperty (new Property ("JP2HeaderLabel",
                                PropertyType.STRING,
                                ((LabelBox) box).getLabel ()));
                
                // Read the next box
                box = (JP2Box) next ();
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
                        ("First box of JP2 header must be image header", 
                                _module.getFilePos ()));
                    _repInfo.setWellFormed (false);
                    return false;
                }
            }
            else {
                // Only certain boxes are meaningful in a JP2 Header.
                // However, others should be skipped over, not considered
                // errors.
                if (box instanceof AssociationBox ||
                    box instanceof BPCCBox ||
                    box instanceof ColorSpecBox ||
                    box instanceof PaletteBox ||
                    box instanceof ComponentMapBox ||
                    box instanceof ChannelDefBox ||
                    box instanceof ResolutionBox ||
                    box instanceof ROIBox) {
                        if (!box.readBox ()) {
                            return false;
                    }
                }
                else {
                    box.skipBox ();
                }

            }
        }
            
        
        // Consistency checks
        if (hasCMap && !hasPalette) {
            _repInfo.setMessage (new ErrorMessage
                ("JP2 Header has Component Mapping box without Palette Box",
                 _module.getFilePos ()));
            _repInfo.setValid (false);
        }
        if (!hasCMap && hasPalette) {
            _repInfo.setMessage (new ErrorMessage
                ("JP2 Header has Palette box without Component Mapping Box",
                 _module.getFilePos ()));
            _repInfo.setValid (false);
        }
        // If there were any Associations, add a property for them.
        Property a = makeAssocProperty ();
        if (a != null) {
            _module.addProperty(a);
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "JP2 Header Box";
    }
}
