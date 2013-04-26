/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.gif;

/**
 *  A class for holding arrays of informative strings that will go into 
 *  properties of a GIF object. 
 */
public class GifStrings {

    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private GifStrings ()
    {
    }

    /** Strings for presence or absence of global color table */
    public final static String[] GLOBAL_COLOR_TABLE_FLAG = 
    { "No global color table; background color index meaningless", 
        "Global color table follows; background color index meaningful" };

    /** Strings for ordering or non-ordering of color table */
    public final static String[] COLOR_TABLE_SORT_FLAG = 
    { "Not ordered", 
        "Ordered by decreasing importance" };

    /** GIF Capabilities Enquiry string: way in which the graphic is to
     *  be treated after being displayed */
    public final static String[] GCE_DISPOSAL_METHOD =
    { "No disposal specified",
         "Do not dispose",
         "Restore to background color",
         "Restore to previous" };

    /** GIF Capabilities Enquiry string: user input 
     * expected or not */
    public final static String[] GCE_USER_INPUT_FLAG =
    { "User input not expected",
         "User input expected" };
    
    /** GIF Capabilities Enquiry string: transparency
     *  index given or not */
    public final static String[] GCE_TRANSPARENCY_FLAG =
    {  "Transparent index is not given",        "Transparent index given" };

    /** Local color table present in image or not */
    public final static String[] LOCAL_COLOR_TABLE_FLAG = 
    {   "No local color table; use global table if available",
        "Local color table follows" };
        
    /** Image is interlaced or not */
    public final static String[] INTERLACE_FLAG =
    {  "Image is not interlaced",
       "Image is interlaced" }; 

}
