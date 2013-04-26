/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;
import java.util.*;

/**
 * This class implements the Cross-Reference Stream, an alternative
 * to the Cross-Reference Table starting in PDF 1.4.
 * 
 * A cross-reference stream is identified by a startxref keyword,
 * as opposed to the xref keyword which identifies the old-style
 * cross-reference table.
 * 
 * JHOVE supports only FlateDecode as a filter for cross-reference 
 * streams. This is consistent with the implementation limitation
 * described in Appendix H of the PDF manual for Acrobat 6 and earlier.
 * 
 *
 * @author Gary McGath
 *
 */
public class CrossRefStream {
    
    private PdfStream _xstrm;   // The underlying Stream object.
    private PdfDictionary _dict;
    private int _size;
    private int[] _index;
    private int[] _fieldSizes;
    private int _freeCount;
    private Filter[] _filters;
    private int _entriesRead;
    private int _bytesPerEntry;
    private long _prevXref;    // byte offset to previous xref stream, if any

    /* Per-object variables. */
    private int _objType;
    private int _objNum;
    private int _objField1;
    private int _objField2;
    
    /**
     * Constructor.
     * 
     * @param   xstrm	PdfStream object which contains a presumed
     *          cross-reference stream.
     */
    public CrossRefStream(PdfStream xstrm) {
        _xstrm = xstrm;
        _dict = xstrm.getDict ();
        _freeCount = 0;
    }

    /**  Returns <code>true</code> if the PdfStream object meets
     *   the requirements of a cross-reference stream.  Also extracts
     *   information from the dictionary for subsequent processing.
     */
    public boolean isValid () {
        try {
            PdfObject typeobj = _dict.get ("Type");
            String typeStr = null;
            if (typeobj instanceof PdfSimpleObject) {
                typeStr = ((PdfSimpleObject) typeobj).getStringValue ();
                if (!("XRef".equals (typeStr))) {
                    return false;
                }
            }
            if (typeStr == null) {
                return false;
            }
            PdfObject sizeobj = _dict.get ("Size");
            if (sizeobj instanceof PdfSimpleObject) {
                _size = ((PdfSimpleObject) sizeobj).getIntValue();
            }
            else {
                return false;
            }
            
            // The Index entry is optional, but must have the right
            // format if it's present.
            PdfObject indexobj = _dict.get ("Index");
            if (indexobj instanceof PdfArray) {
                Vector vec = ((PdfArray) indexobj).getContent();
                // This is supposed to have a size of 2.
                _index = new int[2];
                PdfSimpleObject idx = (PdfSimpleObject) vec.get (0);
                _index[0] = idx.getIntValue ();
                idx = (PdfSimpleObject) vec.get (1);
                _index[1] = idx.getIntValue ();
            }
            else {
                // Set up default index.
                _index = new int[] { 0, _size };
            }
            
            // Get the field sizes.
            PdfObject wObj = _dict.get ("W");
            if (wObj instanceof PdfArray) {
                Vector vec = ((PdfArray) wObj).getContent ();
                int len = vec.size ();
                _fieldSizes = new int[len];
                for (int i = 0; i < len; i++) {
                    PdfSimpleObject ob = (PdfSimpleObject) vec.get (i);
                    _fieldSizes[i] = ob.getIntValue ();
                }
            }
            
            // Get the offset to the previous xref stream, if any.
            PdfObject prevObj = _dict.get ("Prev");
            if (prevObj instanceof PdfSimpleObject) {
                _prevXref = ((PdfSimpleObject) prevObj).getIntValue();
            }
            else {
                _prevXref = -1;
            }
            
            // Get the filter, for subsequent decompression.
            // We're guaranteed by the spec that this won't be a decryption
            // filter.
            _filters = _xstrm.getFilters();
            // Why isn't this being used?
            
            // passed all tests
            return true;
        }
        catch (Exception e) {
            return false;
        }
    }
    
