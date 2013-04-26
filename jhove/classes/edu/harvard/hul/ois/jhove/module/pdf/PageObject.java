/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.io.*;
import java.util.*;

/**
 *  Class encapsulating a PDF page object node.
 */
public class PageObject extends DocNode 
{
    private List _contentStreams;  // contents of the page; may be null
    private static final String badPageStr = "Invalid dictionary data for page";

    /**
     *  Superclass constructor.
     *  @param module     The module under which we're operating
     *  @param parent     The parent node in the document tree;
     *                    may be null only for the root node
     *  @param dict       The dictionary object on which this node
     *                    is based
     */
    public PageObject (PdfModule module,
                PageTreeNode parent, 
                PdfDictionary dict)
    {
        super (module, parent, dict);
        _contentStreams = null;
        _pageObjectFlag = true;
    }

    /**
     *  Find the content stream(s) for this page.  This is
     *  called when the page tree content stream is built
     *  by PageTreeNode.  <code>getContentStreams</code> may 
     *  subsequently be called to get the content.
     */
    public void loadContent (PdfModule module) throws PdfException
    {
        try {
            PdfObject contents = _dict.get("Contents");
            // the Contents entry in the dictionary may be either
            // a stream or an array of streams.  It may also
            // be null, indicating no content.
            if (contents != null) {
                contents = module.resolveIndirectObject (contents);
                if (contents instanceof PdfStream) {
                    _contentStreams = new ArrayList(1);
                    _contentStreams.add(contents);
                    return;
                }
                else if (contents instanceof PdfArray) {
                    Vector contentVec = 
                        ((PdfArray) contents).getContent ();
                    if (contentVec.size () == 0) {
                        return;
                    }
                    _contentStreams = new ArrayList 
                                        (contentVec.size ());
                    for (int i = 0; i < contentVec.size (); i++) {
                        PdfObject streamElement = (PdfObject)
                                contentVec.elementAt (i);
                        streamElement = module.resolveIndirectObject
                                (streamElement);
                        _contentStreams.add ((PdfStream) streamElement);
                    }
                }
                else {
                    throw new PdfInvalidException (badPageStr, 0);
                }
            }
        }
        catch (NullPointerException e) {
            throw new PdfInvalidException (badPageStr, 0);
        }
        catch (ClassCastException e) {
            throw new PdfInvalidException (badPageStr, 0);
        }
        catch (IOException e) {
            throw new PdfMalformedException (badPageStr, 0);
        }
    }
    
    /**
     *   Returns the List of content streams.  The list elements are
     *   of type PdfStream.
     */
    public List getContentStreams ()
    {
        return _contentStreams;
    }
    
    /**
     *  Return the page's Annots array of dictionaries, or null if none
     */
    public PdfArray getAnnotations () throws PdfException
    {
        String badAnnot = "Invalid Annotations";
        try {
            return (PdfArray) _module.resolveIndirectObject (_dict.get ("Annots"));
        }
        catch (ClassCastException e) {
            throw new PdfInvalidException (badAnnot);
        }
        catch (IOException e) {
            throw new PdfMalformedException (badAnnot);
        }
    }


    /**
     *  Call this function when recursively walking through a document
     *  tree.  This allows nextPageObject () to be return this object
     *  exactly once.
     */
    public void startWalk ()
    {
        _walkFinished = false;
    }
    
    /**
     *  Returns this object the first time it is called after startWalk
     *  is called, then null when called again.  This allows a recursive
     *  walk through a document tree to work properly.
     */
    public PageObject nextPageObject ()
    {
        if (_walkFinished)
            return null;
        _walkFinished = true;
        return this;
    }

    /**
     *  Called to walk through all page tree nodes and page objects.
     *  Functionally identical with nextPageObject.
     */
    public DocNode nextDocNode ()
    {
        return nextPageObject ();
    }
    
    /**
     *  Returns the ArtBox for the page, or null if none.  Throws a
     *  PDFException if there is an ArtBox but it is not a rectangle.
     */
    public PdfArray getArtBox () throws PdfException
    {
        final String badbox = "Malformed ArtBox in page tree";
        try {
            PdfArray mbox = (PdfArray) _dict.get ("ArtBox");
            if (mbox == null) {
                return null;
            }
            else if (mbox.toRectangle () != null) {
                return mbox;
            }
            else {
                // There's an ArtBox, but it's not a rectangle
                throw new PdfInvalidException (badbox);
            }
        }
        catch (Exception e) {
            throw new PdfMalformedException (badbox);
        }
    }

    /**
     *  Returns the TrimBox for the page, or null if none.  Throws a
     *  PDFException if there is an TrimBox but it is not a rectangle.
     */
    public PdfArray getTrimBox () throws PdfException
    {
        final String badbox = "Malformed TrimBox in page tree";
        try {
            PdfArray mbox = (PdfArray) _dict.get ("TrimBox");
            if (mbox == null) {
                return null;
            }
            else if (mbox.toRectangle () != null) {
                return mbox;
            }
            else {
                // There's an TrimBox, but it's not a rectangle
                throw new PdfInvalidException (badbox);
            }
        }
        catch (Exception e) {
            throw new PdfMalformedException (badbox);
        }
    }

    /**
     *  Returns the BleedBox for the page, or null if none.  Throws a
     *  PDFException if there is an BleedBox but it is not a rectangle.
     */
    public PdfArray getBleedBox () throws PdfException
    {
        final String badbox = "Malformed BleedBox in page tree";
        try {
            PdfArray mbox = (PdfArray) _dict.get ("BleedBox");
            if (mbox == null) {
                return null;
            }
            else if (mbox.toRectangle () != null) {
                return mbox;
            }
            else {
                // There's an BleedBox, but it's not a rectangle
                throw new PdfInvalidException (badbox);
            }
        }
        catch (Exception e) {
            throw new PdfMalformedException (badbox);
        }
    }
}
