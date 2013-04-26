/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;
//import edu.harvard.hul.ois.jhove.module.TiffModule;

/**
 * IFD 0 of a DNG document must satisfy this profile.  It doesn't
 * actually have to be a "thumbnail" in the sense of containing
 * a low-resolution image, but it has to contain the "IFD 0"
 * tags specified by DNG. In addition,
 * some other document must satisfy <code>TiffProfileDNG</code>.
 * 
 * @author Gary McGath
 * @see TiffProfileDNG
 */
public class TiffProfileDNGThumb extends TiffProfile {

    /**
     * 
     */
    public TiffProfileDNGThumb() {
        super();
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  DNG thumbnail profile.
     */
    public boolean satisfiesThisProfile(IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;
        /* Check required tags. */
        if (tifd.getDNGVersion() == null) {
            return false;
        }

        if (tifd.getNewSubfileType() != 1) {
            return false;
        }
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        
        if (tifd.getAsShotNeutral () != null && 
                tifd.getAsShotWhiteXY () != null) {
            // There can be only one
            return false;
        }

        if (tifd.getUniqueCameraModel () == null) {
            return false;
        }

        /* The specification says that PhotometricInterpretation
         * must be 1 or 2 for a thumbnail -- but there's no requirement
         * that this BE a thumbnail.  So that requirement appears
         * to be moot. */
        return true;
    }

}
