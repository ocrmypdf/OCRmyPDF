/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/** 
 *  An enumeration class for use with the Tokenizer. Only
 *  the static instances which are declared within the class
 *  should ever be created.
 */
public class State
{
    /* ****************************************************************
     * PUBLIC CLASS FIELDS.
     ******************************************************************/

    public static final State COMMENT = new State ("COMMENT");
    public static final State E = new State ("E");
    public static final State EN = new State ("EN");
    public static final State END = new State ("END");
    public static final State ENDS = new State ("ENDS");
    public static final State ENDST = new State ("ENDST");
    public static final State ENDSTR = new State ("ENDSTR");
    public static final State ENDSTRE = new State ("ENDSTRE");
    public static final State ENDSTREA = new State ("ENDSTREA");
    public static final State ENDSTREAM = new State ("ENDSTREAM");
    public static final State FRACTIONAL = new State ("FRACTIONAL");
    public static final State GREATER_THAN = new State ("GREATER_THAN");
    public static final State HEXADECIMAL = new State ("HEXADECIMAL");
    public static final State HEX_FE_1 =  new State ("HEX_FE_1");
    public static final State HEX_FE_2 =  new State ("HEX_FE_2");
    public static final State HEX_PDF_1 = new State ("HEX_PDF_1");
    public static final State HEX_PDF_2 = new State ("HEX_PDF_2");
    public static final State HEX_UTF16_1 = new State ("HEX_UTF16_1");
    public static final State HEX_UTF16_2 = new State ("HEX_UTF16_2");
    public static final State HEX_UTF16_3 = new State ("HEX_UTF16_3");
    public static final State HEX_UTF16_4 = new State ("HEX_UTF16_4");
    public static final State HEX_RAW = new State ("HEX_RAW");
    public static final State KEYWORD = new State ("KEYWORD");
    public static final State LESS_THAN = new State ("LESS_THAN");
    public static final State LITERAL = new State ("LITERAL");
    public static final State LITERAL_FE = new State ("LITERAL_FE");
    public static final State LITERAL_PDF = new State ("LITERAL_PDF");
    public static final State LITERAL_UTF16_1 = new State ("LITERAL_UTF16_1");
    public static final State LITERAL_UTF16_2 = new State ("LITERAL_UTF16_2");
    public static final State NAME = new State ("NAME");
    public static final State NUMERIC = new State ("NUMERIC");
    public static final State STREAM = new State ("STREAM");
    public static final State WHITESPACE = new State ("WHITESPACE");

    /* ****************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    private String _name;

    /* ****************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Constructor.  It is private so that no other classes
     *  can create instances of State.
     */
    private State (String name)
    {
	_name  = name;
    }

    /* ****************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Equality test.
     *  Two State objects are considered equal only if they
     *  are the same object.
     */
    public boolean equals (State state)
    {
	return this == state;
    }

    /**
     *  Convert to String representation.
     *  A State object's String representation is its name.
     */
    public String toString ()
    {
	return _name;
    }
}
