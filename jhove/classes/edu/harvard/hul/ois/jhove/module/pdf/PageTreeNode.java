/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.util.*;

/**
 *  Class encapsulating a PDF page tree node.
 *  The page tree is built such that callers can walk through
 *  it by calling startWalk and then calling nextDocNode
 *  (for all nodes) or nextPageObject (for pages only) repeatedly.
 */
public class PageTreeNode extends DocNode 
{
    /* The descendant DocNodes. */
    private List<DocNode> _descendants;
    private ListIterator<DocNode> _descendantsIter;
    private DocNode _currentDescendant;
    private boolean _walkFirst;
    private Set<Integer> _visitedNodes;

    /**
     *  Superclass constructor.
     *  @param module     The PDFModule under which we're operating
     *  @param parent     The parent node in the document tree;
     *                    may be null only for the root node
     *  @param dict       The dictionary object on which this node
     *                    is based
     */
    public PageTreeNode (PdfModule module,
		PageTreeNode parent, 
		PdfDictionary dict)
    {
        super (module, parent, dict);
        _pageObjectFlag = false;
        _descendants = new ArrayList<DocNode> (1);  // Empty list in case it doesn't get built
    }

    /**
     *  Builds the subtree of descendants of this node, using
     *  the Kids entry in the dictionary.
     */
    public void buildSubtree (boolean toplevel, int recGuard)
	throws PdfException
    {
        buildSubtree (toplevel, recGuard, -1, -1);
    }
    
    /**
     *  Builds the subtree of descendants of this node, using
     *  the Kids entry in the dictionary.
     */
    public void buildSubtree (boolean toplevel, int recGuard, int objNumber, int genNumber) throws PdfException
    {
        /* Guard against infinite recursion */
        if (recGuard <= 0) {
            throw new PdfMalformedException ("Excessive depth or infinite recursion in page tree structure");
        }
        PdfArray kids = null;
        try {
            /* Section 3.6.2 of the PDF 1.6 doc says:
             * "Applications should be prepared
             * to handle any form of tree structure built of such nodes
             * [page tree nodes and page nodes]. The simplest structure
             * would consist of a single page tree node that references
             * all of the document's page objects directly."
             * But actually, the simplest structure would be a single
             * page node.  And it appears that Acrobat 7 will indeed
             * generate such.
             */
	    /* Note that the Kids dictionary can be an indirect object. */
	    PdfObject obj = _dict.get("Kids");
	    if (obj instanceof PdfIndirectObj) {
	        kids = (PdfArray) (((PdfIndirectObj) obj).getObject ());
	    }
	    else {
            kids = (PdfArray) obj;
	    }
            if (toplevel && kids == null) {
                // The single page node case, maybe.
                PdfSimpleObject type = (PdfSimpleObject) _dict.get ("Type");
                if (type != null &&
                        "Page".equals (type.getStringValue())) {
                    PageObject pageObj = new PageObject
                        (_module, this, _dict);
                    _descendants = new ArrayList<DocNode> (1);
                    _descendants.add (pageObj);
                }
            }
            else {
                Vector<PdfObject> kidsVec = kids.getContent ();
                _descendants = new ArrayList<DocNode> (kidsVec.size ());
                for (int i = 0; i < kidsVec.size (); i++) {
                    PdfIndirectObj kidRef = 
                            (PdfIndirectObj) kidsVec.elementAt (i);
		    /**************************************************
		     * To avoid a simple case of infinite recursion, check
		     * that this kid is not the same page object as its
		     * parent.
		     **************************************************/
		    /**************************************************
		    int kidObjNumber = kidRef.getObjNumber ();
		    int kidGenNumber = kidRef.getGenNumber ();
		    if (objNumber >= 0 && genNumber >= 0 &&
			objNumber == kidObjNumber &&
			genNumber == kidGenNumber) {
			break;
		    }
		    **************************************************/
                    PdfDictionary kid = (PdfDictionary)
                            _module.resolveIndirectObject (kidRef);
                    PdfSimpleObject kidtype = 
                            (PdfSimpleObject) kid.get("Type");
                    String kidtypeStr = kidtype.getStringValue ();
                    if (kidtypeStr.equals("Page")) {
                        PageObject pageObj = new PageObject 
                            (_module, this, kid);
                        pageObj.loadContent (_module);
                        _descendants.add(pageObj);
                    }
                    else if (kidtypeStr.equals ("Pages")) {
                        PageTreeNode nodeObj = 
                            new PageTreeNode (_module, this, kid);
                        nodeObj.buildSubtree (false, recGuard - 1);
                        _descendants.add(nodeObj);
                    }
                }
            }
        }
        catch (PdfException ee) {
            throw ee;
        }
        catch (Exception e) {
            throw new PdfInvalidException ("Invalid page tree node");
        }
	
    }

