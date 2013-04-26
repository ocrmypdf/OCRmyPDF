/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *
 *  Profile checker for TIFF FX, Profile M (Mixed Raster Content).
 * 
 *  Image data content is not checked for profile conformance.
 *  Only tags are checked.
 *
 *  @author Gary McGath
 *
 */
public class TiffProfileFXM extends TiffFXBase {

    /**
     *  Constructor.
     */
    public TiffProfileFXM ()
    {
        super ();
        _profileText = "TIFF-FX (Profile M)";
        _mimeClass = MIME_FX;
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  TIFF/FX M profile.  See the TIFF/FX specification for
     *  details.
     * 
     *  Proper validation should check if the subIFDs are appropriate
     *  to the M profile layer scheme.  However, the existing design
     *  of the TIFF module has almost no understanding of IFD
     *  hierarchies.  This could be an enhancement for a future
     *  release.
     */
    public boolean satisfiesThisProfile(IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;
        if (!satisfiesClass (tifd)) {
            return false;
        }
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (!satisfiesImageWidth (tifd, new int[] 
                {864, 1024, 1216, 1728, 2048, 2432,
                 2592, 3072, 3456, 3648, 4096, 4864} )) {
            return false;
        }
        if (!satisfiesNewSubfileType(tifd, new long[] {16, 18})) {
            return false;
        }
        if (!satisfiesCompression (tifd, 
                new int[] {3, 4, 7, 9, 10})) {
            return false;
            // NOTE: The March 2003 draft allows a compression
            // value of 1 if StripByteCounts contains a 0
            // value, i.e., there is no image data.  Watch
            // for changes.
        }
        if (!satisfiesSamplesPerPixel (tifd,
                new int[] {1, 3, 4} )) {
            return false;
        }
        if (!satisfiesResolutionUnit (tifd,
                new int[] {2, 3, NisoImageMetadata.NULL} )) {
            return false;
        }
        if (!satisfiesPhotometricInterpretation (tifd,
                new int[] {0, 1, 2, 5, 10} )) {
            return false;
            // NOTE: The March 2003 draft allows only 0, 2 and
            // 10.  Watch for change.
        }
        if (!satisfiesFillOrder (tifd,
                new int[] {1, 2} )) {
            return false;
        }
        int bps = niso.getBitsPerSample ()[0];
        if (bps > 16) {
            // NOTE: RFC 2301 (1998) allows 1-16 bits per
            // sample, but the 2003 working draft allows only 1-12.
            // Watch for changes.
            return false;
        }
        int[] imgl = tifd.getImageLayer();
        if (imgl == null || imgl[0] < 1 || imgl[0] > 3) {
            return false;
        }
        
        // Can't have both StripRowCounts and RowsPerStrip
        if (tifd.getStripRowCounts () != null &&
                niso.getRowsPerStrip () != NisoImageMetadata.NULL) {
            return false;
        }
        // By my best reading, the colormap is needed only
        // if the Indexed value is 1.
        if (tifd.getIndexed() == 1) {
            if (niso.getColormapRedValue () == null) {
                return false;
            }
        }

        return true;         // passed all tests
    }

}
