/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.tiff.ExifIFD;
import edu.harvard.hul.ois.jhove.module.tiff.TiffIFD;
import edu.harvard.hul.ois.jhove.module.tiff.TiffProfileExif;
import edu.harvard.hul.ois.jhove.module.tiff.TiffProfileExifIFD;
//import edu.harvard.hul.ois.jhove.module.*;

/**
 * Reader of Exif data embedded in a JPEG App1 block.  This makes use
 * of the TIFF module, since an Exif stream is really an embedded TIFF
 * file; but it is designed to fail cleanly if the TIFF module is absent.
 * 
 * @author Gary McGath
 *
 */
public final class JpegExif {

    private boolean _exifProfileOK;
    
    public JpegExif ()
    {
        _exifProfileOK = false;
    }



    /** Checks if the TIFF module is available. 
     */
    public static boolean isTiffAvailable ()
    {
        try {
            Class tiffClass = Class.forName ("edu.harvard.hul.ois.jhove.module.TiffModule");
            return true;
        }
        catch (Exception e) {
            return false;
        }
    }
    
    /** Reads the Exif data from the current point at the data stream,
     *  puts it into a temporary file, and makes a RepInfo object
     *  available.  This should be called only if isTiffAvailable()
     *  has returned <code>true</code>.
     */
    public RepInfo readExifData (DataInputStream dstream, JhoveBase je, 
				 int length)
    {
        RandomAccessFile tiffRaf = null;
        File tiffFile = null;
        FileOutputStream fos = null;
        RepInfo info = new RepInfo ("tempfile");
        /* We're now at the beginning of the TIFF data.
	 * Copy it into a temporary file, then parse that
	 * as a TIFF file. 
	 */
        try {
            tiffFile = je.tempFile ();
        }
        catch (IOException e) {
            info.setMessage (new ErrorMessage
                    ("Error creating temporary file. Check your configuration: " +
                     e.getMessage ()));
            return info;
        }
        try {
            fos = new FileOutputStream (tiffFile);
            int bufSize = je.getBufferSize ();
            int tiffLen = length - 8;
            /* Set a default buffer size if the app doesn't specify one. */
            if (bufSize <= 0) {
                bufSize = 32768;
            }
            if (bufSize > tiffLen) {
                // can buffer whole file in one buffer
                bufSize = tiffLen;
            }
            BufferedOutputStream bos = new BufferedOutputStream (fos, bufSize);
            byte[] buf = new byte[bufSize]; 
            while (tiffLen > 0) {
                //int len;
                int sz;
                if (tiffLen < bufSize) {
                    sz = tiffLen;
                }
                else {
                    sz = bufSize;
                }
                sz = dstream.read (buf, 0, sz);
                bos.write(buf, 0, sz);
                tiffLen -= sz;
            }
            fos.flush ();
            edu.harvard.hul.ois.jhove.module.TiffModule tiffMod = 
                new edu.harvard.hul.ois.jhove.module.TiffModule ();
            tiffMod.setByteOffsetValid(true);
            // Now parse the file, using a special parsing method.
            // Close only after we're all done.
            tiffRaf = new RandomAccessFile (tiffFile, "r");
            List ifds = tiffMod.exifParse (tiffRaf, info);
            if (ifds == null) {
                return info;
            }
            
            // Locate the Exif IFD.  (We probably also want the
            // Interoperability IFD eventually.)
            ListIterator iter = ifds.listIterator();
            boolean first = true;
            boolean haveNisoMetadata = false;
            while (iter.hasNext()) {
                Object ifd = iter.next ();
                if (ifd instanceof TiffIFD) {
                    // The TIFF IFD has useful information, which gets put
                    // into its NISO metadata.  Make it available to the caller.
                    if (first) {
                        NisoImageMetadata niso = ((TiffIFD) ifd).getNisoImageMetadata ();
                        // The first one is presumed to be the interesting one.
                        info.setProperty (new Property ("NisoImageMetadata",
                                               PropertyType.NISOIMAGEMETADATA,
                                               niso));
                        haveNisoMetadata = true;
                        TiffProfileExif exifProfile = new TiffProfileExif ();
                        _exifProfileOK = exifProfile.satisfiesProfile ((TiffIFD) ifd);
                    }
                }
                if (ifd instanceof ExifIFD) {
                    // Now for complicated stuff copying out the appropriate properties.
                    // Probably I just want to go through them and match interesting
                    // properties one by one, and copy them directly out.
                    // Or do I just want to copy the whole Exif property?
                    ExifIFD eifd = (ExifIFD) ifd;
                    Property ifdProp = eifd.getProperty( (je.getShowRawFlag ()));
                    List exifList = null;
                    if (ifdProp != null) {
                        exifList = eifd.exifProps (ifdProp);
                    }
                    if (_exifProfileOK) {
                        TiffProfileExifIFD exifIFDProfile = new TiffProfileExifIFD ();
                        _exifProfileOK = exifIFDProfile.satisfiesProfile(eifd);
                    }
                    if (exifList != null) {
                        info.setProperty(new Property ("Exif",
                                PropertyType.PROPERTY,
                                PropertyArity.LIST,
                                exifList));
                    }
                    // See if we have any interesting NISO metadata. If so, and
                    // we haven't gotten real NISO metadata, use it.
                    if (!haveNisoMetadata) {
                        NisoImageMetadata niso = eifd.getNisoImageMetadata ();
                        info.setProperty (new Property ("NisoImageMetadata",
                                PropertyType.NISOIMAGEMETADATA,
                                niso));
                    }
                }
                first = false;
            }
        }
        catch (IOException e) {
            info.setMessage (new ErrorMessage
                ("I/O exception processing Exif metadata: " +
		 e.getMessage ()));
            // Maybe should put this directly in the parent's
            // RepInfo, otherwise I have to copy the message afterwards.
        }
        finally {
            if (tiffRaf != null) {
                try {
                    tiffRaf.close();
                }
                catch (Exception e) {}
            }
            if (fos != null) {
                try {
                    fos.close();
                }
                catch (Exception e) {}
            }
            if (tiffFile != null) {
                try {
                    tiffFile.delete();
                }
                catch (Exception e) {}
            }
        }
        return info;
    }
    
    
    /** Returns <code>true</code> if the Exif IFD is present and satisfies
     *  the profile requirements.
     */
    public boolean isExifProfileOK ()
    {
        return _exifProfileOK;
    }
}
