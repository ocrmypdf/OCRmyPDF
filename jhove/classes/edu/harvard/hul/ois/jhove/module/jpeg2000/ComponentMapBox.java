/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Component Mapping Box.
 * See I.5.3.5 in ISO/IEC 15444-1:2000
 *
 * @author Gary McGath
 *
 */
public class ComponentMapBox extends JP2Box {


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ComponentMapBox (RandomAccessFile raf, BoxHolder parent)
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
        if (!(_parentBox instanceof JP2HeaderBox ||
              _parentBox instanceof CodestreamHeaderBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();

        int len = (int) _boxHeader.getDataLength ();
        int ncomp = len / 4;
        Property[] parray = new Property[ncomp];
        App app = _module.getApp ();
        
        // Build the array of properties for each component.
        // Components potentially have lots of stuff attached
        // to them, so probably I should define a Component
        // class.  Need to determine how the Component Mapping
        // relates to component information in a codestream.
        // Or maybe this doesn't have anything to do with it.
        for (int i = 0; i < ncomp; i++) {
            Property[] cprop = new Property[3];
            int index = _module.readUnsignedShort (_dstrm);
            cprop[0] = new Property ("ComponentIndex",
                        PropertyType.INTEGER,
                        new Integer (index));
            int mtyp = ModuleBase.readUnsignedByte (_dstrm, _module);
            cprop[1] = _module.addIntegerProperty ("MTyp", mtyp,
                        JP2Strings.mtypStr);
            int pcol = ModuleBase.readUnsignedByte (_dstrm, _module);
            cprop[2] = new Property ("PaletteComponent",
                        PropertyType.INTEGER,
                        new Integer (pcol));
            parray[i] = new Property ("Component",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        cprop);
        }
        
        // put constructed property into the Module
        Property cmProp = new Property ("ComponentMapping",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                parray);
        if (_parentBox instanceof CodestreamHeaderBox) {
            Codestream cs = ((CodestreamHeaderBox) _parentBox).getCodestream ();
            cs.setCompMapProperty (cmProp);
        }
        else {
            _module.addProperty (cmProp);
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Component Mapping Box";
    }
}
