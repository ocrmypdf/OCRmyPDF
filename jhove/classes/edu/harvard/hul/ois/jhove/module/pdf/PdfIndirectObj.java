/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;

/**
 *  A representation of a PDF indirect object reference.
 */
public class PdfIndirectObj extends PdfObject
{

    private Map _objectMap;
    private PdfObject _cachedObject;

    /** 
     *  Creates a PdfIndirectObj object.  
     *
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     *  @param objectMap  The object map for the PDF file
     */
    public PdfIndirectObj (int objNumber, int genNumber, Map objectMap)
    {
        super (objNumber, genNumber);
        _objectMap = objectMap;
        _cachedObject = null;
    }

    /**
     *  Retrieves the object which is referenced.  Uses the
     *  cached reference if there is one; caches the reference
     *  if there wasn't one before.
     */
    public PdfObject getObject ()
    {
        if (_cachedObject != null) {
	        return _cachedObject;
        }
        else {
            long key = ((long) _objNumber << 32) +
			    ((long) _genNumber & 0XFFFFFFFFL);
            _cachedObject = (PdfObject) _objectMap.get (new Long (key));
            return _cachedObject;
        }
    }
}
