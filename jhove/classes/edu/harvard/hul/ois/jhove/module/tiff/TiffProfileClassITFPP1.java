/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class IT-FP/P1.
 *
 *  TIFF/IT-FP/P1 is a simplified form of TIFF/IT-FP.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassITFPP1 extends TiffProfileClassIT
{
    public TiffProfileClassITFPP1 ()
    {
        super ();
        _profileText =  "TIFF/IT-FP/P1 (ISO 12639:1998)";
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

        // Tags which must be present
        if (tifd.getImageDescription () == null ||
                tifd.getXPosition () == null || 
                tifd.getYPosition () == null) {
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

        if (!satisfiesOrientation (tifd, 1)) {
            return false;
        }

        if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
            return false;
        }

        if (!satisfiesPlanarConfiguration (tifd, 1)) {
            return false;
        }
        
        if (!satisfiesCompression (tifd, 1)) {
            return false;
        }

        // NumberOfInks=4, but only if PhotometricInterpretation=5
        // DotRange={0,255}, but only if PhotometricInterpretation=5
        int pint = niso.getColorSpace ();
        int nInks = tifd.getNumberOfInks ();
        if (pint == 5 && (nInks != 4 || !satisfiesDotRange (tifd, 0, 255))) {
            return false;
        }


        /* Tags which must NOT be defined */
        if (tifd.getDocumentName () != null ||
            niso.getScannerModelName () != null ||
            tifd.getPageName () != null ||
            niso.getHostComputer () != null ||
            tifd.getSite () != null ) {
            return false;
        }

        return true;
    }
}
