/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;

/**
 * A JHElement which signifies a syntactic error.
 *
 * @author Gary McGath
 *
 */
public class JHErrorElement extends JHElement {

    private String _message;
    private String _image;
    private boolean _illFormed;
    
    /**  Constructor.
     *  @param    elements     List of elements representing the document.
     *  @param    message      Message to be reported
     *  @param    image        Textual representation of the offending portion.
     *                         This will be used as the submessage of a generated
     *                         ErrorMessage.
     *  @param    illFormed    <code>true</code> if the error makes the document
     *                         not well-formed, <code>false</code> if it makes
     *                         it only invalid.
     */
    public JHErrorElement (List elements, 
                String message,
                String image, 
                boolean illFormed) {
        super (elements);
        _message = message;
        _image = image;
        _illFormed = illFormed;
    }
    
    
    public String getImage ()
    {
        return _image;
    }

    /** Puts the item's error message into the RepInfo
     *  object, and affects the wellFormed and valid
     *  flags as required.  Once it's determined that
     *  a document is not well-formed, error elements indicating
     *  only invalidity will be ignored.  However, additional
     *  messages that indicate the current level of badness
     *  (not well-formed or invalid) will continue to be reported.*/
    public void reportError (RepInfo info)
    {
        // If we're already not well-formed and the error element
        // is for invalidity, don't bother with it.
        if (info.getWellFormed() == RepInfo.FALSE && !_illFormed) {
            return;
        }
        info.setMessage (new ErrorMessage (_message, _image));
        if (_illFormed) {
            info.setWellFormed (false);
        }
        else {
            info.setValid(false);
        }
    }
}
