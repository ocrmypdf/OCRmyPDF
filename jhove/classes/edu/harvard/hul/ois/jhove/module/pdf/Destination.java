/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;
import java.util.*;

/** 
 *  Class encapsulating PDF destination objects, which refer
 *  to a page in the document.
 * 
 *  We need to make two different kinds of distinctions: between
 *  destinations that make an indirect and a direct reference to
 *  a page; and between destinations that have been reached by
 *  a direct and an indirect reference.  The PDF spec allows
 *  only one level of indirection, so each of these forms has
 *  options not available to the other.  
 *
 *  We call a destination which has been reached directly an
 *  unnamed destination, and one which has been reached indirectly
 *  a named destination.  We call a destination which has an
 *  indirect target an indirect destination, and one which has
 *  a page object as a target a direct destination.  Applying
 *  the PDF documentation, we find that a destination can never
 *  be both named and indirect.  In other words, there are really
 *  two cases, involving three kinds of destinations:
 *
 *  <UL>
 *  <LI> An unnamed, direct destination, which refers to the page
 *      object.
 *  <LI> An unnamed, indirect destination, which refers to a
 *      named, direct destination, which refers to the page object.
 *  </UL>
 */
public final class Destination
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /* Flag indicating destination is indirect. */
    private boolean _indirect;

    /* Name of indirect destination. */
    private PdfSimpleObject _indirectDest;

    /* Page object for explicit destination. */
    private PdfDictionary _pageDest;

    /**
     *  Constructor. If this is a named destination, the destObj
     *  may be a PdfArray or a PdfDictionary;  if this is not a
     *  named destination, the destObj may be a PdfSimpleObject
     *  (encapsulating a Literal or Name) or a PdfDictionary.
     *
     *  @param  destObj      The destination object
     *  @param  module       The invoking PdfModule
     *  @param  named        Flag indicating whether this object came
     *                       from a named destination.
     */
    public Destination (PdfObject destObj, PdfModule module, boolean named)
                         throws PdfException
    {
        try {
            if (!named && destObj instanceof PdfSimpleObject) {
                _indirect = true;
                _indirectDest = (PdfSimpleObject) destObj;
            }
            else if (destObj instanceof PdfArray) {
                // We extract only the page reference, not the view.
                _indirect = false;
                Vector v= ((PdfArray) destObj).getContent ();
                _pageDest = (PdfDictionary) module.resolveIndirectObject
                        ((PdfObject) v.elementAt (0));
            }
            else if (named && destObj instanceof PdfDictionary) {
                PdfArray destObj1 = (PdfArray) 
                    ((PdfDictionary) destObj).get ("D");
                // the D entry is just like the array above.
                _indirect = false;
                Vector v= ((PdfArray) destObj1).getContent ();
                _pageDest = (PdfDictionary) module.resolveIndirectObject
                        ((PdfObject) v.elementAt (0));
            }
            else {
                throw new Exception ("");
            }
        }
        catch (Exception e) {
            throw new PdfInvalidException ("Invalid destination object");
        }
    }

    /** 
     *  Returns <code>true</code> if the destination is indirect.
     */
    public boolean isIndirect ()
    {
        return _indirect;
    }


    /**
     *  Returns the string naming the indirect destination.
     *  Returns null if the destination is not indirect.
     */
    public PdfSimpleObject getIndirectDest ()
    {
        return _indirectDest;
    }

    /**
     *  Returns the page object dictionary if the destination
     *  is direct.  Returns null if the destination is not
     *  direct.
     */
    public PdfDictionary getPageDest ()
    {
        return _pageDest;
    }

    /**
     *  Returns the object number of the page object dictionary
     *  if the destination is direct.  Throws a NullPointerException
     *  otherwise.
     */
    public int getPageDestObjNumber () throws NullPointerException
    {
        return _pageDest.getObjNumber ();
    }
}
