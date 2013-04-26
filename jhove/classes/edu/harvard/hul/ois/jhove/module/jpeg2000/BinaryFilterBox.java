/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.zip.InflaterInputStream;
import edu.harvard.hul.ois.jhove.*;

/**
 *  Binary Filter box (JPX).
 *  See ISO/IEC FCD15444-2: 2000, L.9.14
 * 
 *  A Binary Filter Box can subsume any number of
 *  other boxes, which will look to the module as if they
 *  simply replace this box.  BoxHolder makes a special case
 *  of BinaryFilterBoxes, calling the getBoxStream method to
 *  extract the subsumed boxes.
 * 
 *  Only Deflate coding, not DES, is supported.
 * 
 *  It is assumed that a BinaryFilterBox is never
 *  encoded inside another BinaryFilterBox.  
 * 
 *  This is untested code, due to lack of sample files;
 *  please report any bugs found to HUL/OIS.
 * 
 * @author Gary McGath
 *
 */
public class BinaryFilterBox extends JP2Box {

    private final static int[] gzipuuid =
        { 0XEC, 0X34, 0X0B, 0X04, 0X74, 0XC5, 0X11, 0XD4,
          0XA7, 0X29, 0X87, 0X9E, 0XA3, 0X54, 0X8F, 0X0E };
          
    private DataInputStream boxStream;
    private JP2Box _realParent;
    
    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     *                    or TopLevelBoxHolder
     */
    public BinaryFilterBox(RandomAccessFile raf, JP2Box parent) {
        super(raf, parent);
        _realParent = parent;
    }

    /** Reads the box, putting appropriate information in
     *  the RepInfo object.  setModule, setBoxHeader,
     *  setRepInfo and setDataInputStream must be called
     *  before <code>readBox</code> is called. 
     *  <code>readBox</code> must completely consume the
     *  box, so that the next byte to be read by the
     *  DataInputStream is the <code>FF</code> byte of the next Box.
     */
    public boolean readBox() throws IOException {
        // Compare the filter type with the GZIP type.
        // If it's anything else, just report a property
        // and ignore the contents.
        byte[] uuidbuf = new byte[16];
        ModuleBase.readByteBuf (_dstrm, uuidbuf, _module);
        boolean isGzip = true;
        for (int i = 0; i < 16; i++) {
            if ((int) uuidbuf[i] != gzipuuid[i]) {
                isGzip = false;
            }
        }
        
        // Accumulate all binary filter UUIDs into a property.
        _module.addBinaryFilterProp (new Property ("BinaryFilter",
                    PropertyType.BYTE,
                    PropertyArity.ARRAY,
                    uuidbuf));
        if (isGzip) {
            // report that we've left information unprocessed
            _repInfo.setMessage(new InfoMessage
                    ("Binary Filter Box of type other than Gzip, contents not processed",
                     _module.getFilePos ()));
        }
        else {
            // We use a CountedInputStream, which will report an
            // EOF after streamLimit bytes.
            // The caller is responsible for making sure that
            // the underlying stream doesn't get mixed up with this
            // stream for counting purposes.
            // We have to put a DataInputStream on top of the
            // InflaterInputStream, which means there are two
            // DataInputStreams in the stream stack.  Ugly, but
            // should still work.
            int streamLimit = (int) (_boxHeader.getLength () - 16);
            boxStream = new DataInputStream
                    (new InflaterInputStream 
                    (new CountedInputStream (_dstrm, streamLimit)));
        }
        
        // We report _bytesRead as the total number of bytes in the
        // box, including the stream which hasn't actually been read
        // yet, because that makes things easier for the caller to
        // keep things counted.
        return true;
    }

    public Object next ()
    {
        BoxHeader hdr = new BoxHeader (_module, boxStream);
        try {
            hdr.readHeader ();
            JP2Box box = JP2Box.boxMaker (hdr.getType (), _realParent);
            box.setModule(_module);
            box.setRepInfo(_repInfo);
            box.setRandomAccessFile(_raf);
            box.setDataInputStream(boxStream);
            return box;
        }
        catch (IOException e) {
            // Will come here when the BoxHeader reaches an EOF
            return null;
        }
    }


    /** returns the InputStream which will provide the decompressed
     *  boxes subsumed in this Box.
     */
    public DataInputStream getBoxStream ()
    {
        return boxStream;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Binary Filter Box";
    }
}
