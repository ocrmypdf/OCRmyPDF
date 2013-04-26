/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  Abstract class to encapsulate lexical tokens from a PDF
 *  file.  Tokens include numbers, strings, names, delimiters (the
 *  open and close markers for dictionaries and arrays), and streams.
 *  There are a variety of subclasses for specific kinds of tokens.
 */
public abstract class Token
{

    /** Superclass constructor */
    public Token ()
    {
    }
    
    /**
     *  Returns <code>true</code> if the token is one which the Parser
     *  treats as a unitary object.  Everything but arrays and dictionaries
     *  is considered a "simple" token for our purposes. 
     */
    public boolean isSimpleToken ()
    {
        return (! (this instanceof ArrayStart) &&
                ! (this instanceof ArrayEnd) &&
                ! (this instanceof DictionaryStart) &&
                ! (this instanceof DictionaryEnd));
    }
    
    /** Returns <code>true</code> if this token is within PDF/A implementation
     *  limits. Always returns true unless overridden. */
    public boolean isPdfACompliant () 
    {
        return true;
    }
}
