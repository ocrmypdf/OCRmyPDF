/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-MP.
 *
 *  The TIFF/IT spec states that "TIFF/IT-MP makes use of all
 *  the features and functionality supported by the TIFF and
 *  TIFF/IT fields appropriate to monochrome continuous
 *  tone picture images."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITMP extends TiffProfileClassIT
{
    public TiffProfileClassITMP ()
    {
        super ();
        _profileText =  "TIFF/IT-MP (ISO 12639:1998)";
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
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (niso.getBitsPerSample () == null) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, new int [] {1, 32895} )) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
            return false;
        }
        
        // RasterPadding=0,1,2,9, or 10, but only if Compression=32895
        if (niso.getCompressionScheme () == 32895) {
            int pad = tifd.getRasterPadding ();
            if (pad != 0 && pad != 1 && pad != 2 && pad != 9 && pad != 10) {
                return false;
            }
        }
        
        if (!satisfiesImageColorIndicator (tifd, new int [] {0, 1} )) {
            return false;
        }
        
        // ImageColorValue is defined if ImageColorIndicator=1
	int ind = tifd.getImageColorIndicator ();
        if (ind == 1) {
            if (tifd.getImageColorValue () == IFD.NULL) {
                return false;
            }
        }
        return true;
    }
}
