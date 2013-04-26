/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class Y (Baseline YCbCr).
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassY extends TiffProfile
{
    public TiffProfileClassY ()
    {
        super ();
        _profileText =  "Extension YCbCr (Class Y)";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  Class Y profile.  See the TIFF 6.0 specification for
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
            niso.getYSamplingFrequency () == null ||
            niso.getReferenceBlackWhite () == null) {
            return false;
        }

        /* Check required values. */
	if (!satisfiesSamplesPerPixel (tifd, 3)) {
            return false;
	}

        int[] bps = niso.getBitsPerSample ();
        if (bps == null || bps.length < 3 || 
        	bps[0] != 8 || bps[1] != 8 || bps[2] != 8) {
            return false;
        }

	if (!satisfiesCompression (tifd, new int [] {1, 5, 6} )) {
            return false;
        }

	if (!satisfiesPhotometricInterpretation (tifd, 6)) {
            return false;
        }

	if (!satisfiesResolutionUnit (tifd, new int  [] {1, 2, 3} )) {
            return false;
        }

        return true;
    }
}
