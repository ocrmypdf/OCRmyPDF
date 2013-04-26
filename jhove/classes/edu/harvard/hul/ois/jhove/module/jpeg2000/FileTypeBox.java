/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * File Type Box.
 * See I.5.2 in ISO/IEC 15444-1:2000
 * 
 * A File Type box can occur only as the first thing after the
 * Signature Box, so this will be invoked only directly from
 * the Module.
 * 
 * @author Gary McGath
 *
 */
public class FileTypeBox extends JP2Box {

    /**
     * Constructor.
     */
    public FileTypeBox(RandomAccessFile raf) {
        super(raf);
    }

    /**
     * The constructor with superbox is meaningless.
     */
    public FileTypeBox(RandomAccessFile raf, JP2Box parent) {
        super (raf);
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
        String brand = _module.read4Chars(_dstrm);
        _module.addProperty (new Property ("Brand",
                PropertyType.STRING,
                brand));
        // 12 bytes have been read
        
        // Brand indicates intended compliance
        if (!"jp2 ".equals (brand)) {
            _module.setJP2Compliant (false);
        }
        if (!"jpx ".equals (brand)) {
            _module.setJPXCompliant (false);
        }

        long minv = _module.readUnsignedInt(_dstrm);
        _module.addProperty (new Property ("MinorVersion",
                PropertyType.LONG,
                new Long (minv)));
        // 16 bytes have been read
        
        // Read the compatibility list.  It takes up the rest
        // on the box length.
        int ncomp = (((int) _boxHeader.getLength ()) - 16) / 4;
        if (ncomp < 1) {
            _repInfo.setMessage (new ErrorMessage
                        ("Empty compatibility list in File Type Box",
                         _module.getFilePos ()));
            _repInfo.setWellFormed (false);
            return false;
        }
        List<String> compList = new ArrayList<String> (ncomp);
        boolean eflag = false;
        StringBuffer hexcitem = new StringBuffer (8);
        for (int i = 0; i < ncomp; i++) {
            String citem = _module.read4Chars (_dstrm);
            
            // Some files have a count of entries, which isn't supposed
            // to be there.  If we see any nulls, report an ill-formed condition.
            // For each entry, we build a hex string in hexcitem just in case
            // it's necessary to report the string in hex.
            char[] cbytes = citem.toCharArray();
            boolean binflag = false;
            for (int j = 0; j < cbytes.length; j++) {
                int ch = (int) cbytes[j];
                hexcitem.append (Integer.toHexString(ch));
                if (ch == 0 || ch >= 0X7F) {
                    binflag = true;
                    if (!eflag) {
                        eflag = true;   // Avoid multiple report of same error
                        _repInfo.setValid (false);
                        _repInfo.setMessage (new ErrorMessage
                            ("Non-ASCII characters in compatibility item of File Type Box",
                             _module.getFilePos ()));
                    }
                    
                }
            }
            if (!binflag) {
                compList.add (citem);
            }
            else {
                compList.add (hexifyString (citem));
            }
        }
        _module.addProperty (new Property ("Compatibility",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    compList));
        // All the bytes have been read
        return true;
    }
    
    private String hexifyString (String s) 
    {
        StringBuffer retval = new StringBuffer (2 * s.length () + 2);
        retval.append ("0X");
        char[] chs = s.toCharArray();
        for (int i = 0; i < chs.length; i++) {
            String hs = Integer.toHexString ((int) chs[i]);
            // Pad to 2 characters
            if (hs.length () == 1) {
                retval.append ('0');
            }
            retval.append (hs);
        }
        return retval.toString ();
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "File Type Box";
    }
}
