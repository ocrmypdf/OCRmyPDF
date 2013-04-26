/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.PdfModule;

/**
 *  PDF profile checker for PDF/A-1 documents, Level A.
 *  See ISO 19005-1:2005(E), "Document Imaging Applications
 *  Application Issues".
 * 
 *  This profile checker is completely dependent on AProfile.
 *  It simply queries an instance of AProfile for Level A compliance.
 *
 * @author Gary McGath
 *
 */
public class AProfileLevelA extends PdfProfile {

    /* AProfile to which this profile is linked. */
    private AProfile _aProfile;

    /** 
     *   Constructor.
     *   Creates an AProfileLevelA object for subsequent testing.
     *
     *   @param  module   The module under which we are checking the profile.
     *
     */
    public AProfileLevelA(PdfModule module) {
        super (module);
        _profileText = "ISO PDF/A-1, Level A";
    }

    /** 
     * Returns <code>true</code> if the document satisfies the profile
     * at Level A.  This returns a meaningful result only if 
     * <code>satisfiesThisProfile()</code> has previously
     * been called on the profile assigned by <code>setAProfile</code>.
     *
     */
    public boolean satisfiesThisProfile() {
        return _aProfile.satisfiesLevelA();
    }

    /**
     *  Calling setAProfile links this AProfile to a TaggedProfile.
     *  This class gets all its information from the linked AProfile,
     *  so calling this is mandatory.
     */
    public void setAProfile (AProfile tpr) 
    {
        _aProfile = tpr;
    }

}
