/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  A class for holding arrays of informative strings that will go into 
 *  properties of a PDF object. 
 */
public class PdfStrings 
{

    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private PdfStrings ()
    {
    }


    /** Encryption algorithm strings. */
    public final static String[] ALGORITHM = 
    { "Undocumented", 
        "40 bit key", 
        "Key greater than 40", 
        "Unpublished" };

    /** Flags for FontDescriptor.  In PDF notation, bit 1
     * (not 0) is the low-order bit.
     */
    public final static String[] FONTDESCFLAGS =
    {
        "FixedPitch",    // 1
        "Serif",         // 2
        "Symbolic",      // 3
        "Script",        // 4
        "",              // 5
        "Nonsymbolic",   // 6
        "Italic",        // 7
        "",              // 8
        "",              // 9
        "",              // 10
        "",              // 11
        "",              // 12
        "",              // 13
        "",              // 14
        "",              // 15
        "",              // 16
        "AllCap",        // 17
        "SmallCap",      // 18
        "ForceBold"};      // 19

    /** Flags for user access permissions when revision 3 is specified. */
    public final static String[] USERPERMFLAGS3 =
    {
        "",             // 1, reserved
        "",             // 2, reserved
        "Print",        // 3
        "Modify",       // 4
        "Extract",      // 5
        "Add/modify annotations/forms",  // 6
        "",             // 7
        "",             // 8
        "Fill interactive form fields",  // 9
        "Extract for accessibility",     // 10
        "Assemble",     // 11
        "Print high quality"             // 12
    };

    /** Flags for user access permissions when revision 2 is specified. */
    public final static String[] USERPERMFLAGS2 =
    {
        "",             // 1, reserved
        "",             // 2, reserved
        "Print",        // 3
        "Modify",       // 4
        "Extract",      // 5
        "Add/modify annotations/forms",  // 6
        "",             // 7
        "",             // 8
        "",             // 9
        "",             // 10
        "",             // 11
        ""              // 12
    };

    /** Flags for annotations */
    public final static String[] ANNOTATIONFLAGS =
    {
        "Invisible",       // 1
        "Hidden",          // 2
        "Print",           // 3
        "NoZoom",          // 4
        "NoRotate",        // 5
        "NoView",          // 6
        "ReadOnly"        // 7
    };

}
