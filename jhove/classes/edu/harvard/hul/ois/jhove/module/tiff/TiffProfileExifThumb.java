/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

/**
 *  Profile checker for the thumbnail IFD of a
 *  TIFF file potentially meeting the TIFF profile.
 * 
 *  This doesn't go into the _profiles list of TiffIFD,
 *  but rather is one of two (or more?) profiles that must
 *  be checked to determine if the file meets the Exif
 *  profile.  It should be called only for the "thumbnail"
 *  IFD, which is the second top-level IFD.
 * 
 *
 * @author Gary McGath
 *
 * @see  TiffProfileExif
 */
public class TiffProfileExifThumb extends TiffProfile {
    
    /** Compression scheme of the main IFD.  We need to check
     *  our compression against the main IFD's compression. */
    int mainCompression;
    
    public TiffProfileExifThumb ()
    {
        super ();
        // This isn't used directly to report a profile, so the
        // profile text is irrelevant.
        _profileText = null;
    }


    /**
     *  Record the compression scheme of the main IFD; required
     *  for comparison.
     */
    public void setMainCompression (int comp)
    {
        mainCompression = comp;
    }



    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  thumbnail IFD for an
     *  Exif profile.  See the Exif specification for details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;
        if (!satisfiesCompression (tifd, new int [] {1, 6} )) {
            return false;
        }
        
        // If the main IFD is uncompressed, the thumbnail must be too
        if (mainCompression == 1 && 
              tifd.getNisoImageMetadata().getCompressionScheme() != 1) {
            return false;
        }
        return true;
    }
}