        /** Prepares for reading the Stream. 
     *  If the filter List includes one which we don't support, throws a
     *  PdfException. */
    public void initRead (RandomAccessFile raf) 
            throws IOException, PdfException 
    {
        Stream strm = _xstrm.getStream ();
        strm.setFilters (_xstrm.getFilters ());
        strm.initRead (raf);
        _entriesRead = 0;
        
        /* Calculate the total bytes per entry.  This may have
         * some utility. */
        _bytesPerEntry = 0;
        for (int i = 0; i < _fieldSizes.length; i++) {
            _bytesPerEntry += _fieldSizes[i];
        }
    }
    


    /** Reads the next object in the stream.
     *  
     *  After calling <code>readObject</code>, it is possible to
     *  call accessors to get information about the object.
     *  For the moment, we
     *  punt on the question of how to deal with Object Streams.
     * 
     *  Free objects are skipped over while being counted.  After
     *  <code>readNextObject() returns <code>false</code>, the caller
     *  may call <code>getFreeCount()</code> to determine the
     *  number of free objects.
     * 
     *  @return  <code>true</code> if there is an object, <code>false</code>
     *           if no more objects are available.
     */
    public boolean readNextObject () throws IOException
    {
        /* Get the field type. */
        int wid;
        Stream is = _xstrm.getStream ();
        int i;
        int b;
        
        for (;;) {
            /* Loop till we find an actual object; we just count
             * type 0's, which are free entries. */
            wid  = _fieldSizes[0];
            if (_entriesRead++ >= _index[1]) {
                return false;       // Read full complement
            }
            if (wid != 0) {
                /* "Fields requiring more than one byte are stored 
                 * with the high-order byte first." */
                _objType = 0;
                for (i = 0; i < wid; i++) {
                    b = is.read ();
                    if (b < 0) {
                        return false;
                    } 
                    _objType = _objType * 256 + b;
                }
            }
            else {
                _objType = 1;   // Default if field width is 0
            }
            
            wid = _fieldSizes[1];
            _objField1 = 0;
            for (i = 0; i < wid; i++) {
                b = is.read ();
                if (b < 0) {
                    return false;
                } 
                _objField1 = _objField1 * 256 + b;
            }
            
            wid = _fieldSizes[2];
            _objField2 = 0;
            for (i = 0; i < wid; i++) {
                b = is.read ();
                if (b < 0) {
                    return false;
                } 
                _objField2 = _objField2 * 256 + b;
            }
            
            if (_objType != 0) {
                _objNum = _index[0] + _entriesRead - 1;
                return true;
            }
            else {
                ++_freeCount;
            }
        }
    }
    
    /** Returns number of the last object read by
     *  <code>readNextObject ()</code>.
     *  Do not call if <code>readNextObject ()</code>
     *  returns <code>false</code>.
     */
    public int getObjNum ()
    {
        return _objNum;
    }


    /** Returns <code>true</code> if the last object read by
     *  <code>readNextObject ()</code> is a compressed object.
     *  Do not call if <code>readNextObject ()</code>
     *  returns <code>false</code>.
     */
    public boolean isObjCompressed ()
    {
        return (_objType == 2);
    }
    
    
    /** Returns the number of free objects detected.  This may
     *  be called after <code>readNextObject</code> returns
     *  <code>false</code>, signifying that all the objects
     *  have been read and all the free objects counted.
     */
    public int getFreeCount ()
    {
        return _freeCount;
    }
    
    /** Returns the total object count. */
    public int getNumObjects ()
    {
        return _index[0] + _index[1];
    }
    
    /** Returns the offset of the last object object read.  
     *  This is meaningful only if the last object read
     *  was type 1 (uncompressed).
     */
    public int getOffset ()
    {
        return _objField1;
    }
    
    /** Returns the object number of the content stream in
     *  which this object is stored.
     *  This is nmeaningful only if the last object read
     *  was type 2 (compressed in content stream).
     */
    public int getContentStreamObjNum ()
    {
        return _objField1;
    }
    
    /** Returns the offset of the previous cross-reference stream,
     *  or -1 if none is specified. */
    public long getPrevXref ()
    {
        return _prevXref;
    }


    /** Returns the content stream index of the last object read.
     *  This is nmeaningful only if the last object read
     *  was type 2 (compressed in content stream).
     */
    public int getContentStreamIndex ()
    {
        return _objField2;
    }
}
