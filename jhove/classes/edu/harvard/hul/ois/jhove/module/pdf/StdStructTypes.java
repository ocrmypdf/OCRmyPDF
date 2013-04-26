/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;


/**
 *  This class holds the constants for standard structure type names,
 *  and a static method for determining if a string belongs
 *  to those names.
 */
public class StdStructTypes
{
    /**
     *  Array of valid structure type names
     */
    public final static String typeNames [] = {
	"Document", "Part", "Art", "Sect",
	"Div", "BlockQuote", "Caption", "TOC",
	"TOCI", "Index", "NonStruct", "Private",
	"P", "H", "H1", "H2", "H3", "H4", "H5", "H6",
	"L", "LI", "Lbl", "LBody",
	"Table", "TR", "TH", "TD",
	"Span", "Quote", "Note", "Reference",
	"BibEntry", "Code", "Link",
	"Figure", "Formula", "Form"
    };

    /**
     *  The subset of typeNames which denotes a block-level
     *  element 
     */
    public final static String blockLevelNames [] = {
	"P", "H", "H1", "H2", "H3", "H4", "H5", "H6",
	"L", "LI", "Lbl", "LBody", "Table"
    };


    /* Private constructor, so no instances of this object
       can be created */
    private StdStructTypes () 
    {
    }

    /**
     *  Returns true if s is equal (by an equals() test)
     *  to some string in typeNames.
     */
    public static boolean includes (String s) 
    {
	for (int i = 0; i < typeNames.length; i++) {
	    if (typeNames[i].equals (s)) {
		return true;
	    }
	}
	return false;
    }

    public static boolean isBlockLevel (String s) 
    {
	for (int i = 0; i < blockLevelNames.length; i++) {
	    if (blockLevelNames[i].equals (s)) {
		return true;
	    }
	}
	return false;
    }
}

