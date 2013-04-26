/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;
import java.util.*;

/**
 *  The Parser class implements some limited syntactic analysis 
 *  for PDF.  It isn't by any means intended to be a full
 *  parser.  Its main job is to track nesting of syntactic
 *  elements such as dictionary and array beginnings and
 *  ends.
 */
public class Parser 
{

    private Tokenizer _tokenizer;
    private int _dictDepth;     // number of dictionary starts on stack
    private int _arrayDepth;    // number of array starts on stack
    private Map _objectMap;     // the object map for the file
    private boolean _encrypted; // true if the document is encrypted

    /* PDF/A compliance flag. */
    private boolean _pdfACompliant;


    /**
     *  Constructor.  A Parser works with a Tokenizer that feeds
     *  it tokens.
     *
     *  @param  tokenizer   The Tokenizer which the parser will use
     */
    public Parser (Tokenizer tokenizer)
    {
        _tokenizer = tokenizer;
        _pdfACompliant = true;
        reset ();
    }
    
    /**
     *  Set the object map on which the parser will work.
     */
    public void setObjectMap (Map objectMap)
    {
        _objectMap = objectMap;
    }

    /**
     *  Clear the state of the parser so that it can start
     *  reading at a different place in the file.  Clears the
     *  stack and the dictionary and array depth counters.
     */
    public void reset () {
        _dictDepth = 0;
        _arrayDepth = 0;
    }


    /**
     *  Clear the state of the parser so that it can start
     *  reading at a different place in the file and ignore
     *  any nesting errors.  Sets the
     *  stack and the dictionary and array depth counters to
     *  a large number so that nesting exceptions won't be thrown.
     */
    public void resetLoose () {
        _dictDepth = 1000000;
        _arrayDepth = 1000000;
    }

    /**
     *  Gets a token.  Uses Tokenizer.getNext, and keeps track
     *  of the depth of dictionary and array nesting.
     */
    public Token getNext ()
	throws IOException, PdfException
    {
	return getNext (0L);
    }

    /**
     *  Gets a token.  Uses Tokenizer.getNext, and keeps track
     *  of the depth of dictionary and array nesting.
     * @param max Maximum allowable size of the token
     */
    public Token getNext (long max)
	throws IOException, PdfException
    {
        Token tok = _tokenizer.getNext (max);
        if (tok instanceof DictionaryStart) {
            ++_dictDepth;
        }
        else if (tok instanceof DictionaryEnd) {
            --_dictDepth;
            if (_dictDepth < 0) {
                throw new PdfMalformedException ("Improperly nested dictionary delimiters");
            }
        }
        if (tok instanceof ArrayStart) {
            ++_arrayDepth;
        }
        else if (tok instanceof ArrayEnd) {
            --_arrayDepth;
            if (_arrayDepth < 0) {
                throw new PdfMalformedException ("Improperly nested array delimiters");
            }
        }
        return tok;
    }

    /**
     *  A class-sensitive version of getNext.  The token
     *  which is obtained must be of the specified class
     *  (or a subclass thereof), or a PdfInvalidException with
     *  message errMsg will be thrown.
     */
    public Token getNext (Class clas, String errMsg)
                throws IOException, PdfException
    {
        Token tok = getNext ();
        if (!clas.isInstance (tok)) {
            throw new PdfInvalidException (errMsg);
        }
        if (!tok.isPdfACompliant())
            _pdfACompliant = false;
        return tok;
    }

    /**
     *  Returns the number of dictionary starts not yet matched by
     *  dictionary ends.
     */
    public int getDictDepth () 
    {
        return _dictDepth;
    }

    /**
     *  Tells this Parser, and its Tokenizer, whether the file
     *  is encrypted.
     */
    public void setEncrypted (boolean encrypted)
    {
        _encrypted = encrypted;
        _tokenizer.setEncrypted (encrypted);
    }

    /**
     *  Returns the number of array starts not yet matched by
     *  array ends.
     */
    public int getArrayDepth ()
    {
        return _arrayDepth;
    }
    
    /**
     *  Returns the Tokenizer's current whitespace string.
     */
    public String getWSString () {
        return _tokenizer.getWSString ();
    }

    /** 
     * Returns the language code set from the Tokenizer.
     */
    public Set getLanguageCodes ()
    {
        return _tokenizer.getLanguageCodes ();   
    }
    /**
     *   Returns false if either the parser or the tokenizer has detected
     *   non-compliance with PDF/A restrictions.  A value of <code>true</code>
     *   is no guarantee that the file is compliant.
     */
    public boolean getPDFACompliant ()
    {
        if (!_tokenizer.getPDFACompliant ()) {
            _pdfACompliant = false;
        }
        return _pdfACompliant;
    }
    
