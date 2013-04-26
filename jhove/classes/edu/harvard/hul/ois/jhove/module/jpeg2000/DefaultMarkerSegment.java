/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;

/**
 * This class is used to handle any unrecognized or unimplemented
 * marker segment in a codestream.
 * 
 * @author Gary McGath
 *
 * To change the template for this generated type comment go to
 * Window&gt;Preferences&gt;Java&gt;Code Generation&gt;Code and Comments
 */
public class DefaultMarkerSegment extends MarkerSegment {

    /**
     * 
     */
    public DefaultMarkerSegment() {
        super();
    }


    /**
     * Processes the marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment; for a marker,
     *  this number will always be 0.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         For a Marker, this number will always be 0.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     */
    protected boolean process (int bytesToEat) throws IOException
    {
        _module.skipBytes (_dstream, bytesToEat, _module);
        return true;
    }
}
