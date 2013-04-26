/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates information about an identifier
 *  for a specification document.
 */
public class Identifier
{
    private IdentifierType _type;
    private String _value;
    private String _note;

	/**
	 *  Create an Identifier.
	 *  @param  value  The text displayed for this Identifier.
	 *  @param  type   The type of identification.
	 */
    public Identifier (String value, IdentifierType type)
    {
	_value = value;
	_type  = type;
    }

	/**
	 *  Create an Identifier.
	 *  @param  value  The text displayed for this Identifier.
	 *  @param  type   The type of identification.
	 *  @param  note   A note giving supplementary information.
	 */
    public Identifier (String value, IdentifierType type, String note)
    {
	this (value, type);
	_note = note;
    }

	/**
	 *  Return the identifier type.
	 */
    public IdentifierType getType ()
    {
	return _type;
    }

	/**
	 *  Return the displayable string.
	 */
    public String getValue ()
    {
	return _value;
    }

	/**
	 *  Return the note, which will be null if none was specified.
	 */
    public String getNote()
    {
	return _note;
    }
}
