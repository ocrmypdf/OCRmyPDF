/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;
import java.io.*;

/**
 *  Abstract class for nodes of a PDF document tree.
 */
public abstract class DocNode 
{
    /** The PdfModule this node is associated with. */
    protected PdfModule _module;
    
    /** The parent node of this node. */
    protected PageTreeNode _parent;
    
    /** The dictionary which defines this node. */
    protected PdfDictionary _dict;  
    
    /** True if this node is a PageObject. */
    protected boolean _pageObjectFlag;
    
    /** Set to true when all subnodes of this node
     *  have been iterated through following a StartWalk. */
    protected boolean _walkFinished;

    /**
     *  Superclass constructor.
     *  @param module     The PdfModule under which we're operating
     *  @param parent     The parent node in the document tree;
     *                    may be null only for the root node
     *  @param dict       The dictionary object on which this node
     *                    is based
     */
    public DocNode (PdfModule module,
                PageTreeNode parent, 
                PdfDictionary dict)
    {
        _module = module;
        _parent = parent;
        _dict = dict;
        // Debug code
        PdfIndirectObj parentRef = (PdfIndirectObj) _dict.get ("Parent");
    }
    
    /**
     *  Returns true if this node is a PageObject.
     */
    public boolean isPageObject ()
    {
        return _pageObjectFlag;
    }
    
    /**
     *  Initialize an iterator through the descendants of this node.
     */
    public abstract void startWalk ();

    /**
     *   Get the next PageObject which is under this node.  
     */
    public abstract PageObject nextPageObject () throws PdfMalformedException;

    /**
     *   Get the next DocNode which is under this node.
     *   All PageTreeNodes and PageObjects are eventually returned
     *   by walking through a structure with nextNode.
     */
    public abstract DocNode nextDocNode () throws PdfMalformedException;
    
    /**
     *   Returns the parent of this node.
     */
    public DocNode getParent ()
    {
        return _parent;
    }

    /**
     *  Returns the page object or page tree node dictionary from 
     *  which this object was constructed.
     */
    public PdfDictionary getDict ()
    {
	return _dict;
    }


    /**
     *  Get the Resources dictionary.  Either a PageTreeNode or
     *  a PageObject can have a Resources dictionary. Returns
     *  null if there is no Resources dictionary.  The object
     *  may be referenced indirectly.
     */
    public PdfDictionary getResources () throws PdfException
    {
        String invres = "Invalid Resources Entry in document";
        if (_dict == null) {
            throw new PdfMalformedException ("Missing dictionary in document node");
        }
        try {
            PdfObject resdict = _dict.get ("Resources");
            resdict = _module.resolveIndirectObject (resdict);
            return (PdfDictionary) resdict;
        }
        catch (ClassCastException e) {
            throw new PdfInvalidException (invres);
        }
        catch (IOException f) {
            throw new PdfInvalidException (invres);
        }
    }

    /**
     *  Returns the dictionary of fonts within the node's Resources
     *  dictionary, if both exist.  Otherwise returns null.
     *  The dictionary will most often have indirect object
     *  references as values.  What is returned is not a
     *  Font dictionary, but rather a dictionary of Font
     *  dictionaries.
     */
    public PdfDictionary getFontResources () throws PdfException
    {
        PdfDictionary resdict = getResources ();
        if (resdict != null) {
            try {
                PdfObject fontdict = (PdfObject) resdict.get("Font");
                fontdict = _module.resolveIndirectObject (fontdict);
                return (PdfDictionary) fontdict;
            }
            catch (Exception e) {
                throw new PdfMalformedException 
                        ("Invalid Font entry in Resources");
            }
        }
        else {
            return null;
        }
    }
    
    /**
     *  Get the MediaBox of this node.  MediaBox is an inheritable
     *  property, so it walks up the chain of ancestors if it doesn't
     *  contain one.  Returns null if none.  Throws a 
     *  PdfInvalidException if an invalid MediaBox is found.
     */
    public PdfArray getMediaBox () throws PdfInvalidException
    {
        final String badbox = "Malformed MediaBox in page tree";
        try {
	    PdfArray mbox = (PdfArray) get ("MediaBox", true);
            if (mbox.toRectangle () != null) {
                return mbox;
            }
            else {
                // There's a MediaBox, but it's not a rectangle
                throw new PdfInvalidException (badbox);
            }
        }
        catch (Exception e) {
            throw new PdfInvalidException (badbox);
        }
    }

    /**
     *  Get an named property.  If this object doesn't
     *  have the specified property and <code>inheritable</code>
     *  is true, walks up the chain of ancestors
     *  to try to find one.  If no ancestor has the property or
     *  inheritable is false, returns null.
     */
    public PdfObject get (String key, boolean inheritable) 
    {
	PdfObject val = _dict.get (key);
	if (val == null) {
	    if (_parent == null || !inheritable) {
		return null;
	    }
	    else {
		return _parent.get (key, inheritable);
	    }
	}
	else {
	    return val;
	}
    }
}
