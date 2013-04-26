/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Profile checker for TIFF Class F.
 *
 *  @author Gary McGath
 */
public final class TiffProfileClassF extends TiffProfile
{
    
    /* Significant changes February 2, 2004 */
    
    /**
     *  Constructor.
     */
    public TiffProfileClassF ()
    {
        super ();
        _profileText = "Class F";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of a
     *  Class F profile.  See the Class F specification for
     *  details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!(ifd instanceof TiffIFD)) {
            return false;
        }
        TiffIFD tifd = (TiffIFD) ifd;

        /* Check required tags. */
        NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (niso.getImageLength () == NisoImageMetadata.NULL ||
            niso.getStripOffsets () == null ||
            niso.getRowsPerStrip () == NisoImageMetadata.NULL ||
            niso.getStripByteCounts () == null ||
            tifd.getPageNumber () == null ||
            niso.getScanningSoftware () == null) {
            return false;
        }

        /* Check required values. */
        if (!satisfiesCompression (tifd, new int[] {3, 4} )) {
            return false;
        }

        int fo = tifd.getFillOrder();
        if (fo != 1 && fo != 2) {
            return false;
        }

        int cmpr = niso.getCompressionScheme ();
        if (cmpr == 3) {
            // T4 options are also known as Group 3 options
            long t4opt = tifd.getT4Options ();
            if (t4opt != 0 && t4opt != 1 && 
                t4opt != 4 && t4opt != 5) {
                return false;
            }
        }
        else if (cmpr == 4) {            long t4opt = tifd.getT4Options ();
            // T6 options are also known as Group 4 options
            long t6opt = tifd.getT6Options ();
            if (t6opt != 2) {
                return false;
            }
        } 

        //long wid = niso.getImageWidth ();
        if (!satisfiesImageWidth (tifd, 
            new int [] {1728, 2048, 
                2432, 2592, 3072, 3648, 3456, 4096, 4864} )) {
            return false;
        }

        if (!satisfiesNewSubfileType (tifd, 2)) {
            return false;
        }

        if (!satisfiesResolutionUnit (tifd, new int [] {2, 3} )) {
            return false;
        }

        if (!satisfiesXResolution (tifd, 
            new int[] {204, 200, 300, 400, 408} )) {
            return false;
        }

        if (!satisfiesYResolution (tifd, 
            new int[] {98, 196, 100, 200, 300, 391, 400} )) {
            return false;
        }

        int[] bps = niso.getBitsPerSample ();
        if (bps == null || bps[0] != 1 ) {
            return false;
        }

        if (!satisfiesPhotometricInterpretation (tifd, new int [] {0, 1} )) {
            return false;
        }

        if (!satisfiesSamplesPerPixel (tifd, 1)) {
            return false;
        }
        
        // Only certain combinations of ImageWidth and resolution are
        // permitted.
        int wid = (int) niso.getImageWidth ();
        int xres = (int) niso.getXSamplingFrequency ().toLong ();
        int yres = (int) niso.getYSamplingFrequency ().toLong ();
        switch (wid) {
            case 1728:
            case 2048:
            case 2432:
            if (!(xres == 204 && yres == 391) ||
                 (xres == 200 && yres == 100) ||
                 (xres == 200 && yres == 200)) {
                return false;
            }
            break;
            
            case 2592:
            case 3072:
            case 3648:
            if (!(xres == 300 && yres == 300)) {
                return false;
            }
            break;
            
            case 3456:
            case 4096:
            case 4864:
            if (!(xres == 408 && yres == 391) ||
                 (xres == 400 && yres == 400)) {
                return false;
            }
            break;
            
            default:
            break;
        }
        
        return true;
    }
}
