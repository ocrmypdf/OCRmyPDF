/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;



/**
 *  Profile checker for TIFF DLF Benchmark for Faithful Digital
 *  Reproductions of Monographs and Serials: black and white.
 */
public final class TiffProfileDLFBW extends TiffProfileDLF
{
    public TiffProfileDLFBW ()
    {
	super ();
	_profileText = "DLF Benchmark for Faithful Digital " +
		"Reproductions of Monographs and Serials: " +
		"black and white";
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

	if (!satisfiesCompression (tifd, new int [] {1, 6} )) {
	    return false;
	}

	if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
	    return false;
	}

	/* XResolution and YResolution >= 600 (inches) or 1520 (cm) */
	if (!hasMinimumResolution (tifd, 600.0, 1520.0)) {
	    return false;
	}

	return true;
    }
}