    /**
     *   Set the value of the pdfACompliant flag.  This may be used to
     *   clear previous detection of noncompliance.  If the parameter
     *   has a value of <code>true</code>, the tokenizer's pdfACompliant
     *   flag is also set to <code>true</code>.
     */
    public void setPDFACompliant (boolean pdfACompliant)
    {
        _pdfACompliant = pdfACompliant;
        if (pdfACompliant) {
            _tokenizer.setPDFACompliant (true);
        }
    }

    /**
     *  Reads an object definition, from wherever we are in the stream to 
     *  the completion of one full object after the obj keyword.
     */
    public PdfObject readObjectDef () throws IOException, PdfException
    {
        Numeric objNumTok = (Numeric) getNext 
            (Numeric.class, "Invalid object definition");
        return readObjectDef (objNumTok);
    }
    
    /** Reads an object definition, given the first numeric object, which
     *  has already been read and is passed as an argument.  This is called
     *  by the no-argument readObjectDef; the only other case in which it
     *  will be called is for a cross-reference stream, which can be distinguished
     *  from a cross-reference table only once the first token is read. 
     */
    public PdfObject readObjectDef (Numeric objNumTok) 
                    throws IOException, PdfException
    {
        String invDef = "Invalid object definition";
        reset ();
        // The start of an object must be <num> <num> obj
        //Numeric objNumTok = (Numeric) getNext (Numeric.class, invDef);
        Numeric genNumTok = (Numeric) getNext (Numeric.class, invDef);
        Keyword objKey = (Keyword) getNext (Keyword.class, invDef);
        if (!"obj".equals (objKey.getValue ())) {
            throw new PdfMalformedException (invDef);
        }
        if (_tokenizer.getWSString ().length () > 1) {
                _pdfACompliant = false;
        }
        PdfObject obj = readObject ();
        
        // Now a special-case check to read a stream object, which
        // consists of a dictionary followed by a stream token.
        if (obj instanceof PdfDictionary) {
            Stream strm = null;
            try {
                strm = (Stream) getNext (Stream.class, "");
            }
            catch (Exception e) {
                // if we get an exception, it just means it wasn't a stream
            }
            if (strm != null) {
                // Assimilate the dictionary and the stream token into the
                // object to be returned
                PdfStream strmObj = new PdfStream ((PdfDictionary) obj, strm);
                if (!strmObj.isPdfaCompliant()) {
                    _pdfACompliant = false;
                }
                obj = strmObj;
            }
        }
        
        obj.setObjNumber (objNumTok.getIntegerValue ());
        obj.setGenNumber (genNumTok.getIntegerValue ());
        return obj;
    }
    
    /**
     *  Reads an object.  By design, this reader has a number
     *  of limitations.
     *  <ul>
     *    <li>It doesn't retain the contents of streams</li>
     *    <li>It doesn't recognize a stream when it's pointing at
     *        the stream's dictionary; it will just read the
     *        dictionary</li>
     *  </ul>
     *  Functions which it uses may call it recursively to build up structures.
     *  If it encounters a token inappropriate for an object start, it
     *  throws a PdfException on which getToken() may be called to retrieve
     *  that token.  
     */
    public PdfObject readObject () throws IOException, PdfException
    {
        Token tok = getNext ();
        if (tok instanceof ArrayStart) {
            return readArray ();
        }
        else if (tok instanceof DictionaryStart) {
            return readDictionary ();
        }
        else if (tok.isSimpleToken ()) {
            return new PdfSimpleObject (tok);
        }
        else {
            throw new PdfMalformedException 
              ("Cannot parse object", getOffset(), tok);
        }
    }
    
