/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for the DNG raw IFD.
 *  
 * 
 * @author Gary McGath
 * 
 * @see TiffProfileDNG
 *
 */
public class TiffProfileDNG extends TiffProfile {

    /** PhotometricInterpretation for CFA space */
    public final static int CFA = 32803;
    
    /* PhotometricInterpretation for LinearRaw space */
    public final static int LINEAR_RAW = 34892;
    
    /* Set to true if anything directly contravenes DNG,
     * or a previous profile has reported as DNG */
//    private boolean notDNG;     

    /* An IFD has been seen with a photometricInterpretation
     * specific to DNG. */
//    private boolean photoInterpOK;
    
    /* Orientation has been specified. */
//    private boolean orientationSeen;
    
    /* DNGVersion tag has been seen */
//    private boolean dngVersionSeen;
    
    /* UniqueCameraModel tag has been seen */
//    private boolean uniqueCameraModelSeen;
    
    /* AsShotNeutral tag has been seen.  This isn't required,
     * but is mutually exclusive with AsShotWhiteXY. */
    private boolean asShotNeutralSeen;
    
    /* AsShotWhiteXY tag has been seen.  This isn't required,
     * but is mutually exclusive with AsShotNeutral. */
    private boolean asShotWhiteXYSeen;
    
    /**
     * 
     */
    public TiffProfileDNG() {
        super();
        _profileText =  "DNG 1.0.0.0 (September 2004)";
        //notDNG = false;
        //photoInterpOK = false;
        //orientationSeen = false;
        //dngVersionSeen = false;
        //uniqueCameraModelSeen = false;
    }

    /**
     *  Returns true if the IFD satisfies the requirements
     *  of the profile.  See the documentation for
     *  details.
     */
    public boolean satisfiesThisProfile(IFD ifd) {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;

        /* Check if this is the "raw" profile.  */
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        int pInterpretation = niso.getColorSpace ();
        if (!(pInterpretation == CFA || pInterpretation == LINEAR_RAW)) {
            return false;
        }
        /* BitsPerSample must be 8 to 32, and same for all samples */
        int[] bps = niso.getBitsPerSample();
        if (bps != null) {
            int bpsval = bps[0];
            if (bpsval < 8 || bpsval > 32) {
                return false;
            }
            for (int i = 0; i < bps.length; i++) {
                if (bpsval != bps[i]) {
                    return false;
                }
            }
        }
        
        /* If the photometric interpretation is CFA, there must be
         * certain other tags. */
        if (pInterpretation == CFA) {
            if (tifd.getCFAPlaneColor() == null ||
                tifd.getCFARepeatPatternDim() == null ||
                tifd.getCFAPattern() == null) {
                return false;
            }
        }

        /* Orientation is required. */
        if (niso.getOrientation() == NisoImageMetadata.NULL) {
            return false;
        }
        
        /* Compression must be 1 or 7 */
        int compression = niso.getCompressionScheme ();
        if (compression != NisoImageMetadata.NULL) {
            if (!(compression == 1 || compression == 7)) {
                return false;
            }
        }
        
        return true;
    }

}
