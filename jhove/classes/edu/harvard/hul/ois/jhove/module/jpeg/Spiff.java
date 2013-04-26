/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

/**
 * Static methods and data for SPIFF Jpeg files.
 * 
 * @author Gary McGath
 *
 */
public class Spiff {

    /* Definitions of SPIFF tags. */
    public final static int
        EOD = 1,
        XFER_CHARACTERISTICS = 2,
        IMAGE_ORIENTATION = 3,
        THUMBNAIL = 4,
        IMAGE_TITLE = 5,
        IMAGE_DESC = 6,
        TIME_STAMP = 7,
        VERSION_IDENT = 8,
        CREATOR_ID = 9,
        PROTECTION_INDICATOR = 0XA,
        COPYRIGHT_INFO = 0X0C,
        CONTACT_INFO = 0X0D,
        TILE_INDEX = 0X0E,
        SCAN_INDEX = 0X0F,
        SETREF = 0X10;

    /* Color space to NISO mapping array. */
    private final static int[] nisoColor = {
        0,            // 0 bilevel, white is 0
        6,            // 1 YCbCr (1)
        -1,           // 2 other
        6,            // 3 YCbCr (2)
        6,            // 4 YCbCr (3)
        -1,           // 5 reserved
        -1,           // 6 reserved
        -1,           // 7 reserved
        1,            // 8 grayscale (black is 0)
        -1,           // 9 PhotoYCC
        2,            // 10 RGB
        -1,           // 11 CMY
        5,            // 12 CMYK
        -1,           // 13 YCCK
        8,            // 14 CIELab
        1             // 15 bilevel, black is 0
    };


    /* Compression to NISO mapping array.  When we don't have
     * an exact match, call it JPEG (6). */
    private final static int[] nisoCompScheme = {
        1,              // 0 uncompressed
        6,              // 1 T.4, MH
        6,              // 2 T.4, MR
        6,              // 3 T.6, MMR
        32661,          // 4 JBIG
        6               // 5 JPEG
    };    
    
    /**
     * Private constructor, to prevent instantiation
     */
    private Spiff() {
    }


    /** Converts S value to NISO color space.  Return -1 if there
     *  is no matching color space in NISO, or the S value is out
     *  of bounds.
     */
    public static int colorSpaceToNiso (int s) 
    {
        if (s < 0 || s > nisoColor.length) {
            return -1;
        }
        else {
            return nisoColor[s];
        }
    }


    /** Converts C value to NISO compression scheme.  Return -1 if there
     *  is no matching color space in NISO, or the S value is out
     *  of bounds.
     */
    public static int compressionTypeToNiso (int s) 
    {
        if (s < 0 || s > nisoCompScheme.length) {
            return -1;
        }
        else {
            return nisoCompScheme[s];
        }
    }
}
