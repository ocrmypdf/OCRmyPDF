
package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.util.*;

/**
 *  PDF profile checker for PDF/X-2 documents.
 *  See ISO Standard ISO 15930-2:2003(E), "Graphic technology - 
 *  Prepress digital data exchange Use of PDF - Part 2: 
 *  Partial exchange of printing data (PDF/X-2)"
 */
public final class X2Profile extends XProfileBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /** 
     *   Constructor.
     *   Creates an X2Profile object for subsequent testing.
     *
     *   @param  module   The module under which we are checking the profile.
     *
     */
    public X2Profile (PdfModule module) 
    {
        super (module, XProfileBase.PDFX2);
        _profileText = "ISO PDF/X-2";
    }

    /** 
     * Returns <code>true</code> if the document satisfies the profile.
     *
     */
    public boolean satisfiesThisProfile ()
    {
        try {
            // First off, there must be an OutputIntents array
            // in the document catalog dictionary.
            PdfDictionary catDict = _module.getCatalogDict ();
            PdfArray intentsArray = (PdfArray) _module.resolveIndirectObject 
                    (catDict.get ("OutputIntents"));
            if (intentsArray == null) {
                return false;
            }
            
            // Next check if the OutputIntents are valid.
            if (!outputIntentsOK (intentsArray)) {
                return false;
            }

            // Check that bounding boxes are present as required.
            // MediaBox is required.
            if (!bboxOK (true)) {
                return false;
            }

	    // Check that ViewerPreferences meet certain restrictions
	    // if any BleedBoxes are present.
	    if (!checkPrefsAgainstBleedBox ()) {
		return false;
	    }

            // Check resources and other stuff.
            if (!resourcesOK ()) {
                return false;
            }

            // Check the trailer dictionary.
            if (!trailerDictOK ()) {
                return false;
            }


            // Check specific requirements on the doc info dictionary.
            if (!infoDictOK ("PDF/X-2:")) {
                return false;
            }


        }
        catch (Exception e) {
            // Any otherwise uncaught exception means nonconformance
            return false;
        }
        return true;  // Placeholder
    }
    
    /* Walk through the page tree and check all Resources dictionaries
       that we find.  Along the way, we check several things:
       
       Color spaces. Any Separation and DeviceN resources we
       find must have an AlternateSpace of DeviceGray or
       DeviceCMYK. 
       
       Extended graphic states.
       
       XObjects.
     */
    private boolean resourcesOK () 
    {
        PageTreeNode docTreeRoot = _module.getDocumentTree ();
        try {
            docTreeRoot.startWalk ();
            DocNode docNode;
            for (;;) {
                docNode = docTreeRoot.nextDocNode ();
                if (docNode == null) {
                    break;
                }
                // Check for node-level resources
                PdfDictionary rsrc = docNode.getResources ();
                if (rsrc != null) {
                

                    // Check extended graphics state.
                    PdfDictionary gs = (PdfDictionary)
                        _module.resolveIndirectObject
                            (rsrc.get ("ExtGState"));
                    if (!extGStateOK (gs)) {
                        return false;
                    }
                    
                    // Check XObjects.
                    PdfDictionary xo = (PdfDictionary)
                        _module.resolveIndirectObject
                            (rsrc.get ("XObject"));
                    if (!xObjectsOK (xo)) {
                        return false;
                    }
                }
                
                // Check content streams for  resources
                if (docNode instanceof PageObject) {
                    List streams = 
                        ((PageObject) docNode).getContentStreams ();
                    if (streams != null) {
                        Iterator iter = streams.listIterator ();
                        while (iter.hasNext ()) {
                            PdfStream stream = (PdfStream) iter.next ();
                            PdfDictionary dict = stream.getDict ();
                            PdfDictionary rs = 
                                (PdfDictionary) dict.get ("Resources");
                            if (rs != null) {
                                PdfDictionary gs = (PdfDictionary)
                                    _module.resolveIndirectObject
                                        (rs.get ("ExtGState"));
                                if (!extGStateOK (gs)) {
                                    return false;
                                }

                                PdfDictionary xo = (PdfDictionary)
                                    _module.resolveIndirectObject
                                        (rs.get ("XObject"));
                                if (!xObjectsOK (xo)) {
                                    return false;
                                }
                            }
                            
                            // Also check for filters, to make sure
                            // there aren't any forbidden LZW filters.
                            PdfObject filters =
                                dict.get ("Filter");
			    if (!filterOK (filters, true, true)) {
					    return false;
			    }
				
                        }
                    }
                    
                    // Also check page objects for annotations --
                    // in particular, TrapNet annotations.
                    PdfArray annots = ((PageObject) docNode).getAnnotations ();
                    if (annots != null) {
                        Vector annVec = annots.getContent ();
                        for (int i = 0; i < annVec.size (); i++) {
                            PdfDictionary annDict = (PdfDictionary)
                                _module.resolveIndirectObject
                                    ((PdfObject) annVec.elementAt (i));
                            PdfSimpleObject subtypeObj = (PdfSimpleObject) annDict.get ("Subtype");
                            if ("TrapNet".equals (subtypeObj.getStringValue ())) {
                                // FontFauxing must be absent or 0-length
                                PdfArray ff = (PdfArray) annDict.get ("FontFauxing");
                                if (ff != null) {
                                    Vector ffVec = ff.getContent ();
                                    if (ffVec.size() > 0) {
                                        return false;   // a faux pas
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        catch (Exception e) {
            return false;
        }
        return true;   // passed all tests
    }

    /** Checks if a Form xobject is valid.  This overrides the method in
       XProfileBase. */
    protected boolean formObjectOK (PdfDictionary xo)
    {
        // PDF-X/2 elements can't have an OPI key in Form
        // or Image xobjects.
        if (xo.get ("OPI") != null) {
            return false;
        }
        if (xo.get ("Ref") != null) {
            // This is an external reference XObject.
            // All PDF reference XOjbects must have a Page entry.
            if (xo.get ("Page") == null) {
                return false;
            }
            // An X/2 external reference XObject must also have a
            // Metadata entry.
            if (xo.get ("Metadata") == null) {
                return false;
            }
        }
        return true;
    }
}
