/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;

/**
 * Encapsulation of Exif information for a Wave file.  Exif sound
 * information doesn't closely follow Exif image information, so we
 * don't particularly try to force property names to match.
 * 
 * @see edu.harvard.hul.ois.jhove.module.tiff.ExifIFD
 *
 * @author Gary McGath
 *
 */
public class ExifInfo {

    private String _exifVersion;
    private String _relatedImageFile;
    private String _timeCreated;
    private String _manufacturer;
    private String _model;
    private byte[] _makerNote;
    private String _userComment;
   
    public ExifInfo ()
    {
        
    }
    
    /** Constructs a property and returns it. */
    public Property buildProperty ()
    {
        List entries = new LinkedList ();

        if (_exifVersion != null) {
            entries.add (new Property ("ExifVersion", PropertyType.STRING,
                                   _exifVersion));
        }
        else {
            return null;          // Version must be specified
        }
        if (_relatedImageFile != null) {
            entries.add (new Property ("RelatedImageFile", PropertyType.STRING,
                                   _relatedImageFile));
        }
        if (_timeCreated != null) {
            entries.add (new Property ("TimeCreated", PropertyType.STRING,
                                   _timeCreated));
        }
        if (_manufacturer != null) {
            entries.add (new Property ("Manufacturer", PropertyType.STRING,
                                   _manufacturer));
        }
        if (_model != null) {
            entries.add (new Property ("Model", PropertyType.STRING,
                                   _model));
        }
        if (_makerNote != null) {
            entries.add (new Property ("MakerNote", PropertyType.BYTE,
                                   PropertyArity.ARRAY,
                                   _makerNote));
        }
        if (_userComment != null) {
            entries.add (new Property ("UserComment", PropertyType.STRING,
                                   _userComment));
        }
        
        
        return new Property ("Exif", PropertyType.PROPERTY,
            PropertyArity.LIST,
            entries);
    }
    
    
    /** Converts the raw 4-byte array into a version string and
     *  stores it. */
    protected void setExifVersion(String version) {
        _exifVersion = version;
    }
    
    /** Sets the related image file name. */
    protected void setRelatedImageFile (String file)
    {
        _relatedImageFile = file;
    }

    /** Sets the creation time as an ASCII string. */
    protected void setTimeCreated (String time)
    {
        _timeCreated = time;
    }


    /** Sets the manufacturer of the equipment that produced the file. */
    protected void setManufacturer (String file)
    {
        _manufacturer = file;
    }

    /** Sets the model of the equipment that produced the file. */
    protected void setModel (String file)
    {
        _model = file;
    }
    
    /** Sets the maker note. */
    protected void setMakerNote (byte[] note) 
    {
        _makerNote = note;
    }
    
    /** Sets the user comment. */
    protected void setUserComment (String comment)
    {
        _userComment = comment;
    }
}
