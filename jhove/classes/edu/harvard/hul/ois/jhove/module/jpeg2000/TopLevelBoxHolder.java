/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;
import java.io.*;

/**
 * A subclass of BoxHolder specifically for getting top-level
 * boxes in a JPEG 2000 file.
 * 
 * 
 * @author Gary McGath
 *
 */
public class TopLevelBoxHolder extends BoxHolder {

    private boolean eof;
    
    /**
     * @param raf
     */
    public TopLevelBoxHolder(Jpeg2000Module module,
            RandomAccessFile raf, 
            RepInfo info,
            DataInputStream dstream) 
    {
        super(raf);
        _module = module;
        _dstrm = dstream;
        _repInfo = info;
        eof = false;
        hasBoxes = true;
        bytesLeft = Long.MAX_VALUE;
    }

    /** Returns a name for use in messages. */
    protected String getSelfPropName ()
    {
        return "Top Level";
    }

    public boolean hasNext ()
    {
        return (!eof);
    }

}
