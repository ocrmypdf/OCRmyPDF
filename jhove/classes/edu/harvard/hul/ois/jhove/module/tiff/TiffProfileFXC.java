/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *
 *  Profile checker for TIFF FX, Profile C (Baseline Color).
 * 
 *  Image data content is not checked for profile conformance.
 *  Only tags are checked.
 *
 *  @author Gary McGath
 *
 */
public class TiffProfileFXC extends TiffFXBase {

    /**
     *  Constructor.
     */
    public TiffProfileFXC ()
    {
        super ();
        _profileText = "TIFF-FX (Profile C)";
        _mimeClass = MIME_FX;
    }


    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  TIFF/FX C profile.  See the TIFF/FX specification for
     *  details.
     */
    public boolean satisfiesThisProfile(IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;
        if (!satisfiesClass (tifd)) {
            return false;
        }
        if (!satisfiesImageWidth (tifd, new int[] 
                {864, 1024, 1216, 1728, 2048, 2432,
                 2592, 3072, 3456, 3648, 4096, 4864} )) {
            return false;
        }
        
        if (!satisfiesSamplesPerPixel(tifd, new int[] {1, 3})) {
            return false;
        }

        if (!satisfiesCompression (tifd, 7)) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation(tifd, 10)) {
            return false;
        }
        if (!satisfiesResolutionUnit (tifd,
                new int[] {2, 3, NisoImageMetadata.NULL} )) {
            return false;
            // NOTE: RFC 2301 (1998) allows 2 or 3, but
            // the 2003 working draft allows only 2 (inch).
            // Watch for change.
        }
        if (!satisfiesSamplesPerPixel(tifd, 
                new int[] {1, 3} )) {
            return false;
        }
        // XResolution must be one of the specified values
        // and equal YResolution
        if (!satisfiesXResolution(tifd,
                new int[] {100, 200, 300, 400} )) {
            return false;
        }
        if (!satisfiesFillOrder (tifd,
                new int[] {1, 2} )) {
            return false;
        }
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        long xRes = niso.getXSamplingFrequency ().toLong ();
        if (xRes != niso.getYSamplingFrequency ().toLong ()) {
            return false;
        }
        if (niso.getSamplingFrequencyUnit() == 3) {
            // Convert from units/cm to units/inch, with rounding
            xRes = perCMtoPerInch ((int) xRes);
        }
        int bps = niso.getBitsPerSample ()[0];
        if (bps != 8 && bps != 12) {
            // NOTE: RFC 2301 (1998) allows 8 or 12 bits per
            // sample, but the 2003 working draft allows only 8.
            // Watch for changes.
            return false;
        }
        
        // Check if image width is suitable to resolution
        int wid = (int) niso.getImageWidth ();
        switch ((int) xRes) {
            case 100:
                if (wid != 864 && wid != 1024 & wid != 1216) {
                    return false;
                }
                break;
            case 200:
                if (wid != 1728 && wid != 2048 & wid != 2432) {
                    return false;
                }
                break;
            
            case 300:
                if (wid != 2592 && wid != 3072 & wid != 3648) {
                    return false;
                }
                break;
            
            case 400:
                if (wid != 3456 && wid != 4096 & wid != 4864) {
                    return false;
                }
                break;
        }
        
        // By my best reading, the colormap is needed only
        // if the Indexed value is 1.
        if (tifd.getIndexed() == 1) {
            if (niso.getColormapRedValue () == null) {
                return false;
            }
        }

        return true;         // passed all tests
    }

}
