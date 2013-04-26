/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.io.*;
import java.util.*;

/**
 *  Abstract class for PDF profile checkers.
 */
public abstract class PdfProfile
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /** The module invoking this profile. */
    protected PdfModule _module;
    
    /** A brief human-readable description of the profile. */
    protected String _profileText;
    
    /** The Parser being used on the file. */
    protected Parser _parser;
    
    /** The file being analyzed. */
    protected RandomAccessFile _raf;
    
    /** Set to <code>true</code> if this file has previously
     *  been validated by an invocation of this PdfProfile. */
    private boolean _alreadyOK;

    /** 
     *   Creates a PdfProfile.
     *   Subclass constructors should call the super constructor,
     *   then assign a value to _profileText.
     *
     *   @param module   The PDFModule we're working under
     *
     */
    public PdfProfile (PdfModule module)
    {
        _module = module;
    }

    /**
     *  Returns the value of the alreadyOK flag.  
     *  This flag when one profile depends on another, to save redundant
     *  checking.
     *  The alreadyOK flag is set whenever satisfiesProfile
     *  returns <code>true</code>.
     */
     public boolean isAlreadyOK ()
     {
        return _alreadyOK;
     }


    /** 
     * Returns <code>true</code> if the document satisfies the profile.
     * This calls <code>satisfiesThisProfile()</code>, which does the actual work.
     *
     *   @param raf    The RandomAccessFile being parsed
     *   @param parser The Parser being used on the file
     */
    public final boolean satisfiesProfile 
                (RandomAccessFile raf, Parser parser)
    {
        _raf = raf;
        _parser = parser;
        _alreadyOK = false;
        boolean sp = satisfiesThisProfile ();
        if (sp) {
            _alreadyOK = true;
        }
        return sp;
    }

    /**
     * Returns <code>true</code> if the document satisfies the
     * profile.  Subclasses should override <code>satisfiesThisProfile()</code>,
     * not <code>satisfiesProfile()</code>, as
     * <code>satisfiesProfile()</code> does some
     * additional bookkeeping for all subclases.
     */
    public abstract boolean satisfiesThisProfile ();



    /**
     *  Returns the text which describes this profile.
     */
    public String getText () 
    {
        return _profileText;
    }

    /** Returns <code>true</code> if a Filter object contains a filter name which
     *  matches any of the Strings in the second argument.  
     *  Will return <code>false</code< if a PdfException is thrown due 
     *  to an unexpected data type.
     * 
     *  (Note 24-Feb-04:  This was returning false if any filter matched,
     *   but that's contrary to both the sense conveyed by the name and
     *   the way it's being called.  Was there a reason it was that way?)
     *
     *  @param  filter  A PdfObject which may be either a PdfSimpleObject
     *                  encapsulating a Name, or a PdfArray of such objects.
     *                  If a null value is passed, it doesn't match any filter,
     *                  so <code>false</code> is returned.
     *  @param  names   An array of Strings naming the filters which should
     *                  precipitate a true result
     */
   protected boolean hasFilters (PdfObject filter, String[] names)
   {
        String filterName;
        try {
            if (filter == null) {
                return false;
            }
            if (filter instanceof PdfSimpleObject) {
                // Name of just one filter
                filterName = ((PdfSimpleObject) filter).getStringValue ();
                for (int j = 0; j < names.length; j++) {
                    if (names[j].equals (filterName)) {
                        return true;
                    }
                }
            }
            else {
                // If it's not a name, it must be an array
                Vector filterVec = ((PdfArray) filter).getContent ();
                for (int i = 0; i < filterVec.size (); i++) {
                    PdfSimpleObject filt = 
                        (PdfSimpleObject) filterVec.elementAt (i);
                    filterName = filt.getStringValue ();
                    for (int j = 0; j < names.length; j++) {
                        if (names[j].equals (filterName)) {
                            return true;
                        }
                    }
                }
            }
        }
        catch (Exception e) {
            return false;   
        }
        return false;   // none of the filters were found

   }

    /**
     *  This checks the "XObjects" dictionary, which is a dictionary whose
     *  entries have values that are XObjects.  Override xObjectOK to
     *  implement profile-specific behavior.
     */
    protected boolean xObjectsOK (PdfDictionary xos) 
    {
        if (xos == null) {
            return true;   // nothing to fail
        }
        try {
            Iterator iter = xos.iterator ();
            while (iter.hasNext ()) {
                PdfObject obj = _module.resolveIndirectObject
            ((PdfObject) iter.next ());
        if (obj instanceof PdfStream) {
            obj = ((PdfStream) obj).getDict ();
        }
                if (obj instanceof PdfDictionary) {
                    PdfDictionary xobj = (PdfDictionary) obj;
                    if (!xObjectOK (xobj)) {
                        return false;
                    }
                }
            }
        }
        catch (Exception e) {
            return false;
        }
        return true;
    }

    /**
     *  Checks a single XObject for xObjectsOK.  Always returns <code>true</code>.
     *  Override to implement tests.
     */
    protected boolean xObjectOK (PdfDictionary xo) 
    {
        return true;
    }
}
