/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;
import java.util.*;

/**
 *  Class for nodes of a PDF number tree.
 */
public class PageLabelNode 
{
    /** The PdfModule this node is associated with. */
    protected PdfModule _module;
    
    /** The parent node of this node. */
    protected PageLabelNode _parent;

    /** The dictionary which defines this node. */
    protected PdfDictionary _dict;

    /** Set to true when all subnodes of this node
     *  have been iterated through following a StartWalk. */
    protected boolean _walkFinished;

    private List<PageLabelNode> _descendants;
    private Iterator<PageLabelNode> _descendantsIter;
    private int _currentKey;        // Key most recently obtained in traversing tree
    private PdfObject _currentValue; // Value most recently obtained in traversing tree
    private int _prevKey;        // Key previously obtained in traversing tree
    private PdfObject _prevValue; // Value previously obtained in traversing tree
    private int _currentNumsIndex;  // Current index into Nums entry
    private int _currentNumsLength; // Length of current Nums entry
    private Vector _currentNumsVec; // Vector from the Nums entry
    private PageLabelNode _currentDescendant;
    private PageLabelNode _currentLeaf;

    /**
     *  Superclass constructor.
     *  @param module     The PdfModule under which we're operating
     *  @param parent     The parent node in the document tree;
     *                    may be null only for the root node
     *  @param dict       The dictionary object on which this node
     *                    is based
     */
    public PageLabelNode (PdfModule module,
                PageLabelNode parent, 
                PdfDictionary dict)
    {
        _module = module;
        _parent = parent;
        _dict = dict;
    }
    

    /**
     *  Build the subtree of descendants of this node, using
     *  the Kids entry in the dictionary.  Leaf nodes are
     *  recognized by not having a Kids entry.
     */
    public void buildSubtree () throws PdfException
    {
        PdfArray kids = null;
        try {
            kids = (PdfArray) _dict.get("Kids");
            if (kids != null) {
                Vector<PdfObject> kidsVec = kids.getContent ();
                _descendants = new ArrayList<PageLabelNode> (kidsVec.size ());
                for (int i = 0; i < kidsVec.size (); i++) {
                    PdfDictionary kid = (PdfDictionary)
                            _module.resolveIndirectObject 
                                ((PdfObject) kidsVec.elementAt (i));
                    PageLabelNode nodeObj = 
                        new PageLabelNode (_module, this, kid);
                    nodeObj.buildSubtree ();
                    _descendants.add(nodeObj);
                }
            }
            else _descendants = null;
        }
	catch (PdfException pe) {
	    throw pe;
	}
        catch (Exception e) {
            throw new PdfInvalidException ("Invalid page label node");
        }
           
    }
    
    /**
     *  Initialize an iterator through the descendants of this node.
     */
    public void startWalk ()
    {
        if (_descendants != null) {
            _descendantsIter = _descendants.listIterator ();
            _walkFinished = false;
        }
        else {
            _descendantsIter = null;   // leaf node, or root in isolation
            _walkFinished = true;
        }
        _currentDescendant = null;
        _currentLeaf = null;
        _currentKey = -1;
        _currentValue = null;
	_prevKey = -1;
	_prevValue = null;
    }

    /**
     *   Get the next leaf object which is under this node.  This function
     *   is designed such that calling startWalk() and then repeatedly
     *   calling nextLeafObject() will return all the leaf objects in the tree
     *   under this node, and finally will return null when there are no more.
     *   A leaf object is one which has no Kids; it is required to have a
     *   Nums entry.
     */
    public PageLabelNode nextLeafObject ()
    {
        if (_walkFinished) {
            return null;
        }
        // _currentDescendant == null and _walkFinished == false indicates
        // we're at the start.
        if (_currentDescendant == null) {
            if (_descendantsIter == null) {
                // No descendants.  This is a root node which functions as its
                // only leaf.
                _walkFinished = true;
                return this;
            }
            else {
                // Get first descendant
                _currentDescendant = (PageLabelNode) _descendantsIter.next ();
                _currentDescendant.startWalk ();
            }
        }
        
        PageLabelNode retval = _currentDescendant.nextLeafObject ();
        if (retval == null) {
            if (_descendantsIter.hasNext ()) {
                _currentDescendant = (PageLabelNode) _descendantsIter.next ();
                _currentDescendant.startWalk ();
                return _currentDescendant.nextLeafObject ();
            }
            else {
                // We've gone through all our descendants.
                _walkFinished = true;
                return null;
            } 
        }
        else return retval;
    } 

