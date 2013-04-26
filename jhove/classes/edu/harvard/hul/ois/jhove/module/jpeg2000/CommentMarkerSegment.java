/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.IOException;
import edu.harvard.hul.ois.jhove.*;

/**
 * Class for the COM (Comment) marker segment.
 * This comes either in the main header or
 * after an SOT. 
 *
 * @author Gary McGath
 *
 */
public class CommentMarkerSegment extends MarkerSegment {

    /**
     * Constructor.
     */
    public CommentMarkerSegment() {
        super();
    }

    /** Process the marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     * 
     *  @return                <code>true</code> if segment is well-formed,
     *                         <code>false</code> otherwise.
     */
    protected boolean process(int bytesToEat) throws IOException {
        MainOrTile cs = getMainOrTile ();
        int rcom = _module.readUnsignedShort (_dstream);
        Property prop;
        byte[] byteBuf = new byte[bytesToEat - 2];
        ModuleBase.readByteBuf (_dstream, byteBuf, _module);
        switch (rcom) {
            case 0:
            // Binary comment
            prop = new Property ("Comment",
                    PropertyType.BYTE,
                    PropertyArity.ARRAY,
                    byteBuf);
            break;
            
            case 1:
            // ISO Latin comment
            prop = new Property ("Comment",
                    PropertyType.STRING,
                    new String (byteBuf));
            break;
            
            default:
            _repInfo.setMessage( (new ErrorMessage 
                    ("Unrecognized comment type")));
            return false;        // other values are reserved
        }
        cs.addComment (prop);
        return true;
    }

}
