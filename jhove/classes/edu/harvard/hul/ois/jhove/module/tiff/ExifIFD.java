/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2007 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Encapsulation of a Exif IFD
 */
public class ExifIFD
    extends IFD
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/


    /** ExifVersion tag. */
    private static final int
        EXPOSURETIME = 33434,
        FNUMBER = 33437,
        EXPOSUREPROGRAM = 34850,
        SPECTRALSENSITIVITY = 34852,
        ISOSPEEDRATINGS = 34855,
        OECF = 34856,
        EXIFVERSION = 36864,
        DATETIMEORIGINAL = 36867,
        DATETIMEDIGITIZED = 36868,
        COMPONENTSCONFIGURATION = 37121,
        COMPRESSEDBITSPERPIXEL = 37122,
        SHUTTERSPEEDVALUE = 37377,
        APERTUREVALUE = 37378,
        BRIGHTNESSVALUE = 37379,
        EXPOSUREBIASVALUE = 37380,
        MAXAPERTUREVALUE = 37381,
        SUBJECTDISTANCE = 37382,
        METERINGMODE = 37383,
        LIGHTSOURCE = 37384,
        FLASH = 37385,
        FOCALLENGTH = 37386,
        SUBJECTAREA = 37396,
        MAKERNOTE = 37500,
        USERCOMMENT = 37510,
        SUBSECTIME = 37520,
        SUBSECTIMEORIGINAL = 37521,
        SUBSECTIMEDIGITIZED = 37522,
        FLASHPIXVERSION = 40960,
        COLORSPACE = 40961,
        PIXELXDIMENSION = 40962,
        PIXELYDIMENSION = 40963,
        RELATEDSOUNDFILE = 40964,
        FLASHENERGY = 41483,
        SPATIALFREQUENCYRESPONSE = 41484,
        FOCALPLANEXRESOLUTION = 41486,
        FOCALPLANEYRESOLUTION = 41487,
        FOCALPLANERESOLUTIONUNIT = 41488,
        SUBJECTLOCATION = 41492,
        EXPOSUREINDEX = 41493,
        SENSINGMETHOD = 41495,
        FILESOURCE = 41728,
        SCENETYPE = 41729,
        CFAPATTERN = 41730,
        CUSTOMRENDERED = 41985,
        EXPOSUREMODE = 41986,
        WHITEBALANCE = 41987,
        DIGITALZOOMRATIO = 41988,
        FOCALLENGTHIN35MMFILM = 41989,
        SCENECAPTURETYPE = 41990,
        GAINCONTROL = 41991,
        CONTRAST = 41992,
        SATURATION = 41993,
        SHARPNESS = 41994,
        DEVICESETTINGDESCRIPTION = 41995,
        SUBJECTDISTANCERANGE = 41996,
        IMAGEUNIQUEID = 42016;

    private static final String [] COLORSPACE_L = {
        "sRGB", "uncalibrated"
    };
    private static final int [] COLORSPACE_INDEX = {
        1, 65535
    };
    public static final String [] COMPONENTSCONFIGURATION_L = {
        "Does not exist", "Y", "Cb", "Cr", "R", "G", "B"
    };
    public static final String [] CONTRAST_L = {
        "normal", "soft", "hard"
    };
    public static final String [] CUSTOMRENDERED_L = {
        "normal", "custom"
    };
    public static final String [] EXPOSUREMODE_L = {
        "auto", "manual", "auto bracket"
    };
    public static final String [] EXPOSUREPROGRAM_L = {
        "unidentified", "manual", "program normal", "aperture priority",
        "shutter priority", "program creative", "program action", 
        "portrait mode", "landscape mode"
    };
    public static final String [] FILESOURCE_L = {
        "", "", "", "DSC"
    };
    public static final String [] FLASH_L = {
        "did not fire",
        "fired",
        "strobe return light not detected", 
        "strobe return light detected", 
        "fired, compulsory flash mode",
        "fired, compulsory flash mode, return light not detected",
        "fired, compulsory flash mode, return light detected",
        "did not fire, compulsory flash mode",
        "did not fire, auto mode",
        "fired, auto mode",
        "fired, auto mode, return light not detected",
        "fired, auto mode, return light detected",
        "no flash function",
        "fired, red-eye reduction mode",
        "fired, red-eye reduction mode, return light not detected",
        "fired, red-eye reduction mode, return light detected",
        "fired, compulsory mode",
        "fired, compulsory mode, return light not detected",
        "fired, compulsory flash mode, return light detected",
        "fired, auto mode, red-eye reduction mode",
        "fired, auto mode, red-eye reduction mode, return light not detected",
        "fired, auto mode, red-eye reduction mode, return light detected",
    };
    public static final int[] FLASH_INDEX = {
        0, 1, 5, 7, 9, 13, 15, 16, 24, 25, 29, 31, 32, 65, 69,  71, 73, 77,
        79, 89, 93, 95
    };
    public static final String [] FOCALPLANERESOLUTIONUNIT_L = {
        "", "", "inches", "centimeters"
    };
    public static final String [] GAINCONTROL_L = {
        "none", "low gain up", "high gain up", "low gain down",
        "high gain down"
    };
    public static final String [] LIGHTSOURCE_L = {
        "unknown", "daylight", "fluorescent", "tungsten",
        "flash", "fine weather", "cloudy weather", "shade",
        "daylight flourescent (D 5700 - 7100K)",
        "day white flourescent (N 4600 - 5400K)",
        "cool white flourescent (W 3900 - 4500K)",
        "white flourescent (WW 3200 - 3700K)",
        "standard light A", "standard light B", "standard light C",
        "D55", "D65", "D75", "D50", "ISO studio tungsten", "other"
    };
    public static final int [] LIGHTSOURCE_INDEX = {
        0, 1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23,
        24, 255
    };
    public static final String [] METERINGMODE_L = {
        "unidentified", "average", "centre weighted average", "spot",
        "multispot", "pattern", "partial", "other"
    };
    public static final int [] METERINGMODE_INDEX = {
        0, 1, 2, 3, 4, 5, 6, 255
    };
    public static final String [] SATURATION_L = {
        "normal", "soft", "hard"
    };
    public static final String [] SCENECAPTURETYPE_L = {
        "standard", "landscape", "portrait", "night"
    };
    public static final String [] SCENETYPE_L = {
        "", "directly photographed image"
    };
    public static final String [] SENSINGMETHOD_L = {
        "", "not defined", "one-chip color area", 
        "two-chip color area", "three-chip color area",
        "color sequential area", "", "trilinear", "colour sequential linear"
    };
    public static final String [] SHARPNESS_L = {
        "normal", "soft", "hard"
    };
    public static final String [] SUBJECTDISTANCERANGE_L = {
        "unknown", "macro", "close", "distant"
    };
    public static final String [] WHITEBALANCE_L = {
        "auto", "manual"
    };

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Aperature value tag. */
    private Rational _apertureValue;
    private Rational _brightnessValue;
    private int [] _cfaPattern;
    private int _colorSpace;
    private int [] _componentsConfiguration;
    private Rational _compressedBitsPerPixel;
    private int _contrast; 
    private int _customRendered;
    private String _dateTimeDigitized;
    private String _dateTimeOriginal;
    private int [] _deviceSettingDescription;
    private Rational _digitalZoomRatio;
    private String _exifVersion;
    private Rational _exposureBiasValue;
    private Rational _exposureIndex;
    private int _exposureMode;
    private int _exposureProgram;
    private Rational _exposureTime;
    private int _fileSource;
    private int _flash;
    private Rational _flashEnergy;
    private String _flashpixVersion;
    private Rational _fNumber;
    private Rational _focalLength;
    private int _focalLengthIn35mmFilm;
    private Rational _focalPlaneXResolution;
    private Rational _focalPlaneYResolution;
    private int _focalPlaneResolutionUnit;
    private int _gainControl;
    private String _imageUniqueID;
    private int [] _isoSpeedRatings;
    private int _lightSource;
    private int [] _makerNote;
    private Rational _maxApertureValue;
    private int _meteringMode;
    private int [] _oecf;
    private long _pixelXDimension;
    private long _pixelYDimension;
    private String _relatedSoundFile;
    private int _saturation;
    private int _sceneCaptureType;
    private int _sceneType;
    private int _sensingMethod;
    private int _sharpness;
    private Rational _shutterSpeedValue;
    private int [] _spatialFrequencyResponse;
    private String _spectralSensitivity;
    private int [] _subjectArea;
    private Rational _subjectDistance;
    private int _subjectDistanceRange;
    private int [] _subjectLocation;
    private String _subSecTime;
    private String _subSecTimeDigitized;
    private String _subSecTimeOriginal;
    private int [] _userComment;
    private int _whiteBalance;
    
    /* data from standard TIFF tags */
    private String _manufacturer;
    private String _model;
    private String _software;
    private String _artist;
    private int _orientation;

    private NisoImageMetadata _niso;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate an <code>ExifIFD</code> object.
     * @param offset IFD offset
     * @param info  the RepInfo object
     * @param raf TIFF file
     * @param bigEndian True if big-endian file
     */
    public ExifIFD (long offset, RepInfo info, RandomAccessFile raf,
                    boolean bigEndian)
    {
        super (offset, info, raf, bigEndian);

        _colorSpace = NULL;
        _contrast = 0;
        _customRendered = NULL;
        _exifVersion = "0220";
        _exposureMode = NULL;
        _exposureProgram = NULL;
        _fileSource = NULL;
        _flash = NULL;
        _flashpixVersion = "0100";
        _focalLengthIn35mmFilm = NULL;
        _focalPlaneResolutionUnit = 2;
        _gainControl = NULL;
        _lightSource = NULL;
        _meteringMode = NULL;
        _pixelXDimension = NULL;
        _pixelYDimension = NULL;
        _saturation = NULL;
        _sceneCaptureType = NULL;
        _sceneType = NULL;
        _sensingMethod = NULL;
        _sharpness = NULL;
        _subjectDistanceRange = NULL;
        _whiteBalance = NULL;
        _niso = new NisoImageMetadata ();
     }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /** Get the IFD properties. */
    public Property getProperty (boolean rawOutput)
    {
        List entries = new LinkedList ();

        entries.add (new Property ("ExifVersion", PropertyType.STRING,
                                   _exifVersion));
        entries.add (new Property ("FlashpixVersion", PropertyType.STRING,
                                   _flashpixVersion));
        if (_colorSpace != NULL) {
            entries.add (addIntegerProperty ("ColorSpace", _colorSpace,
                                             COLORSPACE_L, COLORSPACE_INDEX,
                                             rawOutput));
        }
        if (_componentsConfiguration != null) {
            entries.add (new Property ("ComponentsConfiguration",
                                       PropertyType.INTEGER,
                                       PropertyArity.ARRAY,
                                       _componentsConfiguration));
        }
        if (_compressedBitsPerPixel != null)  {
            entries.add (addRationalProperty ("CompressedBitsPerPixel",
                                              _compressedBitsPerPixel,
                                              rawOutput));
        }
        if (_pixelXDimension != NULL) {
            entries.add (new Property ("PixelXDimension", PropertyType.LONG,
                                       new Long (_pixelXDimension)));
        }
        if (_pixelYDimension != NULL) {
            entries.add (new Property ("PixelYDimension", PropertyType.LONG,
                                       new Long (_pixelYDimension)));
        }
        if (_makerNote != null) {
            entries.add (new Property ("MakerNote", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _makerNote));
        }
        if (_userComment != null) {
            Property ucp = makeUserCommentProperty (_userComment, rawOutput);
            if (ucp != null) {
               entries.add (ucp);
            }
        }
        if (_relatedSoundFile != null) {
            entries.add (new Property ("RelatedSoundFile", PropertyType.STRING,
                                       _relatedSoundFile));
        }
        if (_dateTimeOriginal != null) {
            entries.add (new Property ("DateTimeOriginal", PropertyType.STRING,
                                       _dateTimeOriginal));
        }
        if (_dateTimeDigitized != null) {
            entries.add (new Property ("DateTimeDigitized",
                                       PropertyType.STRING,
                                       _dateTimeDigitized));
        }
        if (_subSecTime != null) {
            entries.add (new Property ("SubSecTime", PropertyType.STRING,
                                       _subSecTime));
        }
        if (_subSecTimeOriginal != null) {
            entries.add (new Property ("SubSecTimeOriginal",
				       PropertyType.STRING,
				       _subSecTimeOriginal));
        }
        if (_subSecTimeDigitized != null) {
            entries.add (new Property ("SubSecTimeDigitized",
				       PropertyType.STRING,
                                       _subSecTimeDigitized));
        }
        if (_imageUniqueID != null) {
            entries.add (new Property ("ImageUniqueID",PropertyType.STRING,
                                       _imageUniqueID));
        }

        if (_exposureTime != null) {
            entries.add (addRationalProperty ("ExposureTime", _exposureTime,
                                              rawOutput));
        }
        if (_fNumber != null) {
            entries.add (addRationalProperty ("FNumber", _fNumber,
                                              rawOutput));
        }
        if (_exposureProgram != NULL) {
            entries.add (addIntegerProperty ("ExposureProgram",
                                             _exposureProgram,
                                             EXPOSUREPROGRAM_L, rawOutput));
        }
        if (_spectralSensitivity != null) {
            entries.add (new Property ("SpectralSensitivity",
                                       PropertyType.STRING,
                                       _spectralSensitivity));
        }
        if (_isoSpeedRatings != null) {
            entries.add (new Property ("ISOSpeedRatings", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _isoSpeedRatings));
        }
        if (_oecf != null) {
            entries.add (new Property ("OECF", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _oecf));
        }
        if (_shutterSpeedValue != null) {
            entries.add (addRationalProperty ("ShutterSpeedValue",
                                              _shutterSpeedValue, rawOutput));
        }
        if (_apertureValue != null) {
            entries.add (addRationalProperty ("ApertureValue", _apertureValue,
                                              rawOutput));
        }
        if (_brightnessValue != null) {
            entries.add (addRationalProperty ("BrightnessValue",
                                              _brightnessValue, rawOutput));
        }
        if (_exposureBiasValue != null) {
            entries.add (addRationalProperty ("ExposureBiasValue",
                                              _exposureBiasValue,
                                              rawOutput));
        }
        if (_maxApertureValue != null) {
            entries.add (addRationalProperty ("MaxApertureValue",
                                              _maxApertureValue, rawOutput));
        }
        if (_subjectDistance != null) {
            entries.add (addRationalProperty ("SubjectDistance",
                                              _subjectDistance, rawOutput));
        }
        if (_meteringMode != NULL) {
            entries.add (addIntegerProperty ("MeteringMode", _meteringMode,
                                             METERINGMODE_L,
                                             METERINGMODE_INDEX, rawOutput));
        }
        if (_lightSource != NULL) {
            entries.add (addIntegerProperty ("LightSource", _lightSource,
                                             LIGHTSOURCE_L,
                                             LIGHTSOURCE_INDEX, rawOutput));
        }
        if (_flash != NULL) {
            entries.add (addIntegerProperty ("Flash", _flash, FLASH_L,
                                             FLASH_INDEX, rawOutput));
        }
        if (_focalLength != null) {
            entries.add (addRationalProperty ("FocalLength", _focalLength,
                                              rawOutput));
        }
        if (_subjectArea != null) {
            entries.add (new Property ("SubjectArea", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _subjectArea));
        }
        if (_flashEnergy != null) {
            entries.add (addRationalProperty ("FlashEnergy", _flashEnergy,
                                              rawOutput));
        }
        if (_spatialFrequencyResponse != null) {
            entries.add (new Property ("SubjectArea", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _subjectArea));
        }
        if (_focalPlaneXResolution != null) {
            entries.add (addRationalProperty ("FocalPlaneXResolution",
                                              _focalPlaneXResolution,
                                              rawOutput));
        }
        if (_focalPlaneYResolution != null) {
            entries.add (addRationalProperty ("FocalPlaneYResolution",
                                              _focalPlaneYResolution,
                                              rawOutput));
        }
        if (_focalPlaneResolutionUnit != NULL) {
            entries.add (addIntegerProperty ("FocalPlaneResolutionUnit",
                                             _focalPlaneResolutionUnit,
                                             FOCALPLANERESOLUTIONUNIT_L,
                                             rawOutput));
        }
        if (_subjectLocation != null) {
            entries.add (new Property ("SubjectLocation", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _subjectLocation));
        }
        if (_exposureIndex != null) {
            entries.add (addRationalProperty ("ExposureIndex", _exposureIndex,
                                              rawOutput));
        }
        if (_sensingMethod != NULL) {
            entries.add (addIntegerProperty ("SensingMethod", _sensingMethod,
                                             SENSINGMETHOD_L, rawOutput));
        }
        if (_fileSource != NULL) {
            entries.add (addIntegerProperty ("FileSource", _fileSource,
                                             FILESOURCE_L, rawOutput));
        }
        if (_sceneType != NULL) {
            entries.add (addIntegerProperty ("SceneType", _sceneType,
                                             SCENETYPE_L, rawOutput));
        }
        if (_cfaPattern != null) {
            entries.add (new Property ("CFAPattern", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _cfaPattern));
        }
        if (_customRendered != NULL) {
            entries.add (addIntegerProperty ("CustomRendered", _customRendered,
                                             CUSTOMRENDERED_L, rawOutput));
        }
        if (_exposureMode != NULL) {
            entries.add (addIntegerProperty ("ExposureMode", _exposureMode,
                                             EXPOSUREMODE_L, rawOutput));
        }
        if (_whiteBalance != NULL) {
            entries.add (addIntegerProperty ("WhiteBalance", _whiteBalance,
                                             WHITEBALANCE_L, rawOutput));
        }
        if (_digitalZoomRatio != null) {
            entries.add (addRationalProperty ("DigitalZoomRatio",
                                              _digitalZoomRatio, rawOutput));
        }
        if (_focalLengthIn35mmFilm != NULL) {
            entries.add (new Property ("FocalLengthIn35mmFilm",
                                       PropertyType.INTEGER,
                                       new Integer (_focalLengthIn35mmFilm)));
        }
        if (_sceneCaptureType != NULL) {
            entries.add (addIntegerProperty ("SceneCaptureType",
                                             _sceneCaptureType,
                                             SCENECAPTURETYPE_L, rawOutput));
        }
        if (_gainControl != NULL) {
            entries.add (addIntegerProperty ("GainControl", _gainControl,
					     GAINCONTROL_L, rawOutput));
        }
        if (_saturation != NULL) {
            entries.add (addIntegerProperty ("Saturation", _saturation,
                                             SATURATION_L, rawOutput));
        }
        if (_sharpness != NULL) {
            entries.add (addIntegerProperty ("Sharpness", _sharpness,
                                             SHARPNESS_L, rawOutput));
        }
        if (_deviceSettingDescription != null) {
            entries.add (new Property ("DeviceSettingDescription",
                                       PropertyType.INTEGER,
                                       PropertyArity.ARRAY,
                                       _deviceSettingDescription));
        }
        if (_subjectDistanceRange != NULL) {
            entries.add (addIntegerProperty ("SubjectDistanceRange",
                                             _subjectDistanceRange,
                                             SUBJECTDISTANCERANGE_L,
                                             rawOutput));
        }

        // properties from standard TIFF tags
        if (_manufacturer != null) {
            entries.add (new Property ("Make",
                    PropertyType.STRING,
                    _manufacturer));
        }
        if (_model != null) {
            entries.add (new Property ("Model",
                    PropertyType.STRING,
                    _model));
        }
        if (_software != null) {
            entries.add (new Property ("Software",
                    PropertyType.STRING,
                    _software));
        }
        if (_artist != null) {
            entries.add (new Property ("Artist",
                    PropertyType.STRING,
                    _artist));
        }
        return propertyHeader ("Exif", entries);
    }
    
    
    /** Returns the Exif version string (tag 36864). */
    public String getExifVersion ()
    {
        return _exifVersion;
    }
    
    /** Returns the constructed NisoImageMetadata. */
    public NisoImageMetadata getNisoImageMetadata ()
    {
        return _niso;
    }


    /** Returns the Flashpix version string (tag 40960). */
    public String getFlashpixVersion ()
    {
        return _flashpixVersion;
    }

    /** returns the colorspace value (tag 40961). */
    public int getColorspace ()
    {
        return _colorSpace;
    }



    /** Extracts and returns the Exif property list from a standard
     *  IFD property header.
     */
    public List exifProps (Property pHeader) 
    {
        try {
            Property[] pArr = (Property []) pHeader.getValue ();
            Property entries = pArr[2];
            return (List) entries.getValue ();
        }
        catch (Exception e) {
            // We could get caught here if we somehow tried to get
            // the Exif properties from something that wasn't a
            // standard property header.
            return null;
        }
    }


    /** Lookup an IFD tag. */
    public void lookupTag (int tag, int type, long count, long value)
        throws TiffException
    {
        try {
            if (tag == APERTUREVALUE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _apertureValue = readRational (count, value);
            }
            else if (tag == BRIGHTNESSVALUE) {
                checkType  (tag, type, SRATIONAL);
                checkCount (tag, count, 1);
                _brightnessValue = readRational (count, value);
            }
            else if (tag == CFAPATTERN) {
                checkType  (tag, type, UNDEFINED);
                _cfaPattern = readByteArray (type, count, value);
            }
            else if (tag == COLORSPACE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _colorSpace = readShort (type, count, value);
            }
            else if (tag == COLORSPACE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _colorSpace = readShort (type, count, value);
            }
            else if (tag == COMPONENTSCONFIGURATION) {
                checkType  (tag, type, UNDEFINED);
                _componentsConfiguration = readByteArray (type, count, value);
            }
            else if (tag == COMPRESSEDBITSPERPIXEL) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _compressedBitsPerPixel = readRational (count, value);
            }
            else if (tag == CONTRAST) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _contrast = readShort (type, count, value);
            }
            else if (tag == CUSTOMRENDERED) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _customRendered = readShort (type, count, value);
            }
            else if (tag == DATETIMEDIGITIZED) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 20);
                _dateTimeDigitized = readASCII (count, value);
            }
            else if (tag == DATETIMEORIGINAL) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 20);
                _dateTimeOriginal = readASCII (count, value);
            }
            else if (tag == DEVICESETTINGDESCRIPTION) {
                checkType  (tag, type, UNDEFINED);
                _deviceSettingDescription = readByteArray (type, count, value);
            }
            else if (tag == DIGITALZOOMRATIO) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _digitalZoomRatio = readRational (count, value);
            }
            else if (tag == EXIFVERSION) {
                checkType  (tag, type, UNDEFINED);
                checkCount (tag, count, 4);
                int [] iarray = readShortArray (type, count, value);
                char [] carray = new char [iarray.length];
                for (int i=0; i<iarray.length; i++) {
                    carray[i] = (char) iarray[i];
                }
                _exifVersion = new String (carray);
            }
            else if (tag == EXPOSUREBIASVALUE) {
                checkType  (tag, type, SRATIONAL);
                checkCount (tag, count, 1);
                _exposureBiasValue = readRational (count, value);
            }
            else if (tag == EXPOSUREINDEX) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _exposureIndex = readRational (count, value);
            }
            else if (tag == EXPOSUREMODE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _exposureMode = readShort (type, count, value);
            }
            else if (tag == EXPOSUREPROGRAM) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _exposureProgram = readShort (type, count, value);
            }
            else if (tag == EXPOSURETIME) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _exposureTime = readRational (count, value);
            }
            else if (tag == FILESOURCE) {
                checkType  (tag, type, UNDEFINED);
                checkCount (tag, count, 1);
                _fileSource = readByte (type, count, value);
            }
            else if (tag == FLASH) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _flash = readShort (type, count, value);
            }
            else if (tag == FLASHENERGY) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _flashEnergy = readRational (count, value);
            }
            else if (tag == FLASHPIXVERSION) {
                checkType  (tag, type, UNDEFINED);
                checkCount (tag, count, 4);
                int [] iarray = readShortArray (type, count, value);
                char [] carray = new char [iarray.length];
                for (int i=0; i<iarray.length; i++) {
                    carray[i] = (char) iarray[i];
                }
                _flashpixVersion = new String (carray);
            }
            else if (tag == FNUMBER) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _fNumber = readRational (count, value);
            }
            else if (tag == FOCALLENGTH) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _focalLength = readRational (count, value);
            }
            else if (tag == FOCALLENGTHIN35MMFILM) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _focalLengthIn35mmFilm = readShort (type, count, value);
            }
            else if (tag == FOCALPLANEXRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _focalPlaneXResolution = readRational (count, value);
            }
            else if (tag == FOCALPLANEYRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _focalPlaneYResolution = readRational (count, value);
            }
            else if (tag == FOCALPLANERESOLUTIONUNIT) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _focalPlaneResolutionUnit = readShort (type, count, value);
            }
            else if (tag == GAINCONTROL) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
		_gainControl = readShort (type, count, value);
		/******************************************************
		 * The EXIF 2.2 specification (JEITA CP-3451, April 2002)
		 * incorrectly identifies the type of the GainControl tag
		 * (41911) as RATIONAL in Table 5 on page 25; it is
		 * correctly identified as SHORT in the detailed tag
		 * description on page 43.
		 * If we wanted to accept either SHORT or RATIONAL
		 * uncomment the following:
		 ******************************************************
                checkType  (tag, type, SHORT, RATIONAL);
                checkCount (tag, count, 1);
		if (type == RATIONAL) {
		    Rational rat = readRational (count, value);
		    _gainControl = (int) rat.toLong ();
		    _info.setMessage (new InfoMessage ("EXIF GainControl " +
			       "tag (41991) is of type RATIONAL, not SHORT"));
		}
		else {
		    _gainControl = readShort (type, count, value);
		}
		******************************************************/
            }
            else if (tag == IMAGEUNIQUEID) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 33);
                _imageUniqueID = readASCII (count, value);
            }
            else if (tag == ISOSPEEDRATINGS) {
                checkType  (tag, type, SHORT);
                _isoSpeedRatings = readShortArray (type, count, value);
            }
            else if (tag == LIGHTSOURCE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _lightSource = readShort (type, count, value);
            }
            else if (tag == MAKERNOTE) {
                checkType  (tag, type, UNDEFINED);
                _makerNote = readShortArray (type, count, value);
            }
            else if (tag == MAXAPERTUREVALUE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _maxApertureValue = readRational (count, value);
            }
            else if (tag == METERINGMODE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _meteringMode = readShort (type, count, value);
            }
            else if (tag == OECF) {
                checkType  (tag, type, SHORT);
                _oecf = readShortArray (type, count, value);
            }
            else if (tag == PIXELXDIMENSION) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _pixelXDimension = readLong (type, count, value);
            }
            else if (tag == PIXELYDIMENSION) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _pixelYDimension = readLong (type, count, value);
            }
            else if (tag == RELATEDSOUNDFILE) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 13);
                _relatedSoundFile = readASCII (count, value);
            }
            else if (tag == SATURATION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _saturation = readShort (type, count, value);
            }
            else if (tag == SCENECAPTURETYPE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _sceneCaptureType = readShort (type, count, value);
            }
            else if (tag == SCENETYPE) {
                checkType  (tag, type, UNDEFINED);
                checkCount (tag, count, 1);
                _sceneType = readShort (type, count, value);
            }
            else if (tag == SENSINGMETHOD) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _sensingMethod = readShort (type, count, value);
            }
            else if (tag == SHARPNESS) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _sharpness = readShort (type, count, value);
            }
            else if (tag == SHUTTERSPEEDVALUE) {
                checkType  (tag, type, SRATIONAL);
                checkCount (tag, count, 1);
                _shutterSpeedValue = readRational (count, value);
            }
            else if (tag == SPATIALFREQUENCYRESPONSE) {
                checkType  (tag, type, UNDEFINED);
                _spatialFrequencyResponse = readShortArray(type, count, value);
            }
            else if (tag == SPECTRALSENSITIVITY) {
                checkType  (tag, type, ASCII);
                _spectralSensitivity = readASCII (count, value);
            }
            else if (tag == SUBJECTAREA) {
                checkType  (tag, type, SHORT);
                _subjectArea = readShortArray (type, count, value);
            }
            else if (tag == SUBJECTDISTANCE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _subjectDistance = readRational (count, value);
            }
            else if (tag == SUBJECTDISTANCERANGE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _subjectDistanceRange = readShort (type, count, value);
            }
            else if (tag == SUBJECTLOCATION) {
                checkType  (tag, type, SHORT);
                _subjectLocation = readShortArray (type, count, value);
            }
            else if (tag == SUBSECTIME) {
                checkType  (tag, type, ASCII);
                _subSecTime = readASCII (count, value);
            }
            else if (tag == SUBSECTIMEDIGITIZED) {
                checkType  (tag, type, ASCII);
                _subSecTimeDigitized = readASCII (count, value);
            }
            else if (tag == SUBSECTIMEORIGINAL) {
                checkType  (tag, type, ASCII);
                _subSecTimeOriginal = readASCII (count, value);
            }
            else if (tag == USERCOMMENT) {
                checkType  (tag, type, UNDEFINED);
                _userComment = readByteArray (type, count, value);
            }
            
            // Here we check for non-EXIF tags, because some documents use
            // standard TIFF tags in an EXIF IFD to provide metadata.
            else if (tag == TiffIFD.MAKE) {
                checkType  (tag, type, ASCII);
                String make = readASCII (count, value);
                _niso.setScannerManufacturer (make);
                _manufacturer = make;
            }
            else if (tag == TiffIFD.MODEL) {
                checkType  (tag, type, ASCII);
                String model = readASCII (count, value);
                _niso.setScannerModelName (model);
                _model = model;
            }
            else if (tag == TiffIFD.ORIENTATION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                int orient = readShort (type, count, value);
                _niso.setOrientation (orient);
                _orientation = orient;
            }
            else if (tag == TiffIFD.XRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _niso.setXSamplingFrequency (readRational (count,
                                                           value));
            }
            else if (tag == TiffIFD.YRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _niso.setYSamplingFrequency (readRational (count,
                                                           value));
            }

        }
        catch (IOException e) {
            throw new TiffException ("Read error for tag " + tag, value);
        }
    }
    
    
    /* Assemble the userComment, which consists of an array of up to three
     * properties: IDCode, Value, and RawValue. 
     */
    private Property makeUserCommentProperty 
            (int[] rawValue, boolean rawOutput)
    {
        String idCode = "Undefined";
        String cmtValue = null;
 
        try {
            /* Convert the first 8 bytes into a zero-terminated string */
            StringBuffer idBuf = new StringBuffer (8);
            int byteLim = 8;
            if (rawValue.length < 8) {
                byteLim = rawValue.length;
            }
            if (rawValue[0] != 0) {
                for (int i = 0; i < byteLim; i++) {
                    if (rawValue[i] == 0) {
                        break;
                    }
                    idBuf.append((char) rawValue[i]);
                }
                idCode = idBuf.toString ();
            }
            
            // If the ID code is "ASCII" or "UNICODE", read the bytes
            // into a string with the appropriate encoding.  We assume
            // UNICODE means UTF-8.
            
            if ("ASCII".equals (idCode) || "UNICODE".equals (idCode)) {
                byte[] textBytes = new byte[rawValue.length - 8];
                for (int i = 0; i < rawValue.length - 8; i++) {
                    textBytes[i] = (byte) rawValue [i + 8];
                }
                String encoding;
                if ("ASCII".equals (idCode)) {
                    encoding = "ASCII";
                }
                else {
                    encoding = "UTF8";
                }
                cmtValue = new String (textBytes, encoding);
            }
            
            Property [] propArray;
            if (rawValue != null && cmtValue != null) {
                propArray = new Property [3];
            }
            else {
                propArray = new Property[2];
            }
            propArray[0] = new Property ("IDCode", PropertyType.STRING, idCode);
            int i = 1;
            if (cmtValue != null) {
                propArray[i++] = new Property 
                        ("Value", PropertyType.STRING, idCode); 
            }
            if (rawValue != null) {
                propArray[i++] = new Property
                        ("RawValue", PropertyType.INTEGER, 
                        PropertyArity.ARRAY,
                        rawValue);
            }
            
            return new Property ("UserComment", PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        propArray);
        }
        catch (Exception e) {
            // In case of anomalous data
            return null;
        }        
    } 
}
