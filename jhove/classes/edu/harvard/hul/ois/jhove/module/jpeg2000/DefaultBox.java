/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;

/**
 *
 * Default class for Boxes that have not yet been implemented.
 * Also used for the "free" box, which by definition contains
 * no information.
 * 
 * @author Gary McGath
 *
 */
public class DefaultBox extends JP2Box {

    /**
     *  Constructor.
     */
    public DefaultBox(RandomAccessFile raf) {
        super(raf);
    }
    
    /**
     *  Constructor with superbox.
     */
    public DefaultBox (RandomAccessFile raf, BoxHolder parent)
    {
        super (raf, parent);
    }

    /* (non-Javadoc)
     * @see edu.harvard.hul.ois.jhove.module.jpeg2000.JP2Box#readBox()
     */
    public boolean readBox() throws IOException {
        skipBox ();
        return true;                
    }

}
