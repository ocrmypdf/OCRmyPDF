/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Abstract superclass for the profile checkers for TIFF/DLF
 */
public abstract class TiffProfileDLF extends TiffProfile
{
    public TiffProfileDLF ()
    {
        super ();
    }

    /**
     *  Returns true if the IFD satisfies the requirements
     *  that are common to the bilevel, grayscale, and color
     *  DLF profiles.  The subclasses should call super(ifd)
     *  first, then do additional checking if it returns true.
     *  details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;

        if (!satisfiesPhotometricInterpretation (tifd, new int[] {0, 1} )) {
            return false;
        }
        return true;       // passed all tests
    }

    /** Checks for minimum X and Y resolution.
     *  All of the DLF profiles have similar tests for
     *  XResolution and YResolution. In all cases the
     *  values depend on the ResolutionUnit, which must be
     *  either 2 or 3.
     *
     *  @param tifd  The TiffIFD from which to extract the tags.
     *  @param minUnit2Res  The minimum XResolution and YResolution
     *                      when ResolutionUnit is 2
     *  @param minUnit3Res  The minimum XResolution and YResolution
     *                      when ResolutionUnit is 3
     */

    protected boolean hasMinimumResolution (TiffIFD tifd, double minUnit2Res,
                                            double minUnit3Res) 
    {
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        Rational xrat = niso.getXSamplingFrequency ();
        Rational yrat = niso.getYSamplingFrequency ();
        if (xrat == null || yrat == null) {
            return false;
        }

        int resUnit = niso.getSamplingFrequencyUnit ();
        if (resUnit == 2) {
            if (xrat.toDouble() < minUnit2Res || yrat.toDouble() < minUnit2Res) {
                return false;
            }
        }
        else if (resUnit == 3) {
            if (xrat.toDouble() < minUnit3Res || yrat.toDouble() < minUnit3Res) {
                return false;
            }
        }
        else {
            return false;  // resUnit must be 2 or 3
        }

        return true;       // passed all tests
    }
}
