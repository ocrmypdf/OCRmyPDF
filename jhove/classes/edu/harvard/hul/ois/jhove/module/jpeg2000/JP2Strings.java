/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

/**
 * String constants for JPEG 2000 module.
 * This module contains no code, and all data are static.
 * 
 * 
 * @author Gary McGath
 *
 */
public final class JP2Strings {
    
    /**
     *  Private constructor, to make sure the class isn't inadvertently
     *  initiated.
     */
    private JP2Strings ()
    {
    }


    /** Strings for method values in the color specification box. */
    public final static String methodStr[] = {
        "",
        "Enumerated Colorspace",
        "Restricted ICC Profile",
        "Any ICC Method",
        "Vendor Color Method"
    };
    
    
    /**  Strings for values of enumCS in the color specification box.
     *   Only values 16-17 are recognized by JP2.
     */
    public final static String enumCSStr[] = {
        "Bilevel (1 = black)",
        "YCbCr (1)",
        "",
        "YCbCr (2)",
        "YCbCr (3)",
        "", "", "", "",       // 5-8
        "PhotoYCC",
        "",
        "CMY",                // 11
        "CMYK",               // 12
        "YCCK",
        "CIELab",
        "",
        
        "sRGB",               // 16 (JP2)
        "Greyscale",          // 17 (JP2)
        "Bilevel (1 = white)",
        "CIEJab",
        "e-sRGB",             // 20
        "ROMM-RGB",
        "sRGB based YCbCr",
        "YPbPr (1125/60)",
        "YPbPr (1250/50)"     // 24
    };
    
    /** Strings for the MTYP field of the Component Mapping box. */
    public final static String mtypStr[] = {
        "Direct Use",
        "Palette Mapping"
    };
    
    /** Strings for the opacity type in the Opacity Box. */
    public final static String opacityTypeStr[] = {
        "Last channel is opacity channel",
        "Last channel is premultiplied opacity channel",
        "Chroma key transparency"
    };
    
    /** Strings for the number type value in the Number
     *  List box.  Types must be normalized by shifting
     *  the high byte right 24 bits before indexing.
     */
    public final static String numberListTypeStr[] = {
        "Rendered result",
        "Codestream number",
        "Compositing layer",
        "Numbered entity"
    };

    /** Strings for types in the Digital Signature Box. */
    public final static String digitalSigTypeStr[] = {
        "MD5 checksum",
        "SHA-1 checksum",
        "DSA signature",
        "RSA signature on MD5 digest",
        "RSA signature on SHA-1 digest",
        "Cryptographic Message Syntax"
    };


    /** Strings for pointer types in the Digital Signature Box. */
    public final static String digitalSigPtrTypeStr[] = {
        "Whole file",
        "Byte range"
    };
    
    /** Strings for the "region of interest present in codestream" field
     *  of the ROI box. */
    public final static String inCodestreamStr[] = {
        "Codestream does not contain static region of interest",
        "Codestream contains static region of interest"
    };
    
    /** Strings for the region type field of the ROI box. */
    public final static String roiTypeStr[] = {
        "Rectangular",
        "Elliptical"
    };
    
    /** Strings for the channel type field of the channel definition box,
     *  indexed by ctypIdx. */
    public final static String ctypStr[] = {
        "Color image data",
        "Opacity",
        "Premultiplied opacity",
        "Not specified"           // 2^16 - 1
    };
    
    /** Indexes for ctypStr. */
    public final static int ctypIdx[] = {0, 1, 2, 65535};
    
    /** Strings for the approx field of the color specification box,
     *  indexed by approxIdx.  A zero value will be reported as
     *  an Integer property of 0. */
    public final static String approxStr[] = {
        "Accurate representation",
        "Approximation with exceptional quality",
        "Approximation with reasonable quality",
        "Approximation with poor quality"
    };
    
    
    /** Indexes for approxStr. */
    public final static int approxIdx[] = {1, 2, 3, 4};
}
