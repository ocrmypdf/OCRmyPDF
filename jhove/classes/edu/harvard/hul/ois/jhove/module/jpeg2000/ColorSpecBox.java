/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Color specification box.
 * See I.5.3.3 in ISO/IEC 15444-1:2000
 * and ISO/IEC FCD15444-2: 2000, L.9.4.2
 *
 * @author Gary McGath
 *
 */
public class ColorSpecBox extends JP2Box {

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    (must be JP2HeaderBox or ColorGroupBox)
     */
    public ColorSpecBox (RandomAccessFile raf, BoxHolder parent)
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
              _parentBox instanceof ColorGroupBox)) {
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        int len = (int) _boxHeader.getDataLength ();

        List subProps = new ArrayList (2);
        Property prop = new Property ("ColorSpec", 
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    subProps);
        int meth = ModuleBase.readUnsignedByte (_dstrm, _module);
        if (meth > 2) {
            _module.setJP2Compliant (false);  // only 1-2 recognized by JP2
        }
        subProps.add (_module.addIntegerProperty("Method", meth, 
            JP2Strings.methodStr));

        // Precedence.  Used in JPX only.
        int prec = ModuleBase.readUnsignedByte (_dstrm, _module);
        subProps.add (new Property ("Precedence",
                    PropertyType.INTEGER,
                    new Integer (prec)));
        
        // The approx field provides a litmus test for distinguishing
        // a JP2 file from a JPX.  JP2 may have only 0 for this value;
        // JPX must have a non-zero value.
        int approx = ModuleBase.readUnsignedByte (_dstrm, _module);
        if (approx == 0) {
            _module.setJPXCompliant (false);
            subProps.add (new Property ("Approx",
                    PropertyType.INTEGER,
                    new Integer (0)));
        }
        else {
            _module.setJP2Compliant (false);
            subProps.add (_module.addIntegerProperty("Approx", approx, 
                    JP2Strings.approxStr, 
                    JP2Strings.approxIdx));
        }

        if (meth == 1) {
            // with meth = 1, we have an enumerated colorspace
            long enumCS = _module.readUnsignedInt (_dstrm);
            _module.skipBytes (_dstrm, len - 7, _module);
            Property p;
            p = _module.addIntegerProperty ("EnumCS", (int) enumCS,
                    JP2Strings.enumCSStr);
            subProps.add (p);
        }
        else if (meth == 2 ) {
            // Code by Justin Littman incorporated here.  
            // With meth = 2, the profile must be either a Monochrome
            // Input or a Three-Component Matrix-Based Input profile,
            // as defined in ICC.1:1998-09.
            //Read the ICC profile
            //Skip the header (128 bytes)
            _module.skipBytes(_dstrm, 128, _module);
            //Tag count
            long tagCount = _module.readUnsignedInt(_dstrm);
            HashSet tagSignatureSet = new HashSet();
            for (int i=0; i < tagCount; i++) {
                //Read the tag
                tagSignatureSet.add(_module.read4Chars(_dstrm));
                //Skip the rest of the tag table entry
                _module.skipBytes(_dstrm, 8, _module);                
            }
            
            //Check if Monochrome Input Profile
            if (tagSignatureSet.contains("desc") && 
                    tagSignatureSet.contains("kTRC") && 
                    tagSignatureSet.contains("wtpt") && 
                    tagSignatureSet.contains("cprt")) {
                subProps.add (new Property ("RestrictedICCProfile",
                    PropertyType.STRING,
                    "Monochrome Input Profile"));                
            }
            //Check if Three-Component Matrix-Based Input Profile
            else if (tagSignatureSet.contains("desc") && 
                    tagSignatureSet.contains("rXYZ") && 
                    tagSignatureSet.contains("gXYZ") && 
                    tagSignatureSet.contains("bXYZ") && 
                    tagSignatureSet.contains("rTRC") && 
                    tagSignatureSet.contains("gTRC") && 
                    tagSignatureSet.contains("bTRC") && 
                    tagSignatureSet.contains("wtpt") && 
                    tagSignatureSet.contains("cprt")) {
                subProps.add (new Property ("RestrictedICCProfile",
                    PropertyType.STRING,
                    "Three-Component Matrix-Based Input Profile"));                                
            }
            //Not a valid method 2 box
            else {
                //_module.setJP2Compliant (false);
                _repInfo.setMessage(new ErrorMessage
                        ("Color spec box with method 2 has unrecognized ICC profile", 
                         filePos));
                _repInfo.setValid(false);
            }
        }
        else {
            // We have an ICC profile, or else a method which isn't
            // defined in the specification.  This excludes it
            // from the JP2 profile.
            _module.setJP2Compliant (false);
        }
        // If it's in a JP2 Header, add to the default color specs.
        // If it's in a Color Group Box, add to Compositing Layer
        // properties.
        if (_parentBox instanceof JP2HeaderBox) {
            _module.addColorSpec (prop);
        }
        else if (_parentBox instanceof ColorGroupBox) {
            ((ColorGroupBox) _parentBox).addColorSpec (prop);
        }
        // Skip any bytes we haven't read
        if (_boxHeader.getLength () != 0) {
            _module.skipBytes (_dstrm, 
                (int) (len - (_module.getFilePos () - startBytesRead)), _module);
        }
        finalizeBytesRead ();
        _module.setColorSpecSeen (true);
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Color Specification Box";
    }
}
