/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Association Box.
 * 
 * An AssociationBox can occur in pretty much any superbox
 * or at the top level.  It simply establishes an association
 * between boxes.  
 *
 * See ISO/IEC FCD15444-2: 2000, L.9.11
 * 
 * @author Gary McGath
 *
 */
public class AssociationBox extends JP2Box {



    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    or TopLevelBoxHolder
     */
    public AssociationBox(RandomAccessFile raf, BoxHolder parent) {
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
        hasBoxes = true;
        int sizeLeft = (int) _boxHeader.getDataLength ();

        // Label and Number List boxes are given as examples, but
        // there is actually no restriction; an Association Box
        // can associate any arbitrary collection of boxes.
        // In order to avoid doubling (squaring?) the complexity
        // of the Module, only Image, Number List, Association and XML
        // boxes are reported in detail. 
        
        JP2Box box = null;
        List boxProps = new LinkedList ();
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }
            if (!box.readBox ()) {
                return false;
            }
            Property sdProp = box.selfDescProperty ();
            if (sdProp != null) {
                boxProps.add (sdProp);
            }
        }
        // Hierarchically add any association properties to the
        // property list.
        if (!associations.isEmpty ()) {
            boxProps.add (new Property ("Associations",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    associations));
        }
        Property assocProp = new Property
                    ("Association",
                     PropertyType.PROPERTY,
                     PropertyArity.LIST,
                     boxProps);
        if (_parentBox != null) {
            _parentBox.addAssociation (assocProp);
        }
        else {
            _module.addAssociationProp (assocProp);
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns a Property which describes the Box, for use
     *  by Association boxes and perhaps others.
     *  An Association box can recursively contain other
     *  Association boxes.  Since an Association box adds
     *  Association properties to its ancestors, This just
     *  returns null to avoid duplicate reporting.
     */
    protected Property selfDescProperty () {
        return null;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Association Box";
    }
}
