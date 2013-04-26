/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;


/**
 *  Profile checker for TIFF/EP.
 *  For TIFF/EP, no default values may be assumed.
 *  At the moment, we have no way to determine which values
 *  were defaulted, so defaults are shown even if the file
 *  satisfies the EP profile.
 * 
 *  This class also serves as the base class for DNG,
 *  which is defined as a restricted subset of TIFF/EP.
 */
public class TiffProfileEP extends TiffProfile
{
    public TiffProfileEP ()
    {
	super ();
	_profileText = "TIFF/EP (ISO 12234-2:2001)";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  TIFF/EP profile.  See the TIFF/EP specification for details.
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
	    niso.getBitsPerSample () == null ||
	    tifd.getImageDescription () == null ||
	    niso.getXSamplingFrequency () == null ||
	    niso.getYSamplingFrequency () == null ||
	    niso.getScannerManufacturer () == null ||
	    (niso.getScannerModelName () == null &&
	     niso.getScannerModelNumber () == null) ||
	    niso.getScanningSoftware() == null ||
	    tifd.getImageDescription () == null ||
	    tifd.getCopyright () == null ||
	    niso.getDateTimeCreated () == null ||
	    tifd.getDateTime () == null ||
	    tifd.getTIFFEPStandardID () == null) {
		 return false;
	}
	/* Must have either a full complement of strip tags or
	 * a full complement of tile tags.
	 */
	if (!(niso.getStripOffsets () != null &&
		niso.getRowsPerStrip () != NisoImageMetadata.NULL &&
		niso.getStripByteCounts () != null) &&
	    !(niso.getTileWidth () != NisoImageMetadata.NULL &&
		niso.getTileLength () != NisoImageMetadata.NULL &&
		niso.getTileOffsets () != null &&
		niso.getTileByteCounts () != null)) {
		return false;
	}

	long subfile = tifd.getNewSubfileType ();
	if (subfile != 0 && subfile != 1) {
	    return false;
	}

	if (!satisfiesResolutionUnit (tifd, new int [] {1, 2, 3} )) {
	    return false;
	}

	if (!satisfiesOrientation (tifd, new int [] {NisoImageMetadata.NULL,
						    1, 3, 6, 8, 9} )) {
	    return false;
	}

	int pInterpretation = niso.getColorSpace ();
	if (!(pInterpretation == 1 ||
	  pInterpretation == 2 ||
	  pInterpretation == 6 ||
	  pInterpretation == 32803 ||
	  pInterpretation > 32767)) {
		return false;
	}

	int config = niso.getPlanarConfiguration ();
	if (config != 1 && config != 2) {
	    return false;
	}

	int method = niso.getSensor ();
	if (method == NisoImageMetadata.NULL || method < 0 || method > 8) {
	    return false;
	}

	if (pInterpretation == 32803) {
	    if (tifd.getCFARepeatPatternDim () == null) {
		return false;
	    }
	    if (tifd.getCFAPattern () == null) {
		return false;
	    }
	}

	/* Make sure PhotometricInterpretation and SamplesPerPixel
	 * are compatible. 
	 */
	int samplesPerPixel = niso.getSamplesPerPixel ();
	if (pInterpretation == 1 || pInterpretation == 32803) {
	    if (samplesPerPixel != 1) {
		return false;
	    }
	}
	if (pInterpretation == 2 || pInterpretation == 6) {
	    if (samplesPerPixel != 3) {
		return false;
	    }
	}
	if (pInterpretation == 6) {
	    if (niso.getYCbCrCoefficients() == null ||
		niso.getYCbCrSubSampling () == null ||
		niso.getYCbCrPositioning () == NisoImageMetadata.NULL ||
		niso.getReferenceBlackWhite () == null) {
		    return false;
	    }
	}
	// meteringMode and exposureProgram checks deleted, per Bugzilla #33
	
	int compression = niso.getCompressionScheme ();
	if (compression != NisoImageMetadata.NULL) {
        // Corrected 6-Jan-04 per Bugzilla #33
	    if (!(compression == 1 || compression == 7 ||
		  compression > 32767)) {
		return false;
	    }
	}
	return true;
    }
}