    /**
     *   Reads an array.  When this is called, we have already read the
     *   ArrayStart token, and arrayDepth has been incremented to reflect this.
     */
    public PdfArray readArray () throws IOException, PdfException
    {
        PdfArray arr = new PdfArray ();
        for (;;) {
            PdfObject obj = null;
            try {
                obj = readObject ();
                arr.add (obj);
            }
            // We detect the end of an array by a PdfException being thrown
            // when readObject encounters the close bracket.  When we get
            // the end of the array, collapse the vector before returning the object.
            catch (PdfException e) {
                Token tok = e.getToken ();
                if (tok instanceof ArrayEnd) {
                    collapseObjectVector (arr.getContent ());
                    if (!arr.isPdfACompliant()) {
                        _pdfACompliant = false;
                    }
                    return arr;
                }
                else {
                    throw e;    // real error
                }
            }
        }
    }
    
    
    /** Reads a dictionary.  When this is called, we have already read the
     *   DictionaryStart token, and dictDepth has been incremented to reflect this.
     *   Only for use in this special case, where we're picking up
     *   a dictionary in midstream.
     */
    public PdfDictionary readDictionary () throws IOException, PdfException
    {
        PdfDictionary dict = new PdfDictionary ();
        // Create a vector as a temporary holding place for the objects
        Vector vec = new Vector ();

        for (;;) {
            PdfObject obj = null;
            try {
                obj = readObject ();
                // Comments within a dictionary need to be ignored.
                if (obj instanceof PdfSimpleObject &&
                               ((PdfSimpleObject) obj).getToken() instanceof Comment) {
                    continue;
                }
                vec.add (obj);
            }
            // We detect the end of a dictionary by a PdfException being thrown
            // when readObject encounters the close angle brackets.  When we get
            // the end of the array, collapse the vector before returning the object.
            catch (PdfException e) {
                Token tok = e.getToken ();
                if (tok instanceof DictionaryEnd) {
                    collapseObjectVector (vec);
                    String invalDict = "Malformed dictionary";
                    // The collapsed vector must contain an even number of objects
                    int vecSize = vec.size ();
                    if ((vecSize % 2) != 0) {
                        throw new PdfMalformedException (invalDict + ": Vector must contain an even number of objects, but has " + vecSize, getOffset ());
                    }
                    for (int i = 0; i < vecSize; i += 2) {
                        try {
                            Name key = (Name) ((PdfSimpleObject) 
                                    vec.elementAt (i)).getToken ();
                            PdfObject value = (PdfObject) vec.elementAt (i + 1);
                            dict.add (key.getValue (), value);
                        }
                        catch (Exception f) {
                            throw new PdfMalformedException (invalDict, getOffset ());
                        }
                    }
                    if (!dict.isPdfACompliant()) {
                        _pdfACompliant = false;    // exceeds implementation limit for PDF/A
                    }
                    return dict;
                }
                else {
                    throw e;    // real error
                }
            }
        }
    }
    
    
    /**
     *  Returns the current offset into the file.
     */
    public long getOffset ()
    {
        return _tokenizer.getOffset ();
    }

    /**
     *  Positions the file to the specified offset, and
     *  resets the state for a new token stream.
     */
    public void seek (long offset)
        throws IOException, PdfException
    {
        _tokenizer.seek (offset);
        reset ();
    }


    /**
     *  PDF has a wacky grammar which must be a legacy of
     *  PostScript's postfix syntax.  A keyword of R means that
     *  the two previous objects are really part of an indirect object
     *  reference.  This means that when a vector of objects is complete,
     *  it has to be read backwards so that indirect object references can
     *  be collapsed out.  In the case of a dictionary, this has to be done
     *  before the content can be interpreted as key-value pairs.
     */
    private void collapseObjectVector (Vector v) throws PdfException
    {
        for (int i = v.size() - 1; i >= 2; i--) {
            PdfObject obj = (PdfObject) v.elementAt (i);
            if (obj instanceof PdfSimpleObject) {
                Token tok = ((PdfSimpleObject) obj).getToken ();
                if (tok instanceof Keyword) {
                    if ("R".equals (((Keyword)tok).getValue ())) {
                        // We're in the key of 'R'.  The two previous tokens
                        // had better be Numerics.  Three objects in the Vector
                        // are replaced by one.
                        try {
                            PdfSimpleObject nobj = 
                                (PdfSimpleObject) v.elementAt (i - 2);
                            Numeric ntok = (Numeric) nobj.getToken ();
                            int objNum = ntok.getIntegerValue ();
                            nobj = (PdfSimpleObject) v.elementAt (i - 1);
                            ntok = (Numeric) nobj.getToken ();
                            int genNum = ntok.getIntegerValue ();
                            v.set (i - 2, new PdfIndirectObj 
                                (objNum, genNum, _objectMap));
                            v.removeElementAt (i);
                            v.removeElementAt (i - 1);
                            i -= 2;
                        }
                        catch (Exception e) {
                            throw new PdfMalformedException 
                                ("Malformed indirect object reference");
                        }
                    }
                }
            }
        }
    }

    /**
     * If true, do not attempt to parse non-whitespace delimited tokens, e.g.,
     * literal and hexadecimal strings.
     * @param flag Scan mode flag
     */
    public void scanMode (boolean flag)
    {
	_tokenizer.scanMode (flag);
    }
}
