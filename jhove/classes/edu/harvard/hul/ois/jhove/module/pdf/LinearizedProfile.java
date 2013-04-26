
package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.util.*;

/**
 *  PDF profile checker for Linearized documents.
 */
public final class LinearizedProfile extends PdfProfile
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** 
     *   Creates a PdfProfile object for subsequent testing.
     *
     */
    public LinearizedProfile (PdfModule module) 
    {
        super (module);
        _profileText = "Linearized PDF";
    }

    /** 
     * Returns <code>true</code> if the document satisfies the profile.
     *
     */
    public boolean satisfiesThisProfile ()
    {
        long fileLength;
        try {
            fileLength = _raf.length ();
            // First we must find the first object from the beginning
            // of the file.  The documentation contradicts the examples
            // on whether this is an indirect object or not. Based
            // on the actual files I've seen so far, I think it isn't.
            PdfObject firstObj = findFirstObject ();
            if (!(firstObj instanceof PdfDictionary)) {
                return false;
            }
            // Initial checks: that the first object is a linearization
            // dictionary, and that it has a length element which matches
            // the length of the file.
            // All entries in a linearization dictionary must be direct.
            PdfDictionary lindict = (PdfDictionary) firstObj;
            if (lindict.get ("Linearized")!= null) {
                PdfObject lengthObj = lindict.get ("L");
                if (lengthObj instanceof PdfSimpleObject) {
                    // The value of L must be the file length
                    Token lengthTok = 
                        ((PdfSimpleObject) lengthObj).getToken ();
                    if (lengthTok instanceof Numeric) {
                        long length = ((Numeric) lengthTok).getLongValue ();
                        if (length != fileLength) {
                            return false;
                        }
                    }
                    else {
                        return false;
                    }
                }
                else {
                    return false;
                }
            }
            else {
                return false;
            }

            // Next -- check the integrity of the hint tables.
            // These are described in F.2.5 in the PDF 1.4 manual.
            // The linearization dictionary must have an 'H' entry
            // whose values is an array of 2 or 4 integers.
            PdfArray hintArray = (PdfArray) lindict.get ("H");
            if (hintArray != null) {
                Vector hintVec = hintArray.getContent ();
                int vecSize = hintVec.size ();
                if (vecSize != 2 && vecSize != 4) {
                    return false;
                }
                // element 0 (and 2, if present) is the offset
                // of a stream object. Make sure it really is.
                // Also check elements 1 and 3, which are lengths,
                // for not overflowing the file.
                for (int i = 0; i < vecSize; i += 2) {
                    PdfSimpleObject hobj = 
                        (PdfSimpleObject) _module.resolveIndirectObject
                                ((PdfObject) hintVec.elementAt (i));
                    Numeric hnum = (Numeric) hobj.getToken ();
                    long hoffset = hnum.getLongValue ();
                    hobj = (PdfSimpleObject) hintVec.elementAt (i + 1);
                    hnum = (Numeric) hobj.getToken ();
                    long hlen = hnum.getLongValue ();
                    if (hoffset + hlen > fileLength) {
                        return false;  // hint dict runs past EOF
                    }
                    _parser.seek (hoffset);
                    // The documentation appears to lie here. What
                    // we find isn't the stream, but an object
                    // definition for the stream (of the form
                    // m n obj). Allow for both possibilities.
                    PdfObject hintStream = _parser.readObject ();
                    if (hintStream instanceof PdfSimpleObject) {
                        _parser.readObject ();  // discard version no.
                        _parser.readObject ();  // discard obj keyword
                        hintStream = _parser.readObject (); // the real thing
                    }
                    // Parser will see a dictionary, not the stream
                    if (!(hintStream instanceof PdfDictionary)) {
                        return false;
                    }
                    if (!validateHintStream ((PdfDictionary) hintStream)) {
                        return false;
                    }
                }
            }
            else {
                return false;
            }

            // Check for valid first object number
            PdfSimpleObject firstObjNum = (PdfSimpleObject) lindict.get ("O");
            if (! (firstObjNum.getToken () instanceof Numeric)) {
                return false;
            }

            // Check for valid offset to end of first page
            PdfSimpleObject endpageObj =
                (PdfSimpleObject) lindict.get ("E");
            Numeric endpageTok = (Numeric) endpageObj.getToken ();
            long endpage = endpageTok.getLongValue ();
            if (endpage > fileLength) {
                return false;
            }

            // Check for valid number of pages entry
            PdfSimpleObject numpagesObj = 
                (PdfSimpleObject) lindict.get ("N");
            if (!(numpagesObj.getToken () instanceof Numeric)) {
                return false;
            }

            // Check offset to main cross-reference table
            PdfSimpleObject xrefObj =
                (PdfSimpleObject) lindict.get ("T");
            Numeric xrefTok = (Numeric) xrefObj.getToken ();
            long xrefOffset = xrefTok.getLongValue ();
            if (!verifyXRef (xrefOffset)) {
                return false;
            }
        }
        catch (Exception e) {
            // An exception thrown anywhere means some assumption
            // has been violated, so it's not linearized.
            return false;
        }
        return true;    // passed all tests
    }

    /* Find the first object from the beginning of the file.
       This is similar to, and perhaps a bit easier than, finding
       the last dictionary.  For the moment we don't worry about
       what the object is. */
    private PdfObject findFirstObject ()
    {
       try {
            _parser.seek (8);
            // To get in sync, read until we see the keyword
            // "obj".
            for (;;) {
                Token tok = _parser.getNext ();
                if (tok instanceof Keyword) {
                    if ("obj".equals(((Keyword) tok).getValue ())) {
                        PdfObject val = _parser.readObject ();
                        // Object must be completely contained in
                        // the first 1024 bytes.
                        if (_parser.getOffset () <= 1024) {
                            return val;
                        }
                        else {
                            return null;
                        }
                    }
                }
                if (_parser.getOffset () > 1024) {
                    return null;
                }
            }

        }
        catch (Exception e) {
            return null;
        }
    }


    /* Read a cross-reference table to make sure it looks OK.
       What we're pointing at is the first _entry_ of the
       table, not the start of the subsection.
       This means we don't know the object count, which makes
       it very tough to figure out whether we're hit the
       end or we really have an invalid table.
       Settle for reading one object to see if it looks good. */
    private boolean verifyXRef (long xrefOffset)
    {
        try {
            _parser.seek (xrefOffset);
            _parser.getNext (Numeric.class, "");  // Object number
            _parser.getNext (Numeric.class, "");  // Generation number
            _parser.getNext (Keyword.class, "");  // n or f keyword
            // If that didn't throw an exception, assume we're ok
            return true;
        }
        catch (Exception e) {
            return false;
        }
    }

    /* Check that a hint stream dictionary has some semblance 
       of validility. */
    private boolean validateHintStream (PdfDictionary hDict)
    {
        try {
            // An offset to the shared object hint table
            // is the one thing that's required.
            PdfSimpleObject obj = (PdfSimpleObject)
                hDict.get ("S");
            if (obj == null) {
                return false;
            }
            int offset = obj.getIntValue ();
            if (offset < 0) {
                return false;
            }

            // Other objects aren't required, but must be
            // non-negative integers if they're there.
            obj = (PdfSimpleObject) hDict.get ("T");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("O");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("A");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("E");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("V");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("I");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("L");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            obj = (PdfSimpleObject) hDict.get ("C");
            if (obj != null) {
                offset = obj.getIntValue ();
                if (offset < 0) {
                    return false;
                }
            }
            return true;  // passed all tests
        }
        catch (Exception e) {
            return false;
        }
    }
}
