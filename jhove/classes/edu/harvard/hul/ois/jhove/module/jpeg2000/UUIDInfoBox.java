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
 * UUID info box.
 * See I.7.3 in ISO/IEC 15444-1:2000
 * 
 * @author Gary McGath
 *
 */
public class UUIDInfoBox extends JP2Box {

    private Property _urlProp;
    private Property _uuidListProp;


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public UUIDInfoBox(RandomAccessFile raf, BoxHolder parent) {
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
            wrongBoxContext ();
            return false;
        }
        initBytesRead ();
        hasBoxes = true;
        int sizeLeft = (int) _boxHeader.getDataLength() ;
        BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        JP2Box box = null;
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }            
            if (box instanceof UUIDListBox ||
                box instanceof UUIDListBox ||
                box instanceof DataEntryURLBox) {
                    box.setBoxHeader(subhdr);
                    box.setDataInputStream(_dstrm);
                    box.setRandomAccessFile (_raf);
                    box.setRepInfo(_repInfo);
                    box.setModule(_module);
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
            _repInfo.setMessage (new ErrorMessage 
                ("Size of contained boxes underruns UUID Info Box", 
                 _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
            
        }
        List<Property> propList = new ArrayList<Property> (2);
        if (_urlProp != null) {
            propList.add (_urlProp);
        }
        if (_uuidListProp != null) {
            propList.add (_uuidListProp);
        }
        _module.addUUIDInfo (new Property ("UUIDInfo",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList));
        finalizeBytesRead ();
        return true;
    }


    /** Sets the URL string.  This will be called from
     *  DataEntryURLBox. 
     */
    protected void setURL(String url) 
    {
        _urlProp = new Property ("URL", PropertyType.STRING, url);
    }
    
    
    /** Sets the UUID list.  The argument is an array
     *  of byte arrays of length 16, or schematically:
     *  <code>byte[][16]</code>.
     */
    protected void setUUIDList (byte[][] uuids)
    {
       List<Property> propList = new ArrayList<Property> (uuids.length); 
       for (int i = 0; i < uuids.length; i++) {
           propList.add (new Property 
                ("UUIDList",
                 PropertyType.BYTE,
                 PropertyArity.ARRAY,
                 uuids[i]));
       }
       _uuidListProp = new Property ("UUIDInfo",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList);
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "UUID Info Box";
    }
}
