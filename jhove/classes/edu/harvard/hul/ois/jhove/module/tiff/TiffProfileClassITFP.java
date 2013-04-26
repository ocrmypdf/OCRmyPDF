/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-FP.
 *
 *  The TIFF/IT spec states that "TIFF/IT-FP provides a mechanism for
 *  associating image files of the different types that make up a 
 *  final page."  Note that Jhove profiles are applied to individual
 *  IFD levels, so this profile does not check the relationships among
 *  IFDs which are part of the FP specification.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITFP extends TiffProfileClassIT
{
    public TiffProfileClassITFP ()
    {
        super ();
        _profileText =  "TIFF/IT-FP";
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

	// We now know this is a TiffIFD
	TiffIFD tifd = (TiffIFD) ifd;
        
        if (tifd.getImageDescription () == null) {
            return false;
        }

        // BitsPerSample=4 or 8 or {8,8,8} or {8,8,8,8} or undefined 
        // (consistent with PhotometricInterpretation)
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int [] bps = niso.getBitsPerSample ();
        if (!(bps == null ||
	      (bps.length == 1 && (bps[0] == 4 || bps[0] == 8)) ||
	      (bps.length == 3 && bps[0] == 8 && bps[1] == 8 && bps[2] == 8) ||
	      (bps.length == 4 && bps[0] == 8 &&
	       bps[1] == 8 && bps[2] == 8 && bps[3] == 8))) {
            return false;
        }
        
        
        // NewSubfileType bit 3=1
        long nsft = tifd.getNewSubfileType ();
        if ((nsft & 8) == 0) {
            return false;
        }

        if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1, 2,
								  5} )) {
            return false;
        }
        
        // SamplesPerPixel=3 or 4 or undefined (consistent with 
        // PhotometricInterpretation)
        if (!satisfiesSamplesPerPixel (tifd, new int [] {3, 4,
						 NisoImageMetadata.NULL} )) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, 1)) {
            return false;
        }

        if (!satisfiesPlanarConfiguration (tifd, 1)) {
            return false;
        }
        
        // InkSet=1, but only if PhotometricInterpretation=5
        // NumberOfInks=4, but only if PhotometricInterpretation=5
        // DotRange={0,255}, but only if PhotometricInterpretation=5
        int pint = niso.getColorSpace ();
        int inkSet = tifd.getInkSet ();
        int nInks = tifd.getNumberOfInks ();
        if (pint == 5 && (inkSet != 1 || nInks != 4 ||
			  !satisfiesDotRange (tifd, 0, 255))) {
            return false;
        }
        return true;
    }
}
