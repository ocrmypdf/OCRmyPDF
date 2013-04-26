
package edu.harvard.hul.ois.jhove.module.pdf;

import edu.harvard.hul.ois.jhove.module.*;

/**
 *  PDF profile checker for PDF/X-1a documents.
 *  See ISO Standard 15930-1, "Complete exchange using
 *  CMYK data (PDF/X-1 and PDF/X-1a)"
 *  
 *  This module depends on the PDF/X-1 profiler, since the PDF/X-1 specification
 *  is PDF/X-1 plus a few additional restrictions.  
 */
public final class X1aProfile extends XProfileBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private X1Profile _x1Profile;

    /** 
     *   Constructor.
     *   Creates an X1aProfile object for subsequent testing.
     *
     *   @param  module   The module under which we are checking the profile.
     *
     */
    public X1aProfile (PdfModule module) 
    {
        super (module, XProfileBase.PDFX1A);
        _profileText = "ISO PDF/X-1a";
    }
    
    /**
     *  Calling setX1Profile links this X1aProfiler to an X1Profiler.
     *  
     */
    public void setX1Profile (X1Profile x1) 
    {
        _x1Profile = x1;
    }

    /** 
     * Returns <code>true</code> if the document satisfies the profile.
     * If <code>setX1Profile</code> hasn't been called,
     * creates a temporary X1Profile and tests against that profile first.
     * Either way, <code>X1Profile.isX1aCompliant</code> is then called
     * to determine the X-1/a compliance status.
     *
     */
    public boolean satisfiesThisProfile ()
    {
        if (_x1Profile != null) {
            // If there is a linked X1Profile, we save time by checking if
            // it passed or not.
            if (!_x1Profile.isAlreadyOK ()) {
                return false;
            }
        }
        else {
            // If there isn't a linked X1Profile, create one
            // and check it.
            _x1Profile = new X1Profile (_module);
            if (!_x1Profile.satisfiesProfile (_raf, _parser)) {
                return false;
            }
        }

        return _x1Profile.isX1aCompliant ();
    }

}
