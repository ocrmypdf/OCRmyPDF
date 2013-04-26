
package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;
import java.util.*;

/**
 *  Abstract base class for PDF profilers of the PDF/X family.
 *  See ISO Standard 15930-1, "Complete exchange using
 *  CMYK data (PDF/X-1 and PDF/X-1a)"
 */
public abstract class XProfileBase extends PdfProfile
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /** Enumerated values for PDF-X type */
    public static int PDFX1 = 1,
        PDFX1A = 2,
        PDFX2 = 3,
        PDFX3 = 4;
    
    /** PDF-X type used by the subclass. */
    protected int _xType;
    
    /** Set to <code>true</code> if a BleedBox is found. */
    protected boolean _bleedBoxPresent;

    /** 
     *   Constructor.
     *   Creates an X1Profile object for subsequent testing.
     *
     *   @param  module   The module under which we are checking the profile.
     *   @param  xType    The type of PDF/X profile being checked
     *
     */
    public XProfileBase (PdfModule module, int xType) 
    {
        super (module);
	_bleedBoxPresent = false;
        _xType = xType;
    }


    /** Checks if the entries which are required in the document information
     *  dictionary by PDF-X/1 and X/3 are there.
     *  These entries are optional under the PDF specification,
     *  so they must be checked here.  
     */
    protected boolean infoDictOK (String xVersion)
    {
        PdfDictionary docInfo = _module.getDocInfo();
        try {
            PdfSimpleObject trapped = 
                (PdfSimpleObject) docInfo.get ("Trapped");
            PdfSimpleObject xvers = (PdfSimpleObject) docInfo.get ("GTS_PDFXVersion");
            if (docInfo.get ("CreationDate") == null ||
                xvers == null ||
                docInfo.get ("ModDate") == null ||
                docInfo.get ("Title") == null ||
                trapped == null) {
                return false;
            }
            
            // The value of Trapped must be True or False.
            // Unknown (and other random values) is prohibited.
            String trappedVal = trapped.getStringValue ();
            if (!("True".equals (trappedVal) ||
                  "False".equals (trappedVal))) {
                return false;
            }
            
            // The value of GTS_PDFXVersion must begin with the value of xVersion.
            String vers = xvers.getStringValue ();
            if (!vers.startsWith (xVersion)) {
                return false;
            }
        }
        catch (Exception e) {
            return false;
        }
        return true;
    }

    /** Returns true if a BleedBox has been detected. */
    protected boolean isBleedBoxPresent ()
    {
	return _bleedBoxPresent;
    }


    /** Checks if the OutputIntents of this document conform
     *  to profile requirements. 
     *  There must be exactly one entry in the dictionary
     *  which has a subtype of GTS_PDFX. 
     */
    protected boolean outputIntentsOK (PdfArray intents) 
    {
        Vector intVec = intents.getContent ();
        int matchCount = 0;
        try {
            for (int i = 0; i < intVec.size (); i++) {
                PdfDictionary intent = 
                        (PdfDictionary) _module.resolveIndirectObject
                            ((PdfObject)intVec.elementAt (i));
                PdfSimpleObject sval = (PdfSimpleObject) 
                    _module.resolveIndirectObject (intent.get ("S"));
                if (sval != null) {
                    String subtype = sval.getStringValue ();
                    if ("GTS_PDFX".equals (subtype)) {
                        ++matchCount;  // there can be only one

                        // It must have an OutputConditionIdentifier
                        PdfSimpleObject outcond = (PdfSimpleObject)
                            _module.resolveIndirectObject
                              (intent.get("OutputConditionIdentifier"));
                        if (outcond == null)
                            return false;

                        // X1 and 1a only: There must be either a RegistryName entry
                        // or a DestOutputProfile 
                        // entry.  Having them both is OK.
                        if (_xType == PDFX1) {
                            PdfSimpleObject regName = (PdfSimpleObject)
                                _module.resolveIndirectObject
                                    (intent.get ("RegistryName"));
                            PdfStream dop = (PdfStream)
                                _module.resolveIndirectObject
                                    (intent.get ("DestOutputProfile"));
                            if (regName == null && dop == null) {
                                return false;
                            }
                            /* This is WRONG for X-1 and X-1a.  Was it
                             * supposed to go somewhere else?? */
//                            if (dop != null) {
//                                // If present, the DestOutputProfile
//                                // must have an AtoB1Tag entry.
//                                PdfObject ab1 = dop.getDict().get ("AtoB1Tag");
//                                if (ab1 == null) {
//                                    return false;
//                                }
//                            }
                        }
                    }
                }
            }
            return (matchCount == 1);
        }
        catch (Exception e) {
            return false;
        }
    }

    /** Checks profile requirements on the trailer dictionary.
     */
    protected boolean trailerDictOK ()
    {
        PdfDictionary trailerDict = _module.getTrailerDict ();
        if (trailerDict == null) {
            return false;       // Something is SERIOUSLY wrong if this happens
        }
        // ID entry is required
        if (trailerDict.get ("ID") == null) {
            return false;
        }
        
        return true;
    }

    /** Checks if the ExtGState resource meets profile requirements.
     *  It may not have TR, TR2, or HTP entries.
     */
    protected boolean extGStateOK (PdfDictionary gs) 
    {
        if (gs == null) {
            // no object means no problem
            return true;
        }
        try {
            PdfObject tr = gs.get ("TR");
            PdfObject tr2 = gs.get ("TR2");
            PdfObject htp = gs.get ("HTP");
            if (tr != null || tr2 != null || htp != null) {
                return false;
            }
            
            // If there is a halftone dictionary, it must meet
            // certain requirements
            PdfObject ht = gs.get ("HT");
            if (ht instanceof PdfDictionary) {
                // HalftoneType must be 1 or 5
                PdfDictionary htd = (PdfDictionary) ht;
                PdfSimpleObject htType = (PdfSimpleObject) htd.get ("HalftoneType");
                int htTypeVal = htType.getIntValue ();
                if (htTypeVal != 1 && htTypeVal != 5) {
                    return false;
                }
            }
            
            // The HalftoneName entry ist verboten
            if (gs.get ("HalftoneName") != null) {
                return false;
            }

	    // The SMask entry is forbidden in X-1a and X-2
	    // unless its value is "None"
	    if (_xType == PDFX1A || _xType == PDFX2) {
		PdfSimpleObject smask = (PdfSimpleObject) gs.get ("SMask");
		if (smask != null) {
		    if (!"None".equals (smask.getStringValue ())) {
			return false;
		    }
		}

		// The values of BM, CA, and ca are restricted if
		// these keys are present
		PdfSimpleObject blendMode =
		    (PdfSimpleObject) gs.get ("BM");
		if (blendMode != null) {
		    String bmVal = blendMode.getStringValue ();
		    if (!"Normal".equals (bmVal) &&
			!"Compatible".equals (bmVal)) {
			return false;
		    }
		}
		PdfSimpleObject ca = (PdfSimpleObject) gs.get ("CA");
		double caVal;
		if (ca != null) {
		    caVal = ca.getDoubleValue ();
		    if (caVal != 1.0) {
			return false;
		    }
		}
		ca = (PdfSimpleObject) gs.get ("ca");
		if (ca != null) {
		    caVal = ca.getDoubleValue ();
		    if (caVal != 1.0) {
			return false;
		    }
		}
	    }
        }
        catch (Exception e) {
            return false;
        }
        return true;   // passed all tests
    }


    /** 
     *   Checks a single XObject for xObjectsOK.  Calls imageObjectOK
     *   and formObjectOK for profile-specific functionality.
     */
    protected boolean xObjectOK (PdfDictionary xo) 
    {
        if (xo == null) {
            // no XObject means no problem
            return true;
        }
        try {
            // PostScript XObjects aren't allowed.
            // Image XObjects must meet certain tests.
            PdfSimpleObject subtype = (PdfSimpleObject) xo.get ("Subtype");
            if (subtype != null) {
                String subtypeVal = subtype.getStringValue ();
                if ("PS".equals (subtypeVal)) {
                    // PS XObjects aren't allowed in any X format.
                    return false;
                }
                if ("Image".equals (subtypeVal)) {
                    if (!imageObjectOK (xo)) {
                        return false;   
                    }
                }
                if ("Form".equals (subtypeVal)) {
                    if (!formObjectOK (xo)) {
                        return false;   
                    }
                }
            }
        }
        catch (Exception e) {
            return false;        
        }
        return true;
    }


    /** Checks if a single image XObject fits the profile */
    protected boolean imageObjectOK (PdfDictionary xo) 
    {
        try {
            PdfArray alternates = (PdfArray) xo.get ("Alternates");
            if (alternates == null) {
                // No alternates means we're fine
                return true;
            }
            Vector altVec = alternates.getContent ();
            for (int i = 0; i < altVec.size (); i++) {
                PdfDictionary alt = (PdfDictionary) altVec.elementAt (i);
                // No alternate may have DefaultForPrinting = true
                PdfSimpleObject dfp = 
                    (PdfSimpleObject) alt.get ("DefaultForPrinting");
                if (dfp.isTrue ()) {
                    return false;
                }
            }
            if (_xType == PDFX2) {
                 // PDF-X/2 elements can't have an OPI key in Form
                 // or Image xobjects.
                 if (xo.get ("OPI") != null) {
                    return false;
                 }
            }
	    if (_xType == PDFX1A || _xType == PDFX2) {
		// SMask is restricted in PDFX-1/a and X-2
		PdfSimpleObject smask = (PdfSimpleObject) xo.get ("SMask");
		if (smask != null) {
		    if (!"None".equals (smask.getStringValue ())) {
			return false;
		    }
		}
	    }
        }
        catch (Exception e) {
            return false;
        }
        return true;     // passed all tests
    }

    /** Checks the conformance of a form XObject.  
     *  Does nothing; must be overridden if there are
     *  conditions on such forms. 
     */
    protected boolean formObjectOK (PdfDictionary fo)
    {
        return true;
    }



    /** Checks all the page objects for bounding boxes.  If requireMediaBox
     *  is true, each page has to include 
     *  or inherit a MediaBox. 
     *  Each page must include one but not both of a TrimBox and
     *  an ArtBox. 
     */
    protected boolean bboxOK (boolean requireMediaBox)
    {
        PageTreeNode pgtree = _module.getDocumentTree ();
        try {
            pgtree.startWalk ();
            PageObject pageObject;
            for (;;) {
                pageObject = pgtree.nextPageObject ();
                if (pageObject == null) {
                    break;
                }
                if (requireMediaBox) {
                    // Check for a MediaBox.  If there isn't one here, one
                    // of its ancestors must have one.
                    PdfArray mbox = pageObject.getMediaBox ();
                    if (mbox == null) {
                        return false;
                    }
                }
                
                // Check for TrimBox or ArtBox.  Apply the Highlander rule.
                PdfArray tbox = pageObject.getTrimBox ();
                PdfArray abox = pageObject.getArtBox ();
                if (tbox == null && abox == null) {
                    return false;
                }
                if (tbox != null && abox != null) {
                    return false;
                }
		
		// BleedBox may be in conflict with other
		// features.  Record here whether any
		// BleedBox is found.
		if (pageObject.getBleedBox () != null) {
		    _bleedBoxPresent = true;
		}
            }
        }
        catch (Exception e) {
            return false;
        }
        return true;    // passed all tests
    }


    /**
     * Checks ViewerPreferences dictionary against MediaBox
     * and BleedBox.
     * In PDF-X1/a and X2, if a BleedBox is present and
     * if the ViewerPreferences dictionary contains the
     * ViewClip, PrintArea or PrintClip keys, each of those
     * keys present shall have the value MediaBox or BleedBox.
     * This must be called after bboxOK has checked if any
     * BleedBoxes are found.
     */
    protected boolean checkPrefsAgainstBleedBox ()
    {
	if (!_bleedBoxPresent) {
	    // No bleed box, the test isn't necessary.
	    return true;
	}
	PdfDictionary viewPrefDict = _module.getViewPrefDict ();
	if (viewPrefDict == null) {
	    // No viewer prefs, passes the test trivially.
	    return true;
	}
	try {
	    PdfSimpleObject[] areas = new PdfSimpleObject[3];
	    areas[0] = (PdfSimpleObject) viewPrefDict.get ("ViewArea");
	    areas[1] = (PdfSimpleObject) viewPrefDict.get ("ViewClip");
	    areas[2] = (PdfSimpleObject) viewPrefDict.get ("PrintArea");

	    for (int i = 0; i < 3; i++) {
		if (areas[i] != null) {
		    String s = areas[i].getStringValue ();
		    if (!"MediaBox".equals (s) &&
			    !"BleedBox".equals (s)) {
			return false;
		    }
		}
	    }
	}
	catch (Exception e) {
	    return false;
	}
	return true;
    }
    /**
     * Checks for forbidden filters in a Filters dictionary. 
     */
    protected boolean filterOK (PdfObject filters, 
            boolean forbidLZW, 
            boolean forbidJBIG2)
    {
        String filterName;
        try {
            if (filters == null) {
                return true;
            }
            if (filters instanceof PdfSimpleObject) {
                // Name of just one filter
                filterName = ((PdfSimpleObject) filters).getStringValue ();
                if ("LZWDecode".equals (filterName)) {
                    return false;
                }
            }
            else {
                // If it's not a name, it must be an array
                Vector filterVec = ((PdfArray) filters).getContent ();
                for (int i = 0; i < filterVec.size (); i++) {
                    PdfSimpleObject filter = 
                        (PdfSimpleObject) filterVec.elementAt (i);
                    filterName = filter.getStringValue ();
                    if (forbidLZW && "LZWDecode".equals (filterName)) {
                        return false;
                    }
                    if (forbidJBIG2 && "JBIG2Decode".equals (filterName)) {
                        return false;
                    }
                }
            }
        }
        catch (Exception e) {
            return false;   
        }
        return true;   // passed all tests
    }

}
