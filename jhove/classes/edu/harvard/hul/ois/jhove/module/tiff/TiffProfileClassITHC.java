/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-HC.
 *
 *  The TIFF/IT spec states that "TIFF/IT-HC makes use of all
 *  the features and functionality supported by the TIFF and
 *  TIFF/IT fields appropriate to high resolution continuous
 *  tone images."
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITHC extends TiffProfileClassIT
{
    public TiffProfileClassITHC ()
    {
        super ();
        _profileText =  "TIFF/IT-HC (ISO 12639:1998)";
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
        if (niso.getBitsPerSample () == null ||
            niso.getSamplesPerPixel () == NisoImageMetadata.NULL) {
            return false;
        }
        
        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }

        if (!satisfiesCompression (tifd, 32895)) {
            return false;
        }

        if (!satisfiesPlanarConfiguration (tifd, 1)) {
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

		// Per footnote: If NumberOfInks tag is used, it must have the
		// same value as SamplesPerPixel.  This requirement doesn't
		// apply to P1 or P2.
        int spp = niso.getSamplesPerPixel ();
        int numInks = tifd.getNumberOfInks ();
        if (numInks != IFD.NULL && numInks != spp) {
            return false;
        }

        int trans = tifd.getTransparencyIndicator ();
        if (trans != 0 && trans != 1) {
            return false;
        }

        return true;
    }
}
