/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-LW.
 *
 *  The TIFF/IT spec states that "TIFF/IT-LW makes use of all
 *  the features and functionality supported by the TIFF and
 *  TIFF/IT fields appropriate to line art images."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITLW extends TiffProfileClassIT
{
    public TiffProfileClassITLW ()
    {
        super ();
        _profileText =  "TIFF/IT-LW (ISO 12639:1998)";
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
        if (tifd.getColorTable () == null) {
            return false;
        }

	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int[] bps = niso.getBitsPerSample ();
        if (bps[0] != 8) {
            return false;
        }

        /* Check required values. */
        if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
        }
        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }
        /* NOTE: If compression is 32895, RasterPadding must be
	 * 0, 1, 2, 9, or 10.  Fix this when RasterPadding support is
	 * implemented. */
        if (!satisfiesCompression (tifd, 32896)) {
            return false;
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

        // Per footnote h, this applies to LW, LW/P1 and LW/P2
        int spp = niso.getSamplesPerPixel ();
        int numInks = tifd.getNumberOfInks ();
        if (numInks != IFD.NULL && numInks != spp) {
            return false;
        }
        return true;
    }
}
