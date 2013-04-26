/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *
 *  Profile checker for TIFF FX, Profile L (Lossless Color).
 * 
 *  Image data content is not checked for profile conformance.
 *  Only tags are checked.
 *
 *  @author Gary McGath
 *
 */
public class TiffProfileFXL extends TiffFXBase {


    /**
     *  Constructor.
     */
    public TiffProfileFXL ()
    {
        super ();
        _profileText = "TIFF-FX (Profile L)";
        _mimeClass = MIME_FX;
    }



    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  TIFF/FX L profile.  See the TIFF/FX specification for
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

        // I can't make sense of whether compression mode 7 is
        // allowed (since Profile L implementors are required to
        // implement profile C) or not (since only 10 is mentioned
        // under Profile L).  Since the compression scheme is the
        // defining characteristic of JBIG, I assume it must be 10.
        if (!satisfiesCompression (tifd, 10 )) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation(tifd,
                new int[] {2, 5, 10 } )) {
            return false;
        }
        if (!satisfiesResolutionUnit (tifd,
                new int[] {2, 3, NisoImageMetadata.NULL} )) {
            // NOTE: RFC 2301 (1998) allows 2 or 3, but
            // the 2003 working draft allows only 2 (inch).
            // Watch for change.
            return false;
        }
        if (!satisfiesSamplesPerPixel(tifd, 
                new int[] {1, 3, 4} )) {
            return false;
        }
        // XResolution must be one of the specified values
        // and equal YResolution
        if (!satisfiesXResolution(tifd,
                new int[] {100, 200, 300, 400} )) {
            return false;
        }
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (niso.getXSamplingFrequency ().toLong () != 
                  niso.getYSamplingFrequency ().toLong ()) {
            return false;
        }
        if (!satisfiesIndexed (tifd, new int[] {0, 1} )) {
            return false;
        }
        if (!satisfiesFillOrder (tifd,
                new int[] {1, 2} )) {
            return false;
        }
        int bps = niso.getBitsPerSample ()[0];
        if (bps > 16) {
            // NOTE: RFC 2301 (1998) allows 1-16 bits per
            // sample, but the 2003 working draft allows only 1-12.
            // Watch for changes.
            return false;
        }
        
        if (tifd.getIndexed() == 1) {
            if (niso.getColormapRedValue () == null) {
                return false;
            }
        }

        return true;         // passed all tests
    }

}
