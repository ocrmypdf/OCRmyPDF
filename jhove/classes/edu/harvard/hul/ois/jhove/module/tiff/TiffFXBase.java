/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *
 * Base class for all profiles under TIFF/FX.
 * All TIFF/FX profiles should call TiffFXBase.satisfiesClass
 * to establish that common requirements are met.
 * 
 * @author Gary McGath
 *
 */
public abstract class TiffFXBase extends TiffProfile {

    /** Tiff/FX-specific tags. */
    public static final int
        GLOBALPARAMETERSIFD = 400,
        STRIPROWCOUNTS = 559;

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /* Conversion table from units/inch to units/cm */
    private int[] cmInchTab[] = {
        {80, 204},
        {160, 408},
        {38, 98},   // really 38.5
        {77, 196},
        {154, 391}
    };

    /**
     *  Test for common requirements of all Tiff/FX profiles.
     *  Subclasses should call <code>satisfiesClass()</code> from their
     *  <code>satisfiesThisProfile()</code> method to avoid redundant code.
     *  If this method returns <code>false</code>, the IFD does not
     *  meet the requirements of any TIFF/FX profile.  Calling this
     *  also guarantees that the image length, image width,
     *  bits per sample, X resolution (sampling frequency),
     *  Y resolution and page number values are non-null objects.
     */
    protected boolean satisfiesClass (TiffIFD ifd)
    {
        /* Check required tags. */
        NisoImageMetadata niso = ifd.getNisoImageMetadata ();
        if (niso.getImageLength () == NisoImageMetadata.NULL ||
            niso.getStripOffsets () == null ||
            niso.getImageWidth () == NisoImageMetadata.NULL ||
            niso.getBitsPerSample () == null ||
            niso.getColorSpace () == NisoImageMetadata.NULL ||
            niso.getCompressionScheme () == NisoImageMetadata.NULL ||
            // colorSpace == photometricInterpretation
            niso.getXSamplingFrequency () == null ||
            niso.getYSamplingFrequency () == null ||
            ifd.getNewSubfileType () == IFD.NULL ||
            ifd.getPageNumber () == null) {
            return false;
        }
     
        // If compression method is 3, T4 options must be specified
        if (niso.getCompressionScheme () == 3) {
            if (ifd.getT4Options () == IFD.NULL) {
                return false;
            }
        }
        return true;        // placeholder
    }
    
    /**
     *  Convert a units/cm value to a units/inch value.
     *  For expected values, we use a table lookup to avoid
     *  rounding problems.  If a value isn't in the table,
     *  we do a rounded conversion.
     */
    protected int perCMtoPerInch (int res)
    {
        for (int i = 0; i < cmInchTab.length; i++) {
            int[] pair = cmInchTab[i];
            if (pair[0] == res) {
                return pair[1];
            }
        }
        // No table match; use rounding.
        return (int) ((res * 2.54) + 0.5);
    }
}
