/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Composition Box (JPX).
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.10
 * 
 * @author Gary McGath
 *
 */
public class CompositionBox extends JP2Box {

    private List<Property> instSets;
    private long _height;
    private long _width;
    private int _loop;
    

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public CompositionBox(RandomAccessFile raf, BoxHolder parent) {
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
        JP2Box box;
        if (_parentBox != null) {
            // May not occur in a superbox
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        hasBoxes = true;
        instSets = new LinkedList<Property> ();

        // A Composition box is a superbox which contains one
        // Composition Options Box followed by 0 (?) or more
        // Instruction Set Boxes.  
        //BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        //subhdr.readHeader ();
        if (!hasNext ()) {
            emptyBox ();
            return false;
        }
        
        // Read the options box
        box = (JP2Box) next ();
        if (!(box instanceof CompOptionsBox)) {
            _repInfo.setMessage (new ErrorMessage
                ("First box in Composition Box must be " +                    "Composition Options Box",
                 _module.getFilePos()));
            _repInfo.setWellFormed (false);
            return false;
        }
        long sizeLeft = _boxHeader.getDataLength () - box.getLength ();
//        box = new CompOptionsBox (this);        
//        box.setBoxHeader (subhdr);
//        box.setDataInputStream (_dstrm);
//        box.setRandomAccessFile (_raf);
//        box.setModule (_module);
//        box.setRepInfo (_repInfo);
        if (!box.readBox ()) {
            return false;
        }

        // Read the instruction set boxes
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }
            if (box instanceof InstructionSetBox) {
                if (!box.readBox ()) {
                    return false;
                }
            }
            else {
                box.skipBox ();
            }
        }
        // A box has to be at least 8 bytes long, and there must
        // not be any bytes left over.
        if (sizeLeft != 0) {
            // Underran the superbox -- get out quick
            superboxUnderrun ();
            return false;
            
        }
        finalizeBytesRead ();
        
        List<Property> propList = new ArrayList<Property> (4);
        propList.add (new Property ("Width",
                PropertyType.LONG,
                new Long (_width)));
        propList.add (new Property ("Height",
                PropertyType.LONG,
                new Long (_height)));
        propList.add (new Property ("Loop",
                PropertyType.INTEGER,
                new Integer (_loop)));
        if (!instSets.isEmpty ()) {
            propList.add (new Property ("InstructionSets",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                instSets));
        }
        _module.addProperty (new Property ("Composition",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList));
        return true;
    }

    /** Add an instruction set property to the list.
     *  This is called from InstructionSetBox.
     */
    protected void addInstSet (Property p) 
    {
        instSets.add (p);
    }
    
    /** Set the height value.  This is called from
     *  CompositionBox. */
    protected void setHeight (long h)
    {
        _height = h;
    }


    /** Set the height value.  This is called from
     *  CompositionBox. */
    protected void setWidth (long w)
    {
        _width = w;
    }
    
    
    /** Set the loop value.  This is called from
     *  CompositionBox. */
    protected void setLoop (int l)
    {
        _loop = l;
    }
}
