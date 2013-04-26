/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

/**
 *  A class for holding arrays of informative strings that will go into 
 *  properties of an AIFF object. 
 *
 * @author Gary McGath
 *
 */
public class AiffStrings {

    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private AiffStrings ()
    {
    }

    /** Strings for looping types in the Instrument Chunk */
    public final static String[] LOOP_TYPE = 
    { "No looping", 
        "Forward looping",
        "Forward/backward looping" };

}
