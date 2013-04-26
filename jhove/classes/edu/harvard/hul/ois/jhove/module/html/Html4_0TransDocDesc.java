/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.module.HtmlModule;
import java.util.*;

/**
 * This class describes the requirements of an HTML 4.0 Transitional document.
 * 
 * @author Gary McGath
 *
 */
public class Html4_0TransDocDesc extends Html4_0TFDocDesc {

    /* Static, private map of supported tags. 
     * For efficiency, we create a static Map
     * of supported tags just once, then assign that to stSupportedElements
     * in the constructor. */
    private static Map stSupportedElements;

    {
        stSupportedElements = new HashMap (280);
        Html4_0TFDocDesc.classInit4 
            (stSupportedElements, HtmlModule.HTML_4_0_TRANSITIONAL);

    }

    /**
     *  Constructor. 
     *  Most of the initialization work is done in a static code
     *  block rather than in the constructor, so as to minimize
     *  overhead on multiple invocations.
     */
    public Html4_0TransDocDesc ()
    {
        // publish stSupportedElements to superclass
        supportedElements = stSupportedElements;
        init ();
    }

}
