/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;



/**
 *  Profile checker for GeoTIFF.
 */
public final class TiffProfileGeoTIFF extends TiffProfile
{
    public TiffProfileGeoTIFF ()
    {
        super ();
        _profileText = "Baseline GeoTIFF 1.0";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of the
     *  the profile.  See the GeoTIFF specification for details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;

        if (tifd.getGeoKeyDirectoryTag () == null) {
            return false;
        }
    
        /* Exactly one of modelTiepointTag and modelTransformationTag
         * must be present. */
        boolean hasModelTiepoint =
            (tifd.getModelTiepointTag() != null);
        boolean hasModelTransformation =
            (tifd.getModelTransformationTag() != null);
        if ((hasModelTiepoint && hasModelTransformation) ||
                (!hasModelTiepoint && !hasModelTransformation)) {
            return false;    
        }
        return true;
    }
}
