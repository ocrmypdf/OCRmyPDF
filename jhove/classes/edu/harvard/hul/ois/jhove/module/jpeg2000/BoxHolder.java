/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;
import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * A BoxHolder is a container for JPEG 2000 boxes.   
 *
 * @author Gary McGath
 *
 */
public class BoxHolder implements Iterator<Object> {

    protected Jpeg2000Module _module;
    protected JP2Box _parentBox;
    protected RandomAccessFile _raf;
    protected DataInputStream _dstrm;
    protected BoxHeader _boxHeader;
    protected RepInfo _repInfo;
    protected long bytesLeft;
    protected long filePos;
    protected boolean hasBoxes;
    private BinaryFilterBox binaryFilterBox;

    /**
     *  Constructor.
     */
    public BoxHolder(RandomAccessFile raf) {
        hasBoxes = false;    // subclass which is a superbox should override
        _raf = raf;
        binaryFilterBox = null;
        try {
            filePos = raf.getFilePointer ();
        }
        catch (IOException e) {}
        
        //makeInputStream ();
    }
    


    /** Returns the file position.
     * In practice, this means returning the beginning of the Box. */
    protected long getFilePos () 
    {
        // ghaaaaaa ... Maybe the best I can do is report
        // the start of the box in the file.  the module's
        // file position is useless.  Of course, for a Binary
        // Filter box, even getting the start of the box in
        // the file will be tricky.
        return filePos;
    }


    /**
     * Checks if any more subboxes are available.
     * This class doesn't fully conform to the Iterator interface,
     * as there are some cases where the lack of more boxes
     * won't be detected till an EOF is encounterd.  So callers
     * should call <code>hasNext</code> to avoid reading overruns, and then
     * test the value returned by <code>next</code> for nullity.
     */
    
    public boolean hasNext ()
    {
        return (hasBoxes && bytesLeft >= 8);
    }
    
    
    /* This should return the next Box, if any. */
    public Object next ()
    {
        if (!hasBoxes) {
            return null;
        }
        
        try {
            BoxHeader subhdr;
            JP2Box nextBox;
            // If we've encountered a BinaryFilterBox, it feeds
            // us boxes till it's exhausted.  When it has no
            // more boxes, we set it to null to indicate we
            // resume reading ordinary boxes.
            if (binaryFilterBox != null) {
                if (binaryFilterBox.hasNext ()) {
                    nextBox = (JP2Box) binaryFilterBox.next ();
                }
                else {
                    binaryFilterBox = null;
                    // Fall through into normal reading
                }
            }
            if (bytesLeft < 8) {
                return null;
            }
            subhdr = new BoxHeader (_module, _dstrm);
            subhdr.readHeader ();
            bytesLeft -= subhdr.getLength ();
            String hType = subhdr.getType ();
            if ("bfil".equals (hType)) {
                binaryFilterBox = new BinaryFilterBox 
                        (_raf, (this instanceof JP2Box) ? (JP2Box) this : null);
                // If I can make the following magic actually
                // work correctly, then I'm starting to get somewhere.
                
                if (binaryFilterBox.hasNext ()) {
                    return binaryFilterBox.next ();
                }
                else {
                    // The "else" is a BinaryFilterBox with no content.
                    // This seems unlikely, but assume it's legal and
                    // fall through to the next box.
                    subhdr.readHeader ();
                    hType = subhdr.getType ();
                }
            }
            if ("cref".equals (hType)) {
                // A Cross Reference Box is replaced by another box,
                // which is found in the DataInputStream it produces.
                CrossRefBox xrefBox = new CrossRefBox (_raf, 
                        (this instanceof JP2Box) ? (JP2Box) this : null);
                if (!xrefBox.readBox ()) {
                    return null;
                }
                BoxHeader xrefhdr = 
                    new BoxHeader (_module, xrefBox.getCrossRefStream());
                xrefhdr.readHeader ();
                nextBox = JP2Box.boxMaker (xrefhdr.getType (),
                        (this instanceof JP2Box) ? (JP2Box) this : null);
                return nextBox;
            }
            else {
                nextBox = JP2Box.boxMaker(hType, this);

                nextBox.setModule(_module);
                nextBox.setRepInfo(_repInfo);
                nextBox.setRandomAccessFile(_raf);
                nextBox.setDataInputStream(_dstrm);
                nextBox.setBoxHeader (subhdr);
                return nextBox;
            }
        }
        catch (IOException e) {
            // Probably I should be reporting an error here
            return null;
        }
    }
    
    /** Always throws UnsupportedOperationException. */
    public void remove () throws UnsupportedOperationException
    {
        throw new UnsupportedOperationException();
    }


    /** Utility error reporting function for a subbox overrunning
     *  its superbox. 
     *  Sets the RepInfo's wellFormed flag to <code>false</code>.
     */
    protected void superboxOverrun ()
    {
        _repInfo.setMessage (new ErrorMessage 
            ("Size of contained Box overruns " + getSelfPropName (), 
             _module.getFilePos ()));
        _repInfo.setWellFormed (false);
    }


    /** Utility error reporting function for a subbox underrunning
     *  its superbox. 
     *  Sets the RepInfo's wellFormed flag to <code>false</code>.
     */
    protected void superboxUnderrun ()
    {
        _repInfo.setMessage (new ErrorMessage 
            ("Size of contained Boxes underruns " + getSelfPropName (), 
             _module.getFilePos ()));
        _repInfo.setWellFormed (false);
    }



    /** Returns the name of the BoxHolder. All subclasses should
     *  override this. */
    protected String getSelfPropName ()
    {
        return "";
    }
}
