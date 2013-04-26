/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.module.HtmlModule;
import java.util.*;

/**
 * This class describes the requirements of an HTML 4.01 Frameset document.
 *
 * @author Gary McGath
 *
 */
public class Html4_01FrameDocDesc extends Html4_01TFDocDesc {

    /* Static, private map of supported tags. 
     * For efficiency, we create a static Map
     * of supported tags just once, then assign that to stSupportedElements
     * in the constructor. */
    private static Map stSupportedElements;

    {
        stSupportedElements = new HashMap (280);
        Html4_01TFDocDesc.classInit4 
            (stSupportedElements, HtmlModule.HTML_4_01_FRAMESET);
    }

    /** Constructor. */
    public Html4_01FrameDocDesc ()
    {
        // publish stSupportedElements to superclass
        supportedElements = stSupportedElements;
        init ();
    }

}
