/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-CT/P1.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITCTP1 extends TiffProfileClassIT
{
    public TiffProfileClassITCTP1 ()
    {
        super ();
        _profileText = "TIFF/IT-CT/P1 (ISO 12639:1998)";
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

        // We now know that this is a TiffIFD
        TiffIFD tifd = (TiffIFD) ifd;

        /* Check required tags.*/
        if (!satisfiesNewSubfileType (tifd, 0)) {
            return false;
        }
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();

        // bps must be { 8, 8, 8, 8 }
        int [] bps = niso.getBitsPerSample ();
        if (bps == null || bps.length != 4) {
            return false;
        }
        for (int i = 0; i < 4; i++) {
            if (bps[i] != 8) {
                return false;
            }
        }

        if (!satisfiesCompression (tifd, 1 )) {
            return false;
        }

        if (!satisfiesPhotometricInterpretation (tifd, 5)) {
            return false;
        }

        if (!satisfiesOrientation (tifd, 1)) {
            return false;
        }

        if (!satisfiesSamplesPerPixel (tifd, 4)) {
            return false;
        }

        if (!satisfiesPlanarConfiguration (tifd, 1)) {
            return false;
        }

        if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
            return false;
        }

        int inkSet = tifd.getInkSet ();
        if (inkSet != 1) {
            return false;
        }

        int numInks = tifd.getNumberOfInks ();
        if (numInks != 4) {
            return false;
        }

        if (!satisfiesDotRange (tifd, 0, 255)) {
            return false;
        }

        /* Tags which must NOT be defined */
        if (tifd.getDocumentName () != null ||
	    niso.getScannerModelName () != null ||
	    tifd.getPageName () != null ||
	    niso.getHostComputer () != null ||
	    tifd.getSite () != null ||
	    tifd.getColorSequence () != null ||
	    tifd.getIT8Header() != null) {
            return false;
        }

        return true;
    }
}
