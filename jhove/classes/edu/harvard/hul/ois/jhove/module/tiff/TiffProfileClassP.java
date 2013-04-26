/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class P (Baseline Palette color).
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassP extends TiffProfile
{
    public TiffProfileClassP ()
    {
        super ();
        _profileText =  "Baseline palette-color (Class P)";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  Class P profile.  See the TIFF 6.0 specification for
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
            niso.getColormapBitCodeValue () == null ||
            niso.getColormapRedValue () == null ||
            niso.getColormapGreenValue () == null ||
            niso.getColormapBlueValue () == null) {
            return false;
        }

        /* Check required values. */
        int[] bps = niso.getBitsPerSample ();
        if (bps == null || (bps[0] != 4 && bps[0] != 8)) {
            return false;
        }

	if (!satisfiesCompression (tifd, new int [] {1, 32773} )) {
            return false;
        }

	if (!satisfiesPhotometricInterpretation (tifd, 3)) {
            return false;
        }

	if (!satisfiesResolutionUnit (tifd, new int [] {1, 2, 3} )) {
            return false;
        }

        return true;
    }
}
