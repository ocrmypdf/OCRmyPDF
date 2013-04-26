/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-BP/P1.
 *
 *  The TIFF/IT spec states that "TIFF/IT-BP/P1 is a simplified
 *  image file format profile for binary picture (BP) image
 *  data and can be considred a constrained
 *  subset of TIFF/IT-BP specifically intended for
 *  simpler implementation."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITBPP1 extends TiffProfileClassIT
{
    public TiffProfileClassITBPP1 ()
    {
        super ();
        _profileText =  "TIFF/IT-BP/P1 (ISO 12639:1998)";
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
        
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (!satisfiesNewSubfileType (tifd, 0)) {
            return false;
        }

        if (!satisfiesCompression (tifd, 1)) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation (tifd, 0)) {
            return false;
        }
        
        if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
        }
        
        if (!satisfiesResolutionUnit (tifd, new int[] {2, 3} )) {
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
