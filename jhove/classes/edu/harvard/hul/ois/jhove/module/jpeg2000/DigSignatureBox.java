/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.security.*;
import java.util.*;

/**
 * Digital Signature Box (JPX).
 * See ISO/IEC FCD15444-2: 2000, L.9.17
 * 
 * Only the MD5 and SHA-1
 * algorithms are supported.
 *
 * @author Gary McGath
 *
 */
public class DigSignatureBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public DigSignatureBox(RandomAccessFile raf, BoxHolder parent) {
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
        int sizeLeft = (int) _boxHeader.getDataLength ();
        // This may occur "anywhere in the file."  Does that
        // mean that all superboxes should check it as a possible
        // subbox?
        
        List<Property> propList = new ArrayList<Property> (10);
        JhoveBase je = _module.getBase ();
        boolean raw = je.getShowRawFlag ();
        int styp = ModuleBase.readUnsignedByte (_dstrm, _module);
        if (styp > 5) {
            // Known signature types are 0-5
            _repInfo.setMessage (new ErrorMessage 
                    ("Unknown digital signature type",
                     _module.getFilePos ()));
            _repInfo.setValid (false);
        }
        propList.add (_module.addIntegerProperty ("Type", 
                    styp, JP2Strings.digitalSigTypeStr));
 
        int ptyp = ModuleBase.readUnsignedByte (_dstrm, _module);
        if (ptyp > 1) {
            _repInfo.setMessage (new ErrorMessage
                    ("Unknown digital signature pointer type",
                     _module.getFilePos ()));
            _repInfo.setValid (false);
        }
        propList.add (_module.addIntegerProperty ("PointerType", 
                    styp, JP2Strings.digitalSigPtrTypeStr));
        sizeLeft -= 2;
        
        long off = 0;
        long len = 0;
        if (ptyp == 1) {
            off = _module.readSignedLong (_dstrm);
            len = _module.readSignedLong (_dstrm);
            propList.add (new Property ("Offset",
                    PropertyType.LONG,
                    new Long (off)));
            propList.add (new Property ("Length",
                    PropertyType.LONG,
                    new Long (len)));
            sizeLeft -= 8;
        }
        
        byte[] data = new byte[sizeLeft];
        ModuleBase.readByteBuf(_dstrm, data, _module);
        
        if (styp == 0 || styp == 1) {
            try {
                // If the whole file is indicated, set the
                // parameters accordingly
                if (ptyp == 0) {
                    off = 0;
                    len = _raf.length ();
                }
                propList.add (new Property ("Valid",
                    PropertyType.BOOLEAN,
                    new Boolean (isSigValid 
                        (styp, off, len, data))));
            }
            catch (NoSuchAlgorithmException e) { 
                // In the unlikely event the algorithms aren't
                // available, just don't report validity.  
            }
            catch (IOException f) {}
        }
        
        _module.addDigitalSignatureProp (new Property 
            ("DigitalSignature",
             PropertyType.PROPERTY,
             PropertyArity.LIST,
             propList));
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Digital Signature Box";
    }



    /* Check if the signature is valid. Only applicable
     * for styp of 0 (MD5) or 1 (SHA-1). */
    private boolean isSigValid (int styp,
                long off, long len,
                byte[] data)
                throws NoSuchAlgorithmException,
                    IOException
    {
        MessageDigest digest;
        if (styp == 0) {
            digest = MessageDigest.getInstance ("MD5");
        }
        else {
            digest = MessageDigest.getInstance ("SHA-1");
        }
        
        // With the new robustness of RAFInputStream, it should
        // no longer be necessary to save the file position.
        //long savePos = _raf.getFilePointer ();
        
        // If the whole file is indicated, set the parameters
        // accordingly
        try {
            _raf.seek (off);
            int buflen = (len < 65536 ? (int) len : 65536);
            byte[] buf = new byte[buflen];
            while (len > 0) {
                int btr = (len < buflen ? (int) len : buflen);
                int bytesRead = _raf.read (buf, 0, btr);
                digest.update (buf, 0, bytesRead);
            }
            byte[] digestVal = digest.digest ();
            
            // Check if we suffer from indigestion
            if (digestVal.length != data.length) {
                return false;
            }
            for (int i = 0; i < data.length; i++) {
                if (digestVal[i] != data[i]) {
                    return false;
                }
            }
            // Our digestion is good
            return true;
        }
        catch (IOException e) {
            return false;   // most likely invalid range
        }
        
    }

}
