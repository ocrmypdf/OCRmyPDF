/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/


package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.util.*;

/**
 *  PDF profile checker for PDF/X-1 documents.
 *  See ISO Standard 15930-1, "Complete exchange using
 *  CMYK data (PDF/X-1 and PDF/X-1a)"
 */
public final class X1Profile extends XProfileBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private boolean _x1aCompliant;
    
    /** 
     *   Constructor.
     *   Creates an X1Profile object for subsequent testing.
     *
     *   @param  module   The module under which we are checking the profile.
     *
     */
    public X1Profile (PdfModule module) 
    {
        super (module, XProfileBase.PDFX1);
        _profileText = "ISO PDF/X-1";
    }

    /** 
     * Returns <code>true</code> if the document satisfies the profile.
     * X-1a compliance is a superset of the requirements of X-1 compliance
     * (i.e., X-1a compliant documents are a subset of X-1 compliant
     * documents), so we test for X-1a compliance at the same time.
     * The result can subsequently be obtained by calling
     * <code>isX1aCompliant</code>.
     *
     */
    public boolean satisfiesThisProfile ()
    {
        _x1aCompliant = false;    // guilty till proven innocent
        try {
            // First off, there must be an OutputIntents array
            // in the document catalog dictionary.
            PdfDictionary catDict = _module.getCatalogDict ();
            PdfArray intentsArray = (PdfArray) _module.resolveIndirectObject 
                    (catDict.get ("OutputIntents"));
            if (intentsArray == null) {
                return false;
            }

            // Check if PDF-X1/a conformance is asserted
            PdfDictionary docInfo = _module.getDocInfo();
            try {
                PdfSimpleObject conf = (PdfSimpleObject) docInfo.get ("GTS_PDFXConformance");
                String cn = conf.getStringValue ();
                if (cn.startsWith ("PDF/X-1a:")) {
                        _x1aCompliant = true;
                }
            }
            catch (Exception e) { }

            // Next check if the OutputIntents are valid.
            if (!outputIntentsOK (intentsArray)) {
                return false;
            }

            // Do several resource checks.
            if (!resourcesOK ()) {
                return false;
            }
            
            // Check the trailer dictionary.
            if (!trailerDictOK ()) {
                return false;
            }

            // Check specific requirements on the doc info dictionary.
            if (!infoDictOK ("PDF/X-1")) {
                return false;
            }
            
            // Check that an acceptable form of encryption (or none) is used.
            if (!encryptionOK ()) {
                return false;
            }
            
            // Check that bounding boxes are present as required.
            // MediaBox is required.
            if (!bboxOK (true)) {
                return false;
            }
            
            // If the document contains Actions, it's non-conformant
            if (_module.getActionsExist ()) {
                return false;
            }

            // Now for specific X1-a tests
            // Encryption dictionary is not allowed.
            if (_module.getEncryptionDict () != null) {
                _x1aCompliant = false;
            }

            // Check that ViewerPreferences meet certain restrictions
            // if any BleedBoxes are present.
            if (!checkPrefsAgainstBleedBox ()) {
                _x1aCompliant = false;
            }

        }
        catch (Exception e) {
            // Any otherwise uncaught exception means nonconformance
            return false;
        }
        return true; 
    }
    
    /**
     * Returns the result of X-1a compliance testing which was performed in
     *  the course of <code>satisfiesThisProfile</code>. If
     *  <code>satisfiesThisProfile</code> hasn't been called, returns 
     *  <code>false</code>.
     */
    public boolean isX1aCompliant ()
    {
        return _x1aCompliant;
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
                
                    // Check color spaces.
                    PdfDictionary cs = (PdfDictionary)
                        _module.resolveIndirectObject
                            (rsrc.get ("ColorSpace"));
                    if (!colorSpaceOK (cs)) {
                        return false;
                    }

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
                                PdfDictionary cs = (PdfDictionary)
                                    _module.resolveIndirectObject
                                        (rs.get ("ColorSpace"));
                                if (!colorSpaceOK (cs)) {
                                    return false;
                                }

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
                            // Also check for filters, for X1-a restrictions.
                            PdfObject filters =
                                dict.get ("Filter");
                                                        if (!filter1AOK (filters)) {
                                                                _x1aCompliant = false;
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
                                annVec.elementAt (i);
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
                                
                                // Check Appearance dict for TrapNet annotation
                                PdfDictionary appDict = (PdfDictionary) 
                                    annDict.get ("AP");
                                if (appDict != null) {
                                    PdfDictionary normalDict = (PdfDictionary) appDict.get ("N");
                                    if (normalDict != null) {
                                        PdfSimpleObject pcm = 
                                            (PdfSimpleObject) normalDict.get ("PCM");
                                        if (!"DeviceCMYK".equals (pcm.getStringValue ())) {
                                            return false;
                                        }
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


    /* Check if a color space dictionary is conformant */
    private boolean colorSpaceOK (PdfDictionary cs)
    {
        // If it's null, that's fine.
        if (cs == null) {
            return true;
        }
        // Walk through the color space dictionary,
        // checking Separation and DeviceN resources
        Iterator iter = cs.iterator ();
        while (iter.hasNext ()) {
            PdfObject res = (PdfObject) iter.next ();
            if (res instanceof PdfArray) {
                Vector resv = ((PdfArray) res).getContent ();
                PdfSimpleObject snameobj = (PdfSimpleObject) resv.elementAt (0);
                String sname = snameobj.getStringValue ();
                if ("Separation".equals (sname) || "DeviceN".equals (sname)) {
                    PdfSimpleObject altSpaceObj = (PdfSimpleObject) resv.elementAt (2);
                    String altSpace = altSpaceObj.getStringValue ();
                    if (! ("DeviceGray".equals (altSpace) || 
                            "DeviceCMYK".equals (altSpace))) {
                        return false;
                    }
                }
                if ("Indexed".equals (sname) ||
                    "Pattern".equals (sname)) {
                    // Indexed and pattern color spaces must have a
                    // base colorspace of DeviceCMYK, DeviceGray,
                    // DeviceN, or Separation.
                    PdfSimpleObject baseObj = (PdfSimpleObject)
                        resv.elementAt (1);
                    String base = baseObj.getStringValue ();
                    if (! ("DeviceCMYK".equals (base) ||
                           "DeviceGray".equals (base) ||
                           "DeviceN".equals (base) ||
                           "Separation".equals (base))) {
                        return false;
                    }
                }
            }
        }
        return true;   // passed all tests
    }



    /* Checks a single XObject. */
    protected boolean xObjectOK (PdfDictionary xo) 
    {
        if (xo == null) {
            // no XObject means no problem
            return true;
        }
        // Do common tests
        if (!super.xObjectOK (xo)) {
            return false;
        }
        // Tests specific to X/1
        try {
                        
            PdfDictionary opi = (PdfDictionary) xo.get ("OPI");
            if (opi == null) {
                // If it isn't an OPI object, we don't care
                return true;
            }
            _x1aCompliant = false;      // OPI objects aren't allowed in X-1a
            // get the version 2.0 dictionary.  If it has only
            // a 1.3 dictionary, X1 apparently is indifferent.
            PdfDictionary opi20 = (PdfDictionary) 
                _module.resolveIndirectObject (opi.get ("2.0"));
            if (opi20 == null) {
                return true;
            }
            // Now what we came for.  The Inks entry is optional,
            // but if present, must be full_color, registration,
            // or an array containing monochrome as its first value.
            // If monochrome, all ink names must be CMYK colorants.
            // (Unfortunately, the spec doesn't tell us exactly
            // what these names should be: C? Cyan? cyan?)
            PdfObject inks = _module.resolveIndirectObject
                (opi20.get ("Inks"));
            if (inks == null) {
                return true;
            }
            if (inks instanceof PdfSimpleObject) {
                String inkname = ((PdfSimpleObject) inks).getStringValue ();
                if (!("full_color".equals (inkname) ||
                      "registration".equals (inkname))) {
                    return false;
                }
            }
            else if (inks instanceof PdfArray) {
                Vector inkvec = ((PdfArray) inks).getContent ();
                PdfSimpleObject inkobj = (PdfSimpleObject)
                        inkvec.elementAt (0);
                if (!("monochrome".equals (inkobj.getStringValue ()))) {
                    return false;
                } 
            }

            // Next, the referenced file must be included as
            // an EmbeddedFile.  A file specification can be either
            // a dictionary or a string.  I don't understand what's
            // being said on page 124.  EmbeddedFiles maps name strings
            // to embedded file streams; but exactly what are the name
            // strings it uses?
            
            PdfObject fileObj = 
                _module.resolveIndirectObject (opi20.get ("F"));
            NameTreeNode embFiles = _module.getEmbeddedFiles ();
            // Leave this for now, till I can make some sense of it.
        }
        catch (Exception e) {
            return false;
        }
        return true;    // passed all tests
    }
    
    


    private boolean encryptionOK ()
    {
        PdfDictionary encryptDict = _module.getEncryptionDict ();
        if (encryptDict == null) {
            return true;    //no encryption is good encryption
        }
        try {
            PdfSimpleObject filter = (PdfSimpleObject) encryptDict.get ("Filter");
            if (!"Standard".equals (filter.getStringValue ())) {
                return false;
            }
            
            // the permissions must include bit 3 (printing).  In PDF's
            // notation, bit 1 is the low-order bit.
            PdfSimpleObject perm = (PdfSimpleObject) encryptDict.get ("P");
            if (perm == null) {
                // P is required with standard encryption
                return false;
            }
            if ((perm.getIntValue () & 4) == 0) {
                return false;
            }
        }
        catch (Exception e) {
            return false;
        }
        return true;
    }


    /* Check for LZW and JBIG2 filters, which are forbidden in X/1a.
       This does not affect X/1 compliance. */
    private boolean filter1AOK (PdfObject filters)
    {
        return !hasFilters (filters, 
               new String [] { "LZWDecode", "JBIG2Decode" } );
    }

    /** Checks if a Form xobject is valid.  This overrides the method in
       XProfileBase. */
    protected boolean formObjectOK (PdfDictionary xo)
    {
        // PDF-X/1-a elements can't have a Ref key in the
        // Form dictionary.
        if (xo.get ("Ref") != null) {
            // This is an external reference XObject.
            _x1aCompliant = false;
        }
        // Form objects aren't restricted in X/1
        return true;
    }
}
