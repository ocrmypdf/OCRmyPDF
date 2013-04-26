/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;


/**
 *  Profile checker for TIFF Pagemaker 6.0.
 */
public final class TiffProfilePagemaker6 extends TiffProfile
{
    public TiffProfilePagemaker6 ()
    {
	super ();
	_profileText = "Adobe PageMaker 6.0";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of the
     *  profile.  See the PageMaker specification for details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;

	/* Check required tags. */
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
	long imageLength = niso.getImageLength ();
	if (imageLength == NisoImageMetadata.NULL ||
	    niso.getImageWidth () == NisoImageMetadata.NULL) {
	    return false;
	}

	boolean so = (niso.getStripOffsets () != null);
	boolean to = (niso.getTileOffsets () != null);
	if ((so && to) || (!so && !to)) {
	    return false;
	}

	if (so) {
	    if (niso.getStripByteCounts () == null) {
		return false;
	    }
	    long rowsPerStrip = niso.getRowsPerStrip ();
	    if (rowsPerStrip == NisoImageMetadata.NULL ||
		rowsPerStrip < 1L || rowsPerStrip > imageLength) {
		return false;
	    }
	}

	if (to) {
	    if (niso.getTileWidth () == NisoImageMetadata.NULL ||
		niso.getTileLength () == NisoImageMetadata.NULL ||
		niso.getTileOffsets () == null ||
		niso.getTileByteCounts () == null) {
		return false;
	    }
	}

	/* Check required values. */
	if (!satisfiesCompression (tifd, new int [] {1, 2, 5, 32773, 32895,
						    32896} )) {
	    return false;
	}

	int pi = niso.getColorSpace ();
	if (pi != 0 && pi != 1 && pi != 2 && pi != 3 && pi != 5 && pi != 8 &&
	    pi != 9) {
	    return false;
	}

	int inkSet = tifd.getInkSet ();
	int spp = niso.getSamplesPerPixel ();
	if (pi == 0 || pi == 1 || pi == 3) {
	    if (spp != 1) {
		return false;
	    }
	}
	else if (pi == 2 || pi == 8 || pi == 9) {
	    if (spp != 3) {
		return false;
	    }
	}
	else if (inkSet == 1) {  /* Only check for RGB, not hi-fi/multi-ink. */
	    if (spp != 4) {
		return false;
	    }
	}

	int [] bps = niso.getBitsPerSample ();
	if (bps != null) {
	    if (pi == 0 || pi == 1 || pi == 3) {
		for (int i=0; i<bps.length; i++) {
		    if (bps[i] != 1 && bps[i] != 2 && bps[i] != 4 &&
			bps[i] != 8) {
			return false;
		    }
		}
	    }
	    else {
		for (int i=0; i<bps.length; i++) {
		    if (bps[i] != 8) {
			return false;
		    }
		}
	    }
	}
	else {
	    return false;
	}

	if (inkSet == 2) {
	    if (tifd.getInkNames () == null ||
		tifd.getNumberOfInks () == IFD.NULL) {
		return false;
	    }
	}

	return true;
    }
}
