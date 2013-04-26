/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class B (Baseline Bilevel).
 */
public final class TiffProfileClassB extends TiffProfile
{
    public TiffProfileClassB ()
    {
	super ();
	_profileText = "Baseline bilevel (Class B)";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  Class B profile.  See the TIFF 6.0 specification for
     *  details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;

	/* Check required tags. */
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
	if (niso.getImageWidth () == NisoImageMetadata.NULL ||
	    niso.getImageLength () == NisoImageMetadata.NULL ||
	    niso.getStripOffsets () == null ||
	    niso.getRowsPerStrip () == NisoImageMetadata.NULL ||
	    niso.getStripByteCounts () == null ||
	    niso.getXSamplingFrequency () == null ||
	    niso.getYSamplingFrequency () == null) {
	    return false;
	}

	/* Check required values. */
	if (niso.getSamplesPerPixel () > 1) {
	    return false;
	}
        int [] bps = niso.getBitsPerSample ();
        if (bps == null || (bps[0] > 1)) {
            return false;
        }

	if (!satisfiesCompression (tifd, new int [] {1, 2, 32773} )) {
	    return false;
	}

	if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
	    return false;
	}

	if (!satisfiesResolutionUnit (tifd, new int [] {1, 2, 3} )) {
	    return false;
	}

	return true;
    }
}
