/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;
import java.io.*;
import java.util.*;

/**
 *  Class for PDF document structure tree.
 *  See section 9.6, "Logical Structure," of PDF Reference,
 *  Version 1.4, for an explanation of the document structure.
 *
 *  @see StructureElement
 */
public class StructureTree 
{
    private PdfModule _module;
    private RandomAccessFile _raf;
    private Parser _parser;
    private PdfDictionary _rootDict;
    private PdfDictionary _roleMap;
    private List children;
    private boolean _present;
    private boolean _valid;

    /**
     *  Constructor.  If there is a document structure tree,
     *  this fills in the appropriate information.  If there isn't,
     *  it does nothing.  Call isPresent() to determine whether
     *  there is a document structure tree.  A PdfInvalidException may be
     *  thrown if there is a structure tree but it is invalid.
     *
     *  @param module     The PdfModule under which we're operating
     *  @param raf        The document file object
     *  @param parser     The Parser being used
     */
    public StructureTree (PdfModule module,
		RandomAccessFile raf,
		Parser parser) throws PdfException
    {
        _module = module;
        _raf = raf;
        _parser = parser;
        try {
            PdfDictionary docCatDict = module.getCatalogDict ();
    	    // There must be an entry in the catalog dictionary
    	    // named StructTreeRoot.  If there isn't, set _present
    	    // to false.
           _rootDict = null;
            try {
            _rootDict = (PdfDictionary) _module.resolveIndirectObject
                ((PdfObject) docCatDict.get ("StructTreeRoot"));
            }
            catch (IOException e) {}
            if (_rootDict == null) {
                _present = false;
                _valid = false;
                return;
    	    }
            _present = true;
            validateRoot ();
            getRoleMap ();
            children = getChildren ();
            _valid = true; 
    	}
        catch (Exception e) {
            _valid = false;
        }
    }
    
    /**
     *  Returns <code>true</code> if and only if the document
     *  structure exists. 
     */
    public boolean isPresent ()
    {
        return _present;
    }


    /**
     *   Returns <code>true</code> if and only if no errors were
     *   detected.
     */
    public boolean isValid ()
    {
        return _valid;
    }


    /** Returns the module associated with this object. */
    public PdfModule getModule ()
    {
        return _module;
    }


    /**
     *  Dereference a name in the role map.
     *  If there is no role map, or if the parameter is not
     *  mapped by the role map, the original parameter will
     *  be returned.  The string will be looked up through
     *  multiple levels in the role map.  The maximum number
     *  of levels is limited to 50, in case of circular
     *  mappings.  The value returned will be null if the
     *  role map contains invalid data or the limit of 50
     *  lookups is reached.
     */
    public String dereferenceStructType (String st) 
    {
        if (_roleMap == null) {
            return st;
        }
        // There could be a circular mapping, so we limit the
        // number of concatenated lookups.
        for (int i = 0; i < 50; i++) {
            try {
                PdfSimpleObject mapped = 
                    (PdfSimpleObject) _roleMap.get (st);
                if (mapped == null) {
                    return st;
                }
                st = mapped.getStringValue ();
            }
            catch (Exception e) {
                return null;  // BAD dictionary! No mapping!
            }
        }
        return null;    // Looks like an infinite loop
    }


    /* See if the root is valid.  If not, throw a PDFException. */
    private void validateRoot () throws PdfException
    {
        final String badRoot = "Invalid document structure root";
        try {
            PdfSimpleObject typ = 
        	(PdfSimpleObject)_rootDict.get ("Type");
            if (!"StructTreeRoot".equals (typ.getStringValue ())) {
                throw new PdfInvalidException (badRoot);
            }
        }
        catch (PdfException e) {
            throw e;
        }
        catch (Exception e) {
            throw new PdfInvalidException (badRoot);
        }
    }

    /**
     *  Replaces a string with a string to which the role map
     *  maps it.  This may involve multiple levels of lookup.
     */

    /* Build a list of the children of the root. The
       elements of the list are StructureElements.
       Returns null if there are none. */
    private List getChildren () throws PdfException
    {
	final String invdata = "Invalid data in document structure root";
	List kidsList = null;
	PdfObject kids = null;
	try {
	    kids = _module.resolveIndirectObject
		(_rootDict.get ("K"));
	}
	catch (IOException e) {}
	if (kids == null) {
	    return null;
	}

	if (kids instanceof PdfDictionary) {
	    // Only one child
	    kidsList = new ArrayList (1);
	    StructureElement se = new StructureElement 
		((PdfDictionary) kids, this);
	    se.buildSubtree ();
	    se.checkAttributes ();
	    kidsList.add (se);
	    return kidsList;
	}
	else if (kids instanceof PdfArray) {
	    // Multiple children
	    Vector kidsVec = ((PdfArray) kids).getContent ();
	    kidsList = new ArrayList (kidsVec.size ());
	    for (int i = 0; i < kidsVec.size (); i++) {
		PdfObject kid;
		try {
		    kid = _module.resolveIndirectObject
			((PdfObject) kidsVec.elementAt (i));
		}
		catch (IOException e) {
		    throw new PdfMalformedException (invdata);
		}
		StructureElement se = new StructureElement 
			((PdfDictionary) kid, this);
		se.buildSubtree ();
		se.checkAttributes ();
		kidsList.add (se);
	    }
	    return kidsList;
	}
	else {
	    throw new PdfInvalidException (invdata);
	}
    }


    /*  Extract and save the role map, if any.  Throw an
        exception if RoleMap names something that isn't
        a dictionary. It's legitimate for roleMap to be null. */
    private void getRoleMap () throws PdfException
    {
	final String invdata = "Invalid RoleMap";
	try {
	    _roleMap = (PdfDictionary) _module.resolveIndirectObject
		(_rootDict.get ("RoleMap"));
	}
	catch (Exception e) {
	    throw new PdfInvalidException (invdata);
	}
    }

}
