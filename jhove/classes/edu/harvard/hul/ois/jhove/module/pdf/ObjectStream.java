/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;
import java.util.*;

/**
 * This class implements the Object Stream, a new way of storing
 * objects starting in PDF 1.4.
 * 
 * An object stream can contain one or more objects, as described in
 * Section 3.4 of the PostScript manual.
 * 
 * JHOVE supports only FlateDecode as a filter for cross-reference 
 * streams. This is consistent with the implementation limitation
 * described in Appendix H of the PDF manual for Acrobat 6 and earlier.
 * 
 *
 * @author Gary McGath
 *
 */
public class ObjectStream {

    private PdfStream _ostrm;   // The underlying Stream object.
    private PdfDictionary _dict;
    private int _numObjects;
    private int _firstOffset;
    private Parser _parser;
    private RandomAccessFile _raf;
    
    /* Index of the object stream.  Each element is an int[2],
     * consisting of an object number and an offset.
     */
    private Map _index;

    /**
     *  Constructor.
     */
    public ObjectStream(PdfStream ostrm, RandomAccessFile raf) {
        _ostrm = ostrm;
        _raf = raf;
        _dict = ostrm.getDict ();
        _parser = new Parser (new StreamTokenizer (raf, _ostrm.getStream()));
    }
    
    /** Checks the validity of the stream dictionary, and extracts
     *  information necessary for subsequent reading.
     */
    public boolean isValid ()
    {
        try {
            /* Type must be ObjStm */
            PdfObject obj = _dict.get ("Type");
            String typeStr = null;
            if (obj instanceof PdfSimpleObject) {
                typeStr = ((PdfSimpleObject) obj).getStringValue ();
            }
            if (!("ObjStm".equals (typeStr))) {
                return false;
            }
            /* Number of objects */
            obj = _dict.get ("N");
            if (obj instanceof PdfSimpleObject) {
                _numObjects = ((PdfSimpleObject) obj).getIntValue();
            }
            else {
                return false;
            }
            /* Offset of first object */
            obj = _dict.get ("First");
            if (obj instanceof PdfSimpleObject) {
                _firstOffset = ((PdfSimpleObject) obj).getIntValue();
            }
            else {
                return false;
            }
            /* Optional refernce to object stream which this extends. */
            obj = _dict.get ("Extends");
            if (obj != null) {
                /* What do we do with this? */
            }
            return true;
        }
        catch (Exception e) {
            return false;
        }

    }


    /** Reads the index of the object stream.
     */
    public void readIndex () 
        throws PdfException, IOException
    {
        Stream strm = _ostrm.getStream ();
        strm.setFilters (_ostrm.getFilters ());
        strm.initRead (_raf);
        _index = new HashMap (_numObjects);
        for (int i = 0; i < _numObjects; i++) {
            /* If I'm reading it correctly, the numbers are
             * encoded as ASCII strings separated by white space.
             * I don't know what the restrictions, if any, are on
             * the white space.
             */
            Integer onum = new Integer (strm.readAsciiInt ());
            Integer offset = new Integer (strm.readAsciiInt ());
            _index.put (onum, offset);
        }
    }
    
    /** Extracts an object from the stream. */
    public PdfObject getObject (int objnum)
        throws PdfException
    {
        Integer onum = new Integer (objnum);
        Integer off = (Integer) _index.get (onum);
        try {
            if (off != null) {
                int offset = off.intValue ();
                _parser.seek (offset + _firstOffset);
                return _parser.readObject ();
            }
            else {
                return null;
            }
        }
        catch (IOException e) {
            throw new PdfMalformedException 
                    ("Offset out of bounds in object stream");
        }
    }

}
