/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.JpegModule;

/**
 * This class represents a SPIFF directory and the tags defined under
 * it.  A SPIFF directory consists of one or more APP8 segments, and
 * may define ancillary images. It is always contained within the
 * primary image stream.
 * 
 * @author Gary McGath
 *
 */
public class SpiffDir {

         
    private JpegModule _module; 
    
    /* list of thumbnail properties */
    private List _thumbnails;
    
    /**
     * 
     */
    public SpiffDir(JpegModule module) {
        _module = module;
        _thumbnails = new LinkedList ();
    }

    /**
     *  Reads a directory entry, starting at the position after
     * the APP8 marker and length.  If the entry is for a thumbnail, create
     * a Property for that thumbnail and add it to the thumbnail
     * list.  Other tags provide interesting information, some of
     * which should go into properties, but for the moment we
     * just handle the thumbnail and ignore other tags.
     * 
     * An APP8 segment which is in a SPIFF file, and isn't the
     * first APP8 segment (file header), is presumed to be a
     * directory entry.  These directory entries are a little
     * inconvenient, because they can contain offsets to data in
     * what we otherwise handle as a stream format. The offsets
     * can be either to data within the block, or to faraway
     * indirect data blocks.  For the present version, we ignore
     * offset data, which seems to be used only for the actual
     * image bits (e.g., TNDATA). 
     */
    public void readDirEntry (DataInputStream dstream, int length)
            throws IOException
    {
        int tag = (int) _module.readUnsignedInt (dstream);
        switch (tag) {
            case Spiff.THUMBNAIL:
            readThumbnail (dstream, length);
            break;
            
            default:
            _module.skipBytes (dstream, length - 6, _module);
            break;
        }
    }
    
    
    /**
     *  Appends any thumbnail properties that have been collected to
     * the provided list.
     */
    public void appendThumbnailProps (List imageList)
    {
        imageList.addAll (_thumbnails);
    }
    
    
    /* Reads a thumbnail entry.  A Property is created and added to
     * the list of thumbnails. 
     */
    private void readThumbnail (DataInputStream dstream, int length)
            throws IOException
    {
        NisoImageMetadata niso = new NisoImageMetadata();
        _module.skipBytes (dstream, 4, _module);   // tndata
        int height = _module.readUnsignedShort (dstream);
        int width = _module.readUnsignedShort (dstream);
        int tns = ModuleBase.readUnsignedByte (dstream, _module);
        int tnbps = ModuleBase.readUnsignedByte (dstream, _module);
        int tnc = ModuleBase.readUnsignedByte (dstream, _module);
        _module.skipBytes (dstream, length - 13, _module);
        
        // Fill in NISO data
        niso.setMimeType("image/jpeg");
        niso.setByteOrder ("big-endian");
        niso.setBitsPerSample (new int[] {tnbps} );
        int cs = Spiff.colorSpaceToNiso(tns);
        if (cs >= 0) {
            niso.setColorSpace (cs);
        }
        int comp = Spiff.compressionTypeToNiso (tnc);
        if (comp >= 0) {
            niso.setCompressionScheme(comp);
        }
        Property nisoProp = new Property ("NisoImageMetadata",
                   PropertyType.NISOIMAGEMETADATA, niso);
        List propList = new LinkedList ();
        propList.add (nisoProp);
        Property imageProp = new Property ("ThumbImage",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            propList);
        _thumbnails.add (imageProp);
    }
}
