/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-BP.
 *
 *  The TIFF/IT spec states that "TIFF/IT-BP makes use of all
 *  the features and functionality supported by the TIFF and
 *  TIFF/IT fields appropriate to binary picture images."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITBP extends TiffProfileClassIT
{
    public TiffProfileClassITBP ()
    {
        super ();
        _profileText =  "TIFF/IT-BP (ISO 12639:1998)";
    }

    /**
     *  Returns true if the IFD satisfies the requirements
     *  of the profile.  See the documentation for
     *  details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!super.satisfiesThisProfile (ifd)) {
            return false;
        }
        
	// We now know it's a TiffIFD
	TiffIFD tifd = (TiffIFD) ifd;
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int [] bps = niso.getBitsPerSample ();
        if (bps == null || bps[0] != 1) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, 1)) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation (tifd, new int[] {0, 1} )) {
            return false;
        }
        
        if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
        }

        /* ImageColorIndicator=0,1, or 2; BackgroundColorIndicator=0,1, or 2; 
	 * ImageColorIndicator=1, but only if ImageColorValue is defined; 
	 * BackgroundColorIndicator=1,
	 * but only if BackgroundColorValue is defined.
	 */
        int [] valueVec;
        if (tifd.getImageColorValue () != IFD.NULL) {
            valueVec = new int [] {1};
        }
        else {
            valueVec = new int [] {0, 1, 2};
        }
        if (!satisfiesImageColorIndicator (tifd, valueVec)) {
            return false;
        }
        
        if (tifd.getBackgroundColorValue () != IFD.NULL) {
            valueVec = new int [] {1};
        }
        else {
            valueVec = new int [] {0, 1, 2};
        }
        if (!satisfiesBackgroundColorIndicator (tifd, valueVec)) {
            return false;
        }
        
        return true;
    }
}
