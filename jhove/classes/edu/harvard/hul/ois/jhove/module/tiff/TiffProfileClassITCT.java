/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-CT.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITCT extends TiffProfileClassIT
{
    public TiffProfileClassITCT ()
    {
        super ();
	_profileText = "TIFF/IT-CT (ISO 12639:1998)";
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

        /* Check required tags.*/
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (niso.getBitsPerSample () == null ||
	    niso.getSamplesPerPixel () == NisoImageMetadata.NULL ||
            niso.getSamplingFrequencyUnit () == NisoImageMetadata.NULL) {
            return false;
        }

        /* Check required values. */

        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }

        if (!satisfiesCompression (tifd, new int [] {1, 32895} )) {
            return false;
        /* NOTE: If compression is 32895, RasterPadding must be
           0, 1, 2, 9, or 10.  Fix this when RasterPadding support is
           implemented. */
        }

        int inkSet = tifd.getInkSet ();
        if (inkSet != 1 && inkSet != 2) {
            return false;
        }
        String seq = tifd.getColorSequence ();
        if (seq == null || "CMYK".equals (seq)) {
            if (inkSet != 1) {
                return false;
            }
        }

        int spp = niso.getSamplesPerPixel ();
        int numInks = tifd.getNumberOfInks ();
        if (numInks != NisoImageMetadata.NULL && numInks != spp) {
            return false;
        }
        return true;
    }
}
