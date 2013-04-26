/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;



/**
 *  Profile checker for TIFF DLF Benchmark for Faithful Digital
 *  Reproductions of Monographs and Serials: grayscale.
 */
public final class TiffProfileDLFGray extends TiffProfileDLF
{
    public TiffProfileDLFGray ()
    {
	super ();
	_profileText = "DLF Benchmark for Faithful Digital " +
		"Reproductions of Monographs and Serials: " +
		"grayscale and white";
    }

    /**
     *  Returns true if the IFD satisfies the requirements
     *  of the profile.  See the documentation for
     *  details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;

	if (!satisfiesCompression (tifd, new int [] {1, 5, 32773} )) {
	    return false;
	}

	if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
	    return false;
	}

	if (!satisfiesSamplesPerPixel (tifd, new int [] {1} )) {
	    return false;
	}

	int[] bps = tifd.getNisoImageMetadata ().getBitsPerSample ();
	if (bps == null || bps[0] != 8) {
	    return false;
	}

	/* XResolution and YResolution >= 300 (in) or 760 (cm) */
	if (!hasMinimumResolution (tifd, 300.0, 760.0)) {
	    return false;
	}

	return true;
    }
}
