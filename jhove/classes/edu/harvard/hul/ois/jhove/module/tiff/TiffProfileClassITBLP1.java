/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-BL/P1.
 *
 *  The TIFF/IT spec states that "TIFF/IT-BL/P1 is a simplified
 *  image file format profile for binary line art (BL) image
 *  data and can be considered a constrained
 *  subset of TIFF/IT-BL specifically intended for
 *  simpler implementation."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITBLP1 extends TiffProfileClassIT
{
    public TiffProfileClassITBLP1 ()
    {
        super ();
        _profileText =  "TIFF/IT-BL/P1 (ISO 12639:1998)";
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

	TiffIFD tifd = (TiffIFD) ifd;
        
        if (!satisfiesNewSubfileType (tifd, 0)) {
        	return false;
        }
        
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int [] bps = niso.getBitsPerSample ();
        if (bps == null || bps[0] != 1) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, 32898)) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation (tifd, 0)) {
            return false;
        }
        
        if (!satisfiesOrientation (tifd, 1)) {
	    return false;
        }
        
        if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
        }

	if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
	    return false;
	}
      
        /* ImageColorIndicator=0,1, or 2; BackgroundColorIndicator=0,1, or 2; 
	 * ImageColorIndicator=1, but only if ImageColorValue is defined; 
	 * BackgroundColorIndicator=1,
	 *but only if BackgroundColorValue is defined.
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
        
        /* Tags which must NOT be defined */
        if (tifd.getDocumentName () != null ||
	    niso.getScannerModelName () != null ||
	    tifd.getPageName () != null ||
	    niso.getHostComputer () != null ||
	    tifd.getSite () != null ||
	    tifd.getColorSequence () != null ||
	    tifd.getIT8Header() != null) {
            return false;
        }

        return true;
    }
}