    /**
     *  Obtain the next key-value pair from the tree.  This returns true
     *  if a pair is available, false if not.  After this is called,
     *  getCurrentKey and getCurrentValue may be called to retrieve the
     *  key and value thus found.  Each time this is called,
     *  currentKey and currentValue get copied into prevKey and
     *  prevValue.
     */
    public boolean findNextKeyValue () throws PdfException
    {
        try {
            if (_currentLeaf == null || _currentNumsIndex >= _currentNumsLength) {
                _currentLeaf = nextLeafObject ();
                if (_currentLeaf == null) {
		    _prevKey = _currentKey;
		    _prevValue = _currentValue;
		    _currentKey = Integer.MAX_VALUE;
                    return false;      // all done
                }
                _currentNumsIndex = 0;
                PdfArray pairArray = (PdfArray) 
                    _module.resolveIndirectObject (_currentLeaf._dict.get ("Nums"));
                if (pairArray == null) {
                    throw new PdfInvalidException ("Missing expected element in page number dictionary");
                }
                _currentNumsVec = pairArray.getContent ();
                _currentNumsLength = _currentNumsVec.size ();
            }
            
            // The key and the value are in two successive positions in the
            // array, which is of the form [key value key value ... ]
            PdfSimpleObject keyObj = (PdfSimpleObject) 
                    _currentNumsVec.elementAt (_currentNumsIndex);
            // Save the previous key-value pair
            _prevKey = _currentKey;
            _prevValue = _currentValue;
            _currentKey = keyObj.getIntValue ();
            
            _currentValue = (PdfObject) 
                    _currentNumsVec.elementAt (_currentNumsIndex + 1);
            _currentNumsIndex += 2;
            
            return true;
        }
        catch (PdfInvalidException e) {
            throw e;
        }
        catch (Exception e) {
            e.printStackTrace();
            throw new PdfInvalidException ("Invalid date in page number tree");
        }
    }
    
    /**
     *  Returns key at current position in traversing tree
     */
    public int getCurrentKey () 
    {
        return _currentKey;
    }
    
    /**
     *  Returns value associated with current key
     */
    public PdfObject _getCurrentValue ()
    {
        return _currentValue;
    }

    /**
     *  Returns key previously obtained in traversing tree 
     */
    public int getPrevKey () 
    {
        return _prevKey;
    }
    
    /**
     *  Returns value associated with key previously obtained
     *  in traversing tree
     */
    public PdfObject getPrevValue ()
    {
        return _prevValue;
    }

    /**
     *  A convenience method to turn integers into Roman
     *  numerals, for the generation of page labels.
     */
    public static String intToRoman (int n, boolean upperCase)
    {
	StringBuffer buf = new StringBuffer ();
	// Numbers of a thousand or more start with an "M" for
	// each full thousand.
	while (n >= 1000) {
	    buf.append ("M");
	    n -= 1000;
	}
	// treat "CM" as a special case.
	if (n >= 900) {
	    buf.append ("CM");
	    n -= 900;
	}
	// 500 through 899 uses D, DC, DCC, DCCC
	if (n >= 500) {
	    buf.append ("D");
	    while (n >= 600) {
		buf.append ("C");
		n -= 100;
	    }
	    n -= 500;
	}
	// 400 through 499 is CD
	if (n >= 400) {
	    buf.append ("CD");
	    n -= 400;
	}
	// 100 through 399 is C, CC, CCC
	while (n >= 100) {
	    buf.append ("C");
	    n -= 100;
	}
	// 90 through 99 is XC
	if (n >= 90) {
	    buf.append ("XC");
	    n -= 90;
	}
	// 50 through 89 is L, LX, LXX, LXXX
	if (n >= 50) {
	    buf.append ("L");
	    while (n >= 60) {
		buf.append ("X");
		n -= 10;
	    }
	    n -= 50;
	}
	// 40 through 49 is XL
	if (n >= 40) {
	    buf.append ("XL");
	    n -= 40;
	}
	// 10 through 39 is X, XX, XXX
	while (n >= 10) {
	    buf.append ("X");
	    n -= 10;
	}
	// From here on, nitpick it out with a switch statement.
	switch (n) {
	    case 1:
		buf.append ("I");
		break;
	    case 2:
		buf.append ("II");
		break;
	    case 3:
		buf.append ("III");
		break;
	    case 4:
		buf.append ("IV");
		break;
	    case 5:
		buf.append ("V");
		break;
	    case 6:
		buf.append ("VI");
		break;
	    case 7:
		buf.append ("VII");
		break;
	    case 8:
		buf.append ("VIII");
		break;
	    case 9:
		buf.append ("IX");
		break;
	}
	String val = buf.toString ();
	if (upperCase) {
	    return val;
	}
	else {
	    return val.toLowerCase ();
	}
    }
    /**
     *  A convenience method to turn integers into 
     *  "letter" page numbers as defined for PDF.  
     *  The first 26 pages are A-Z, the next 26 AA-ZZ,
     *  etc.
     */
    public static String intToBase26 (int n, boolean upperCase)
    {
	int repeatCount = ((n - 1) / 26) + 1;
	StringBuffer buf = new StringBuffer ();
	int ch;
	// Have ch be the appropriate character to repeat
	if (upperCase) {
	    ch = 65 + ((n - 1) % 26);
	}
	else {
	    ch = 97 + ((n - 1) % 26);
	}
	while (--repeatCount >= 0) {
	    buf.append ((char) ch);
	}
	return buf.toString ();
    }
}

