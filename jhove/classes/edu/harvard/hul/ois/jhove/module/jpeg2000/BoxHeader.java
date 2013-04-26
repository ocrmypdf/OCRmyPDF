/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;
import java.io.*;

/**
 *  Encapsulation of a JPEG 2000 box header.
 *
 * @author Gary McGath
 *
 */
public class BoxHeader {
    
    private long _length;
    private String _type;
    private Jpeg2000Module _module;
    private DataInputStream _dstream;
    private long _headerLength;
    
    /**
     *  Constructor.
     * 
     *  @param mod         The Module which uses this object
     *  @param dstrm       The DataInputStream reading data for the Module
     */
    public BoxHeader (Jpeg2000Module mod, DataInputStream dstrm)
    {
        _module = mod;
        _dstream = dstrm;   
    }
    
    /**
     *  Reads 8 bytes from the beginning of the box and parses 
     *  out the box length and type.
     */
    public void readHeader () throws IOException
    {
        _length = ModuleBase.readUnsignedInt(_dstream, true, _module);
        _type = _module.read4Chars (_dstream);
        
        // If the length field is 1, there is an 8-byte extended
        // length field.
        if (_length == 1) {
            _length = ModuleBase.readSignedLong(_dstream, true, _module);
            _headerLength = 16;
        }
        else {
            _headerLength = 8;
        }
    }
    
    
    /**
     *  Returns the box length, which includes the length and 
     *  type fields.  If the value returned is 0, the length
     *  of the box is all the remaining data to the end of the file.
     */
    public long getLength ()
    {
        return _length;
    }
    
    
    /**
     *  Returns the length of the header.
     *  This number is equal to the number
     *  of bytes that have been read by <code>readHeader()</code>.
     */
    public long getHeaderLength ()
    {
        return _headerLength;
    }
    
    /**
     *  Returns the number of bytes in the Box, not including
     *  the header.  This is equivalent to 
     *  <code>getLength() - getHeaderLength()</code>.
     *  If <code>getLength()</code> would return 0, this value is
     *  meaningless.
     */
    public long getDataLength ()
    {
        return _length - _headerLength;
    }

    /**
     *  Returns the box type.
     */
    public String getType ()
    {
        return _type;
    }
}
