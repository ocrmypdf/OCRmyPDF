/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-HC/P1.
 *
 *  The TIFF/IT spec states that "TIFF/IT-HC/P1 is a simplified
 *  image file format profile for high resolution continuous tone
 *  (HC) image data and can be considered a constrained subset
 *  of TIFF/IT-HC specifically intended for simpler implementation."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITHCP1 extends TiffProfileClassIT
{
    public TiffProfileClassITHCP1 ()
    {
        super ();
        _profileText =  "TIFF/IT-HC/P1 (ISO 12639:1998)";
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

        /* Check required tags. */
        if (!satisfiesSamplesPerPixel (tifd, 4)) {
            return false;
        }
        
        // BitsPerSample must be {8, 8, 8, 8}
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int[] bps = niso.getBitsPerSample ();
        if (bps == null || bps.length < 4) {
            return false;
        }
        for (int i=0; i<4; i++) {
            if (bps[i] != 8) {
                return false;
            }
        }

        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }

        if (!satisfiesCompression (tifd, 32895)) {
            return false;
        }

        if (!satisfiesPlanarConfiguration (tifd, 1)) {
            return false;
        }
        
        if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
            return false;
        }

        int inkSet = tifd.getInkSet ();
        if (inkSet != 1) {
            return false;
        }

        if (tifd.getNumberOfInks () != 4) {
            return false;
        }
        
        // DotRange={0,255}
        if (!satisfiesDotRange (tifd, 0, 255)) {
            return false;
        }

        int trans = tifd.getTransparencyIndicator ();
        if (trans != 0 && trans != 1) {
            return false;
        }

        // The tags DocumentName, Model, PageName, HostComputer, 
        // Site, and ColorSequence must NOT be defined
        
        if (tifd.getDocumentName () != null ||
	    niso.getScannerModelName () != null ||
	    tifd.getPageName () != null ||
	    niso.getHostComputer () != null ||
	    tifd.getSite () != null ||
	    tifd.getColorSequence () != null) {
            return false;
        }

        return true;
    }
}
