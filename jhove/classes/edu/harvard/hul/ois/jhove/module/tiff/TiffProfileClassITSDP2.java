/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-SD/P2.
 *
 *  The TIFF/IT spec states that "TIFF/IT-SD/P2 is a simplified file
 *  format profile for screened data image (SD) data and can be
 *  considered a constrained subset of TIFF/IT-SD specifically
 *  intended for simpler implementation."
 *
 *  There is no TIFF/IT-SD/P1.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITSDP2 extends TiffProfileClassIT
{
    public TiffProfileClassITSDP2 ()
    {
        super ();
	_profileText = "TIFF/IT-SD/P2 (ISO 12639:2003)";
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

        /* Check required values. */

	int[] bps = niso.getBitsPerSample ();
	if (bps[0] != 1) {
	    return false;
	}

	if (!satisfiesResolutionUnit (tifd, new int[] {2, 3})) {
	    return false;
	}

        if (!satisfiesSamplesPerPixel (tifd, new int[] {1, 4})) {
            return false;
        }

        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }

        if (!satisfiesCompression (tifd, new int [] {1, 4, 8} )) {
            return false;
        }

	if (!satisfiesPlanarConfiguration (tifd, 2)) {
	    return false;
	}

        int inkSet = tifd.getInkSet ();
        if (inkSet != 1 ) {
            return false;
        }

	int numInks = tifd.getNumberOfInks ();
	if (numInks != 4) {
	    return false;
	}

	if (!satisfiesOrientation (tifd, 1)) {
	    return false;
	}

        /* Tags which must NOT be defined */
        if (tifd.getDocumentName () != null ||
	    niso.getScannerModelName () != null ||
	    tifd.getPageName () != null ||
	    niso.getHostComputer () != null ||
	    tifd.getSite () != null ||
	    tifd.getColorSequence () != null ||
	    tifd.getIT8Header () != null) {
            return false;
        }

        return true;
    }
}
