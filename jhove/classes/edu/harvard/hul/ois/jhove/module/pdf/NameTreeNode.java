/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;
import java.util.*;

/**
 *  Class for nodes of a PDF name tree, e.g., ExternalFiles.  Name trees
 *  are intended for large amounts of data that won't have to all be brought
 *  into memory at once; so this implementation is geared toward file-based
 *  lookup of a key rather than creating an in-memory structure.  Descendant
 *  nodes become available for garbage collection if they are not on the
 *  search path for a match.
 *
 *  Keys are collated according to raw bytes, not character encoding.
 */
public class NameTreeNode 
{
    protected PdfModule _module;
    protected NameTreeNode _parent;
    protected PdfDictionary _dict;  // dictionary which defines this node
    //private int _prevKey;        // Key previously obtained in traversing tree
    //private PdfObject _prevValue; // Value previously obtained in traversing tree
    //private NameTreeNode _currentDescendant;
    private Vector _kids;
    private Vector _names;
    private Vector _lowerLimit;     // Lower limit of keys for this node -- null for root
    private Vector _upperLimit;     // Upper limit of keys for this node -- null for root
    

    /**
     *  Constructor.
     *  @param module     The PdfModule under which we're operating
     *  @param parent     The parent node in the document tree;
     *                    may be null only for the root node
     *  @param dict       The dictionary object on which this node
     *                    is based
     */
    public NameTreeNode (PdfModule module,
                NameTreeNode parent, 
                PdfDictionary dict) throws PdfException
    {
	final String inval = "Invalid name tree";
        _module = module;
        _parent = parent;
        _dict = dict;
        
        try {
            // Get the limits of the key range.  If there are no limits, this
            // must be the root node.
            PdfArray limitsDict = (PdfArray) module.resolveIndirectObject
                (dict.get ("Limits"));
            if (limitsDict == null) {
                _lowerLimit = null;
                _upperLimit = null;
            }
            else {
                Vector vec = limitsDict.getContent ();
                PdfSimpleObject limobj = (PdfSimpleObject) vec.elementAt (0);
                _lowerLimit = limobj.getRawBytes ();
                //dumpKey (_lowerLimit, "Lower limit: ");
                limobj = (PdfSimpleObject) vec.elementAt (1);
                _upperLimit = limobj.getRawBytes ();
                //dumpKey (_upperLimit, "Upper limit: ");
            }
            
            // Get the Kids and Names arrays.  Normally only one will
            // be present.
            PdfArray kidsVec = (PdfArray) module.resolveIndirectObject
                (dict.get ("Kids"));
            if (kidsVec != null) {
                _kids = kidsVec.getContent ();
            }
            else {
                _kids = null;
            }
            PdfArray namesVec = (PdfArray) module.resolveIndirectObject
                (dict.get ("Names"));
            if (namesVec != null) {
                _names = namesVec.getContent ();
            }
            else {
                _names = null;
            }
        }
        catch (ClassCastException ce) {
            throw new PdfInvalidException (inval);
        }
        catch (NullPointerException ce) {
            throw new PdfInvalidException (inval);
        }
        catch (Exception e) {
            throw new PdfMalformedException (inval);
        }
    }
    
    /**
     * See if a key is within the bounds of this node.  All keys
     * are within the bounds of the root node.
     */
    public boolean inBounds (Vector key) 
    {
        if (_lowerLimit == null) {
            return true;    // root node
        }
        else {
            if (compareKey (key, _lowerLimit) < 0 || 
                compareKey (key, _upperLimit) > 0) {
                return false;
            }
            return true;
        }
    }
    
    
    /** 
     *  Get the PdfObject which matches the key, or null if there is no match.
     */
    public PdfObject get (Vector key) throws PdfException
    {
        final String invtree = "Invalid name tree";
        try {
            if (!inBounds (key)) {
                return null;
            }
            // If this has a Names array, it's a leaf node or standalone root;
            // search it for the key.
            if (_names != null) {
                for (int i = 0; i < _names.size (); i += 2) {
                    PdfSimpleObject k1 = (PdfSimpleObject) _names.elementAt (i);
                    int cmp = compareKey (key, k1.getRawBytes ());
                    if (cmp == 0) {
                        /* Match! */
                        return _module.resolveIndirectObject
                            ((PdfObject) _names.elementAt (i + 1));
                    }
                    else if (cmp < 0) {
                        // Passed position where match should be
                        return null; 
                    }
                }
                return null;     // just not there
            }
            else if (_kids != null) {
                // It's a non-standalone root or an intermediate note.
                // Figure out which descendant we should search.
                for (int i = 0; i < _kids.size (); i++) {
                    PdfDictionary kid = (PdfDictionary)
                        _module.resolveIndirectObject (
                            (PdfObject) _kids.elementAt (i));
                    NameTreeNode kidnode = new NameTreeNode (_module, this, kid);
                    if (kidnode.inBounds (key)) {
                        return kidnode.get (key);
                    }
                }
                return null;    // Not in any subnode
            }
            else throw new PdfMalformedException (invtree);
        }
        catch (PdfException e1) {
            throw e1;
        }
        catch (Exception e) {
            throw new PdfMalformedException (invtree);
        }
    }

    /*  Compare two keys (Vectors of Integer).  Returns -1 if the
        first argument is less than the second, 1 if the first argument
        is greater, and 0 if they are equal.  Key A is less than key B
        if A is a prefix of B. */
    private int compareKey (Vector a, Vector b) {
        int lena = a.size ();
        int lenb = b.size ();
        int len = (lena < lenb ? lena : lenb);
        for (int i = 0; i < len; i++) {
            int ai = ((Integer) a.elementAt (i)).intValue ();
            int bi = ((Integer) b.elementAt (i)).intValue ();
            if (ai < bi) {
                return -1;
            }
            else if (ai > bi) {
                return 1;
            }
        }
        // Both are equal as far as the length of the shorter one goes.
        // To be equal, they must have the same length; otherwise the
        // shorter one is the lesser.
        if (lena == lenb) {
            return 0;
        }
        else if (lena < lenb) {
            return -1;
        }
        else {
            return 1;
        }
    }
    
    
    /* Debugging code */
    private void dumpKey (Vector v, String label) 
    {
        System.out.print (label);
        for (int i = 0; i < v.size (); i++) {
            System.out.print (v.elementAt (i).toString () + " ");
        }
        System.out.println ();
    }
}