    /**
     *  Initialize an iterator through the descendants of this node.
     */
    public void startWalk ()
    {
        _descendantsIter = _descendants.listIterator ();
        _currentDescendant = null;
        _walkFirst = true;
        _walkFinished = false;
        _visitedNodes = new HashSet<Integer> ();   // Track self-recursion
    }
    
    /**
     *   Get the next PageObject which is under this node.  This function
     *   is designed such that calling startWalk() and then repeatedly
     *   calling nextPageObject() will return all the PageObjects in the tree
     *   under this node, and finally will return null when there are no more.
     */
    public PageObject nextPageObject () throws PdfMalformedException
    {
        if (_walkFinished) {
            return null;
        }
        // _currentDescendant == null and _walkFinished == false indicates
        // we're at the start.
        if (_currentDescendant == null) {
           if (!_descendantsIter.hasNext ()) {
                _walkFinished = true;
                return null;
           }

           // Get first descendant
           _currentDescendant = (DocNode) _descendantsIter.next ();
           _currentDescendant.startWalk ();
        }
        
        PageObject retval = _currentDescendant.nextPageObject ();
        if (retval == null) {
            if (_descendantsIter.hasNext ()) {
                // Every node is a page object or 
                // has at least one page object below it, right?
                _currentDescendant = (DocNode) _descendantsIter.next ();
                _currentDescendant.startWalk ();
                retval = _currentDescendant.nextPageObject ();
            }
            else {
                // We've gone through all our descendants.
                _walkFinished = true;
                retval = null;
            } 
        }
        if (retval != null) {
            int objnum = retval.getDict().getObjNumber();
            if (_visitedNodes.contains((Integer) objnum)) {
                throw new PdfMalformedException("Improperly constructed page tree");
            }
            _visitedNodes.add(objnum);
        }
        return retval;
    } 
     
    /**
     *   Get the next DocNode which is under this node.  This function
     *   is designed such that calling startWalk() and then repeatedly
     *   calling nextPageObject() will return first this node,
     *   then all the DocNodes in the tree
     *   under this node. It finally will return null when there 
     *   are no more.
     */
    public DocNode nextDocNode () throws PdfMalformedException
    {
        if (_walkFinished) {
            return null;
        }
        // _walkFinished == false and _walkFirst == true indicates
        // we need to return "this".
        if (_walkFirst) {
            _walkFirst = false;
            return this;
        }
        // _currentDescendant == null and _walkFinished == false indicates
        // we're at the start.  This is almost identical to the
        // logic for nextPageObject.
        if (_currentDescendant == null) {
            if (!_descendantsIter.hasNext ()) {
                _walkFinished = true;
                return null;
            }

            // Get first descendant
            _currentDescendant = (DocNode) _descendantsIter.next ();
            _currentDescendant.startWalk ();
        }
        
        DocNode retval = _currentDescendant.nextDocNode ();
        if (retval == null) {
            if (_descendantsIter.hasNext ()) {
                // Every node is a page object or 
                // has at least one page object below it, right?
                _currentDescendant = (DocNode) _descendantsIter.next ();
                _currentDescendant.startWalk ();
                retval = _currentDescendant.nextDocNode ();
            }
            else {
                // We've gone through all our descendants.
                _walkFinished = true;
                retval = null;
            } 
        }
        if (retval != null) {
            int objnum = retval.getDict().getObjNumber();
            if (_visitedNodes.contains((Integer) objnum)) {
                throw new PdfMalformedException("Improperly constructed page tree");
            }
            _visitedNodes.add(objnum);
        }
        return retval;
    } 
}
