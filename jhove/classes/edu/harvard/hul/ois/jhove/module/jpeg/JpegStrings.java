/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

/**
 *  A class for holding arrays of informative strings that will go into 
 *  properties of a JPEG object. 
 */
public class JpegStrings {

    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private JpegStrings ()
    {
    }

    /** JPEG compression types, indexed on marker byte - 0XC0.
     *  This applies only to marker codes for the primary image; 
     *  thumbnail compression schemes are completely incompatible.  */
    public final static String[] COMPRESSION_TYPE =
       { "Huffman coding, Baseline DCT",
         "Huffman coding, Extemded sequential DCT",
         "Huffman coding, Progressive DCT",
         "Huffman coding, Lossless (sequential)",
         "",
         "Huffman coding, Differential sequential DCT",
         "Huffman coding, Differential progressive DCT",
         "Huffman coding, Differential lossless (sequential)",
         "",
         "Arithmetic coding, Extended sequential DCT",
         "Arithmetic coding, Progressive DCT", 
         "Arithmetic coding, Lossless (sequential)",
         "",
         "Arithmetic coding, Differential sequential DCT",
         "Arithmetic coding, Differential progressive DCT",
         "Arithmetic coding, Differential lossless (sequential)"         
        };
    
    /** Values for capability indicator byte for Version 0 */
    public final static String[] CAPABILITY_V0 =
    {
        "",                                         // 0
        "Baseline sequential",                      // 1
        "Extended sequential, Huffman, 8-bits",     // 2
        "Extended sequential, arithmetic, 8-bits",  // 3
        "Extended sequential, Huffman, 12-bits",    // 4
        "Extended sequential, arithmetic, 12-bits", // 5
        "Spectral selection, Huffman, 8-bits",      // 6
        "Spectral selection, arithmetic, 8-bits",   // 7
        "Full progression, Huffman, 8-bits",        // 8
        "Full progression, arithmetic, 8-bits",     // 9
        "Spectral selection, Huffman, 12-bits",     // 10
        "Spectral selection, arithmetic, 12-bits",  // 11
        "Full progression, Huffman, 12-bits",       // 12
        "Full progression, arithmetic, 12-bits",    // 13
        "Lossless, Huffman",                        // 14
        "Lossless, arithmetic",                     // 15
        "Hierarchical, sequential Huffman, 8-bits", // 16
        "Hierarchical, sequential arithmetic, 8-bits",  // 17
        "Hierarchical, sequential Huffman, 12-bits",    // 18
        "Hierarchical, sequential arithmetic, 12-bits", // 19
        "Hierarchical, Spectral Selection, " +
            "Huffman, 8-bits",                          // 20
        "Hierarchical, Spectral Selection, " +
            "arithmetic, 8-bits",                       // 21  
        "Hierarchical, Full progression, " +
            "Huffman, 8-bits",                          // 22
        "Hierarchical, Full progression, " +
            "arithmetic, 8-bits",                       // 23
        "Hierarchical, Spectral Selection, " +
            "Huffman, 12-bits",                         // 24
        "Hierarchical, Spectral Selection, " +
            "arithmetic, 12-bits",                      // 25
        "Hierarchical, Full progression, " +
            "Huffman, 12-bits",                         // 26
        "Hierarchical, Full progression, " +
            "arithmetic, 12-bits",                      // 27
        "Hierarchical, Lossless, Huffman",              // 28
        "Hierarchical, Lossless, arithmetic"            // 29
    };
        
        
    /** Values for capability indicator byte for Version 1.
     *  These are by bit position from right to left. 
     */
    public final static String[] CAPABILITY_V1 =
    {
        "10 < blocks per MCU < 20",                   // 0xxx xxx1
        "Variable quantization",                      // 0xxx xx1x
        "Hierarchical selective refinement",          // 0xxx x1xx
        "Progressive selective refinement",           // 0xxx 1xxx
        "Componenet selective refinement",            // 0xx1 xxxx
    };
    
    
    /* Values for capability indicator byte, tiling bits, 
     * for Version 1.  These match the indicated masks.
     */
    public final static String[] TILING_CAPABILITY_V1 =
    {
        "No tiling",                                // 000x xxxx
        "Simple tiling",                            // 001x xxxx
        "Pyramidal tiling",                         // 010x xxxx
        "Composite tiling"                          // 011x xxxx
    }; 
    
    /* Values for tiling type, as defined in the DTI segment.
     */
    public final static String[] TILING_TYPE =
    {
        "Simple",           // 0
        "Pyramidal",        // 1
        "Composite"         // 2
    };
    
    /* Values for precision in DQT segment. 
     */
    public final static String[] DQT_PRECISION =
    {
        "8-bit",            // 0
        "16-bit",           // 1
    };


    /* Values for precision in DAC segment. 
     */
    public final static String[] DAC_CLASS =
    {
        "DC table or iossiess table",            // 0
        "AC table",           // 1
    };
}
