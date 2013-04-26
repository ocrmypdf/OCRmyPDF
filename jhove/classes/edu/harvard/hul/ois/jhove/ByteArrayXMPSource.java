/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;

/**
 * Class for providing an InputSource to XMPHandler,
 * with a ByteArrayInputStream as the basis of the
 * InputSource.  This is suitable for a number of modules.
 *
 *  @author Gary McGath
 *
 */
public class ByteArrayXMPSource extends XMPSource {

    /* The underlying ByteArrayInputStream. */
    ByteArrayInputStream _instrm;

    /**
     * Constructor based on ByteArrayInputStream. 
     * 
     * @param instrm   ByteArrayInputStream containing the XMP
     */
    public ByteArrayXMPSource (ByteArrayInputStream instrm)
            throws IOException
    {
        super (new InputStreamReader
               (new XMLWrapperStream (instrm)));
        _instrm = instrm;
        // Prepare for resetting.
        instrm.mark (instrm.available ());
    }


    /**
     * Constructor based on ByteArrayInputStream with encoding. 
     * 
     * @param instrm   ByteArrayInputStream containing the XMP
     */
    public ByteArrayXMPSource (ByteArrayInputStream instrm,
                    String encoding)
            throws IOException
    {
        super (new InputStreamReader
               (new XMLWrapperStream (instrm), encoding));
        _instrm = instrm;
        // Prepare for resetting.
        instrm.mark (instrm.available ());
    }



    /* (non-Javadoc)
     * @see edu.harvard.hul.ois.jhove.XMPSource#resetReader()
     */
    protected void resetReader() {
        _instrm.reset ();
        _reader = new InputStreamReader (_instrm);
    }

}
