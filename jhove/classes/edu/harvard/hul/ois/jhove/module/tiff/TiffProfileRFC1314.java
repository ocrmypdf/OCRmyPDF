/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;


/**
 *  Profile checker for TIFF RFC 1314.
 *
 *  @author Gary McGath
 */
public final class TiffProfileRFC1314 extends TiffProfile
{
    public TiffProfileRFC1314 ()
    {
        super ();
        _profileText = "RFC 1314";
        _mimeClass = MIME_1314;
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

        /* Check required tags. */
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
	if (niso.getImageWidth () != NisoImageMetadata.NULL ||
	    niso.getImageLength () != NisoImageMetadata.NULL ||
	    tifd.getNewSubfileType () != IFD.NULL ||
            niso.getRowsPerStrip () == NisoImageMetadata.NULL ||
            niso.getStripByteCounts () == null ||
	    niso.getStripOffsets () == null ||
	    niso.getXSamplingFrequency () == null ||
	    niso.getYSamplingFrequency () == null) {
            return false;
        }

	/* Check required values. */
        int [] bps = niso.getBitsPerSample ();
        if (bps == null || bps[0] != 1 ) {
            return false;
        }

	if (!satisfiesCompression (tifd, new int [] {1, 3, 4} )) {
            return false;
        }

	if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
            return false;
        }

	if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
	}

	if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
            return false;
        }

        return true;       // passed all tests
    }
}
