/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates information about format signatures,
 *   both internal and external.
 *   The value of a Signature may be either a String or a byte array
 *   (stored as an int array to avoid signed byte problems).
 */
public abstract class Signature
{
    private int[] _value;
    private String _stringValue;
    private SignatureType _type;
    private SignatureUseType _use;
    private String _note;

    /**
     *  A Signature cannot be created directly; this constructor
     *  can be called as the superclass constructor from a subclass.
     *  This constructor uses a String value.
     */
    protected Signature (String value, SignatureType type,
             SignatureUseType use)
    {
    this (new int[value.length ()], type, use);
    int len = value.length ();
    _stringValue = value;
    for (int i = 0; i < len; i++) {
        _value[i] = value.charAt(i);
    }
    }

    /**
     *  A Signature cannot be created directly; this constructor
     *  can be called as the superclass constructor from a subclass.
     *  This constructor uses a byte array (stored as an int array) value.
     */
    protected Signature (int[] value, SignatureType type,
             SignatureUseType use)
    {
    _value = value;
    _type  = type;
    _use   = use;
    _stringValue = null;
    }

    /**
     *  A Signature cannot be created directly; this constructor
     *  can be called as the superclass constructor from a subclass.
     *  This constructor uses a String value and allows specification
     *  of a note.
     */
    protected Signature (String value, SignatureType type,
             SignatureUseType use,
             String note)
    {
    this (new int[value.length ()], type, use, note);
    int len = value.length ();
    for (int i = 0; i < len; i++) {
        _value[i] = value.charAt(i);
    }
    _stringValue = value;
    }

    /**
     *  A Signature cannot be created directly; this constructor
     *  can be called as the superclass constructor from a subclass.
     *  This constructor uses a byte array (stored as an int array) value
     *  and allows specification of a note.
     */
    protected Signature (int[] value, SignatureType type,
             SignatureUseType use,
             String note)
    {
    this (value, type, use);
    _note = note;
    }

    /**
     *  Returns the type of this Signature
     */
    public SignatureType getType ()
    {
    return _type;
    }

    /**
     *  Returns the use requirement for this Signature
     */
    public SignatureUseType getUse ()
    {
    return _use;
    }

    /**
     *  Returns the byte array value for this Signature.
     *  If this Signature was constructed from a String, it
     *  returns the characters of the String as the bytes of
     *  the array.
     */
    public int[] getValue ()
    {
    return _value;
    }

    /**
     *  Returns the note specified for this Signature, or null
     *  if no note was specified.
     */
    public String getNote ()
    {
    return _note;
    }

    /**
     *  Returns true if this Signature's value was provided as a
     *  String, false if as an array.
     */
    public boolean isStringValue ()
    {
    return (_stringValue != null);
    }

    /**
     *  Returns the string value of this Signature.  Returns null
     *  if this Signature was constructed with an array.
     */
    public String getValueString ()
    {
    return _stringValue;
    }

    /**
     *  Returns the value of this Signature as a hexadecimal string.
     *  The length of the string is twice the length of the array
     *  or string from which this Signature was created, and all
     *  alphabetic characters are lower case.  
     */
    public String getValueHexString ()
    {
    StringBuffer valBuf = new StringBuffer ("0x");
    for (int i = 0; i < _value.length; i++) {
        /* Make each byte exactly two digits */
        int b = _value[i];
        if (b < 16) {
        valBuf.append ('0');
        }
        valBuf.append (Integer.toHexString (b));
    }
    return valBuf.toString ();
    }
}
