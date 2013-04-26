/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;

/**
 *  A representation of a PDF dictionary object.
 */
public class PdfDictionary extends PdfObject
{

    private Map _entries;

    /** 
     *  Creates a PdfDictionary object.
     *
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     */
    public PdfDictionary (int objNumber, int genNumber)
    {
        super (objNumber, genNumber);
        _entries = new HashMap ();
    }

    /** 
     *  Creates a PdfDictionary object.
     *
     */
    public PdfDictionary ()
    {
        super ();
        _entries = new HashMap ();
    }

    /**
     *  Accumulate an entry into the dictionary.
     *
     *  @param key   String value of the dictionary key
     *  @param value PdfObject encapsulation of the dictionary value
     */
    public void add (String key, PdfObject value) 
    {
        _entries.put (key, value);
    }

    /** Get the PDFObject whose key has the specified string
     *  value.  Returns null if there is no such key.
     *
     *  @param  key	The string value of the key to look up.
     */
    public PdfObject get (String key)
    {
        return (PdfObject) _entries.get (key);
    }
    
    /** Return true if it's within the PDF/A implementation limit. */
    public boolean isPdfACompliant () 
    {
        return _entries.size() <= 4095;
    }

    /**
     *  Returns an iterator which will successively return
     *  all the values in the dictionary.
     */
    public Iterator iterator ()
    {
        return _entries.values ().iterator ();
    }
}
