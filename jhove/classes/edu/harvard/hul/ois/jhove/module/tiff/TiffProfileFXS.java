/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF FX, Profile S.
 *
 *  Image data content is not checked for profile conformance.
 *  Only tags are checked.
 *
 * @author Gary McGath
 *
 */
public class TiffProfileFXS extends TiffFXBase {

    /**
     *  Constructor.
     */
    public TiffProfileFXS ()
    {
        super ();
        _profileText = "TIFF-FX (Profile S)";
        _mimeClass = MIME_FX;
    }


    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  TIFF/FX S profile.  See the TIFF/FX specification for
     *  details.
     */
    public boolean satisfiesThisProfile(IFD ifd) {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;
        if (!satisfiesClass (tifd)) {
            return false;
        }
        
        // Profile S (but not any other fax profile) requires
        // "II", little-endian data.
        if (ifd.isBigEndian()) {
            return false;
        }
        
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int[] bps = niso.getBitsPerSample ();
        if (bps[0] != 1) {
            return false;
        }
        if (niso.getStripOffsets().length > 1) {
            // Image data must be a single strip
            return false;
        }
        
        int resUnit = niso.getSamplingFrequencyUnit();
        if (resUnit != 2 && resUnit != NisoImageMetadata.NULL) {
            return false;
        }
        
        if (niso.getCompressionScheme() != 3) {
            return false;
        }
        if (tifd.getFillOrder () != 2) {
            return false;
        }
        if (niso.getImageWidth () != 1728) {
            return false;
        }
        if (niso.getSamplesPerPixel () != 1) {
            return false;
        }
        long xRes = niso.getXSamplingFrequency ().toLong();
        long yRes = niso.getYSamplingFrequency ().toLong();
        // resolution unit must be inches, so no need to 
        // do metric conversion
        if (xRes != 200 && xRes != 204) {
            return false;
        }
        if (yRes != 98 && yRes != 100 &&
                 yRes != 196 && yRes != 200) {
            return false;
        }
        long t4Opt = tifd.getT4Options ();
        if ((t4Opt & 0X3) != 0) {
            // bits 0 and 1 must be 0
            return false;
        }
        return true;         // passed all tests
    }

}
