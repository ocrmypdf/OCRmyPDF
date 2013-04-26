
/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/


package edu.harvard.hul.ois.jhove;


/**
 *  Class encapsulating RFC-1766 language codes.
 */
public final class RFC1766Lang 
{

    String _langCode;

    /**
     * Constructor. 
     *
     * @param   str	The ASCII string for the language code.
     */
    public RFC1766Lang (String str) 
    {
	_langCode = str;
    }

    /**
     *  Returns the language code string. 
     */
    public String getLangCode () 
    {
	return _langCode;
    }

    /**
     *  Returns <code>true</code> if the language code
     *  string is syntactically compliant.
     *  The primary tag must be either a two-letter code,
     *  the letter i, or the letter x (case insensitive);
     *  no checking is done against registry lists.
     */
    public boolean isSyntaxCorrect ()
    {
	int i;
	if (_langCode == null) {
	    return false;
	}
	char[] chrs = _langCode.toLowerCase().toCharArray();
	char firstChar = '\0';

	int ntags = 0;
	int taglength = 0;
	for (i = 0; i < chrs.length; i++) {
	    char ch = chrs[i];
	    if (i == 0) {
		firstChar = ch;
	    }
	    if (!Character.isLetter (ch) && ch != '-') {
		return false;
	    }
	    if (ch == '-') {
		taglength = 0;

		// If this is the primary tag, do some checks
		if (ntags++ == 0) {
		    if (taglength == 1) {
			if (firstChar != 'i' && firstChar != 'x') {
			    return false;
			}
			else if (taglength != 2) {
			    return false;
			}
		    }
		}
	    }
	    else {
		taglength++;
		if (taglength > 8) {
		    return false;
		}
	    }
	}
	// A dangling hyphen at the end isn't allowed.
	if (taglength == 0) {
	    return false;
	}

	return true;
    }
}
