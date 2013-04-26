/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;

/**
 * Number list box.
 * Provides a list of numbers with types.
 * It's apparently used only within an Association
 * box, so it simply makes a property available.
 * 
 * See ISO/IEC FCD15444-2: 2000, L.9.12
 *
 * @author Gary McGath
 *
 */
public class NumberListBox extends JP2Box {

    private Property[] propArray;

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public NumberListBox(RandomAccessFile raf, BoxHolder parent) {
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

        int numEntries = (int) _boxHeader.getDataLength () / 4;
        if (numEntries > 0) {
            propArray = new Property[numEntries];
            for (int i = 0; i < numEntries; i++) {
                long num = _module.readUnsignedInt (_dstrm);
                // High byte is type, low three bytes are the
                // number.
                int typeByte = (int) ((num & 0XFF000000L) >> 24);
                int numValue = (int) (num & 0XFFFFFF);
                App app = _module.getApp ();
                Property[] p = new Property[2];
                p[0] = _module.addIntegerProperty("Type", 
                        typeByte, 
                        JP2Strings.numberListTypeStr);
                p[1] = new Property ("Value",
                        PropertyType.INTEGER,
                        new Integer (numValue));
                propArray[i] = new Property ("Number",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        p);
            }
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns a Property which describes the Box, for use
     *  by Association boxes and perhaps others.
     */
    protected Property getSelfPropDesc () 
    {
        if (propArray != null) {
            return new Property (DESCRIPTION_NAME,
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                propArray);
        }
        else {
            // A number list with no numbers isn't explicitly illegal
            return null;
        }
    }


    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Number List Box";
    }
}
