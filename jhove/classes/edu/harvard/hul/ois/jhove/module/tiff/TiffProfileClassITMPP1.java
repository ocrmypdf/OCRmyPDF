/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-MP/P1.
 *
 *  The TIFF/IT spec states that "TIFF/IT-MP/P1 is a simplified
 *  image file format profile for monochrome continuous tone
 *  picture image (MP) data and can be considred a constrained
 *  subset of TIFF/IT-MP specifically intended for
 *  simpler implementation."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITMPP1 extends TiffProfileClassIT
{
    public TiffProfileClassITMPP1 ()
    {
        super ();
        _profileText =  "TIFF/IT-MP/P1 (ISO 12639:1998)";
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

        if (!satisfiesNewSubfileType (tifd, 0)) {
            return false;
        }

	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int[] bps = niso.getBitsPerSample ();
        if (bps == null || bps[0] != 8) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, 1 )) {
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
        
        if (!satisfiesResolutionUnit (tifd, new int [] { 2, 3} )) {
            return false;
        }
        
        if (!satisfiesDotRange (tifd, 0, 255)) {
            return false;
        }
       
        int ind = tifd.getImageColorIndicator ();
        if (ind != 0 && ind != 1) {
            return false;
        }
        
        // ImageColorValue is defined if ImageColorIndicator=1
        if (ind == 1) {
            if (tifd.getImageColorValue () == IFD.NULL) {
                return false;
            }
        }
        
        // PixelIntesityRange={0,255}
        int [] pir = tifd.getPixelIntensityRange ();
        if (pir == null || pir.length < 2) {
            return false;
        }
        if (pir[0] != 0 || pir[1] != 255) {
            return false;
        }
        
        // Tags which must NOT be defined
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
