/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;

/**
 *  A representation of a PDF stream object.
 *  A PdfStream consists of a dictionary and a stream token.
 *  By default the content of the stream isn't loaded, but
 *  it can be loaded when necessary.
 */
public class PdfStream extends PdfObject
{

    private Stream _stream;
    private PdfDictionary _dict;
    private Filter[] _filters;
    private boolean pdfaCompliant;
    
    /** 
     *  Creates a PdfStream
     *
     *  @param dict       A dictionary describing the stream
     *  @param stream     A Stream token
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     */
    public PdfStream (PdfDictionary dict, Stream stream, 
            int objNumber, int genNumber)
            throws PdfException
    {
        super (objNumber, genNumber);
        _stream = stream;
        _dict = dict;
        pdfaCompliant = true;             // assume compliance to start with
        extractFilters ();
    }


    /** 
     *  Creates a PdfStream.
     *
     *  @param dict       A dictionary describing the stream
     *  @param stream     A Stream token
     */
    public PdfStream (PdfDictionary dict, Stream stream)
            throws PdfException
    {
        super ();
        _stream = stream;
        _dict = dict;
        pdfaCompliant = true;             // assume compliance to start with
        extractFilters ();
    }
    

    /**
     *  Returns the stream's dictionary
     */
    public PdfDictionary getDict ()
    {
        return _dict;
    }


    /**
     *  Returns the stream's Stream portion
     */
    public Stream getStream ()
    {
        return _stream;
    }


    /**
     *  If the stream is external, returns the file specification
     *  for it, otherwise returns null.
     */
    public String getFileSpecification () 
    {
        PdfObject spec = _dict.get ("F");
        if (spec == null) {
            return null;
        }
        try {
            pdfaCompliant = false;          // not allowed with PDF/A
            FileSpecification fs = new FileSpecification (spec);
            return fs.getSpecString ();
        }
        catch (PdfException e) {
            return null;
        }
    }
    
    /** Returns true if no PDF/A compliance problems have been found, false if
     *  problems have been found */
    public boolean isPdfaCompliant () {
        return pdfaCompliant;
    }
    
    
    /**
     *  Returns an array (possibly empty but not null) of the filters for
     *  this Stream.  The elements of the array are Filter
     *  objects.
     */
    public Filter[] getFilters () throws PdfException
    {
        return _filters;
    }
    

    /**
     *  Return the name of the filter, if the DecodeParams dictionary
     *  is present and has a "Name" entry.
     */
    public String getFilterName ()
    {
        PdfObject decparms = _dict.get ("DecodeParams");
        if (decparms instanceof PdfDictionary) {
            PdfObject name = ((PdfDictionary) decparms).get ("Name");
            if (name instanceof PdfSimpleObject) {
                return ((PdfSimpleObject)name).getStringValue();
            }
        }
        return null;
    }



    /* Constructs the _filters array. */
    private void extractFilters () throws PdfException
    {
        boolean ff = false;
        _filters = new Filter[] {};  // default value
        PdfObject filter = _dict.get ("Filter");
        if (filter == null) {
            filter = _dict.get ("FFilter");
            if (filter == null) {
                return;
            }
            ff = true;
            pdfaCompliant = false;
        }
        PdfObject parms;
        if (ff) {
            parms = _dict.get ("FDecodeParms");
            if (parms != null) {
                pdfaCompliant = false;
            }
        }
        else {
            parms = _dict.get ("DecodeParms");
        }
        
        /* There may be a single filter, which will be a string,
         * in which case the parms will be a single dictionary.
         * Or there may be an array, in which case the params will
         * be an array of dictionaries.  The parms are optional, so
         * they may also be null.
         */
        try {
            if (filter instanceof PdfArray) {
                Vector vec = ((PdfArray) filter).getContent();
                int size = vec.size ();
                Filter[] val = new Filter[size];
                Vector parmVec = null;
                if (parms != null) {
                    parmVec = ((PdfArray) parms).getContent ();
                }
                for (int i = 0; i < size; i++) {
                    PdfSimpleObject f = (PdfSimpleObject) vec.get(i);
                    val[i] = new Filter (f.getStringValue());
                    if (parmVec != null) {
                        PdfObject parm = (PdfObject) parmVec.get(i);
                        // Parameter may be the null object.
                        if (parm instanceof PdfSimpleObject) {
                            PdfSimpleObject sParm = (PdfSimpleObject) parm;
                            if ("null".equals (sParm.getStringValue ())) {
                                continue;
                            }
                        }
                        val[i].setDecodeParms((PdfDictionary) parmVec.get(i));
                    }
                }
                _filters = val;
            }
            else {
                /* Only other allowed value is a string */
                Filter[] val = new Filter[1];
                val[0] = new Filter 
                    (((PdfSimpleObject) filter).getStringValue());
                if (parms instanceof PdfDictionary) {
                    val[0].setDecodeParms((PdfDictionary) parms);
                }
                _filters = val;
            }
        }
        catch (Exception e) {
            throw new PdfMalformedException ("Malformed filter");
        }
    }


    protected List makeFilterList () throws PdfException
    {
        Filter[] filters = getFilters ();
        if (filters.length == 0) {
            return null;
        }
        List lst = new ArrayList (filters.length);
        for (int i = 0; i < filters.length; i++) {
            lst.add (filters[i].getFilterName());
        }
        return lst;
    }


    /**
     *  Returns <code>true</code> if this is an image stream.
     */
    public boolean isImage ()
    {
        // An image dictionary may not have a type, but must have a subtype
        // of Image.
        PdfObject subtype = _dict.get ("Subtype");
        if (subtype instanceof PdfSimpleObject) {
            String subtypeStr = ((PdfSimpleObject) subtype).getStringValue ();
            return ("Image".equals (subtypeStr));
        }
        else {
            return false;
        }
    }

}
