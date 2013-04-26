/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates information about internal format signatures.
 *   The value of a Signature may be either a String or a byte array
 *   (stored as an int array to avoid signed byte problems).
 */
public class InternalSignature
    extends Signature
{
    private boolean _hasFixedOffset;
    private int _offset;

    /**
     *  Creates an InternalSignature given a string value, a type,
     *  and a use requirement.  An InternalSignature created with
     *  this constructor does not have a fixed byte offset.
     */
    public InternalSignature (String value, SignatureType type,
			      SignatureUseType use)
    {
	super (value, type, use);
	_hasFixedOffset = false;
    }

    /**
     *  Creates an InternalSignature given a byte array, a type,
     *  and a use requirement.  An InternalSignature created with
     *  this constructor does not have a fixed byte offset.
     */
    public InternalSignature (int[] value, SignatureType type,
			      SignatureUseType use)
    {
	super (value, type, use);
	_hasFixedOffset = false;
    }

    /**
     *  Creates an InternalSignature given a string value, a type,
     *  a use requirement, and a byte offset.  An InternalSignature 
     *  created with this constructor has a fixed byte offset.
     */
    public InternalSignature (String value, SignatureType type,
			      SignatureUseType use, int offset)
    {
	super (value, type, use);
	_offset = offset;
	_hasFixedOffset = true;
    }

    /**
     *  Creates an InternalSignature given a byte array, a type,
     *  a use requirement, and a byte offset.  An InternalSignature 
     *  created with this constructor has a fixed byte offset.
     */
    public InternalSignature (int[] value, SignatureType type,
			      SignatureUseType use, int offset)
    {
	super (value, type, use);
	_offset = offset;
	_hasFixedOffset = true;
    }

    /**
     *  Creates an InternalSignature given a string value, a type,
     *  a use requirement, and a note.  An InternalSignature created with
     *  this constructor does not have a fixed byte offset.
     */
    public InternalSignature (String value, SignatureType type,
			      SignatureUseType use, String note)
    {
	super (value, type, use, note);
	_hasFixedOffset = false;
    }

    /**
     *  Creates an InternalSignature given a byte array, a type,
     *  a use requirement, and a note.  An InternalSignature created with
     *  this constructor does not have a fixed byte offset.
     */
    public InternalSignature (int[] value, SignatureType type,
			      SignatureUseType use, String note)
    {
	super (value, type, use, note);
	_hasFixedOffset = false;
    }

    /**
     *  Creates an InternalSignature given a string value, a type,
     *  a use requirement, a byte offset, and a note.
     *  An InternalSignature created with
     *  this constructor has a fixed byte offset.
     */
    public InternalSignature (String value, SignatureType type,
			      SignatureUseType use, int offset,
			      String note)
    {
	super (value, type, use, note);
	_offset = offset;
	_hasFixedOffset = true;
    }

    /**
     *  Creates an InternalSignature given a string value, a type,
     *  a use requirement, a byte offset, and a note.
     *  An InternalSignature created with
     *  this constructor has a fixed byte offset.
     */
    public InternalSignature (int[] value, SignatureType type,
			      SignatureUseType use, int offset,
			      String note)
    {
	super (value, type, use, note);
	_offset = offset;
	_hasFixedOffset = true;
    }

    /**
     *  Returns the byte offset.  This value is meaningful only
     *  if this InternalSignature has a fixed byte offset.
     */
    public int getOffset ()
    {
	return _offset;
    }

    /**
     *  Returns <code>true</code> if this InternalSignature
     *  has a fixed byte offset.
     */
    public boolean hasFixedOffset ()
    {
	return _hasFixedOffset;
    }
}
