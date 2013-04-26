/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-SD.
 *
 *  The TIFF/IT spec states that "TIFF/IT-SD makes use of all
 *  the features and functionality supported by the TIFF and
 *  TIFF/IT fields appropriate to prescreened (copydot)
 *  colour separation images."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITSD extends TiffProfileClassIT
{
    public TiffProfileClassITSD ()
    {
        super ();
	_profileText = "TIFF/IT-SD (ISO 12639:2003)";
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

	String seq = tifd.getColorSequence ();
	if (seq != null && !"CMYK".equals (seq) && !"YMCK".equals (seq)) {
	    return false;
	}
        return true;
    }
}
