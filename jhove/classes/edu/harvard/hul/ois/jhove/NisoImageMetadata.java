/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 * Encapsulation of the NISO Z39.87-2002 / AIIM 20-2002 Data Dictionary --
 * Technical Metadata for Digital Still Images
 */
public class NisoImageMetadata
{
    /******************************************************************
     * PUBLIC CLASS FIELDS.
     ******************************************************************/

    /** 7.7.3.15 auto focus value labels. */
    public static final String [] AUTOFOCUS = {
	"unidentified", "auto focus used", "auto focus interrupted",
	"near focused", "soft focus", "manual"
    };

    /** 7.7.3.13 back light value labels. */
    public static final String [] BACKLIGHT = {
	"front leight", "backlight 1", "backlight 2"
    };

    /** 6.1.2 byte order value labels. */
    public static final String [] BYTEORDER = {
	"big-endian", "little-endian"
    };

    /** 6.2.3.1 Checksum method value labels. */
    public static final String [] CHECKSUM_METHOD = {
	"CRC32", "MD5", "SHA-1"
    };

    /** 6.1.4.1 Color space value labels. */
    public static final String [] COLORSPACE = {
	"white is zero", "black is zero", "RGB", "palette color",
	"transparency mask", "CMYK", "YCbCr", "CIE L*a*b*", "ICC L*a*b*",
    "ITU L*a*b*",
    "CFA",
    "CIE Log2(L)",
    "CIE Log2(L)(u',v')",
    "LinearRaw"
    };
    /** Index for 6.1.4.1 color space value labels. */
    public static final int [] COLORSPACE_INDEX = {
	0, 1, 2, 3, 
    4, 5, 6, 8, 9,
    10,
    32803,
    32844,
    32845,
    34892
    };

    /** 6.1.3.1 Compression scheme value labels. */
    public static final String [] COMPRESSION_SCHEME = {
	"uncompressed", "CCITT 1D", "CCITT Group 3", "CCITT Group 4", /* 1-4 */
	"LZW", "JPEG", "ISO JPEG", "Deflate",                 /* 5-8 */
	"JBIG",                                               /* 32661 */
	"RLE with word alignment",                            /* 32771 */
	"PackBits", "NeXT 2-bit encoding", "ThunderScan 4-bit encoding", /* 32773- */
	"RasterPadding in CT or MP",                          /* 32895 */
	"RLE for LW", "RLE for HC", "RLE for BL",             /* 32896-8 */
	"Pixar 10-bit LZW",                                   /* 32908 */
	"Pixar companded 11-bit ZIP encoding",                /* 32909 */
	"PKZIP-style Deflate encoding",                       /* 32946 */
	"Kodak DCS",                                          /* 32947 */
	"SGI 32-bit Log Luminance encoding",                  /* 34676 */
	"SGI 24-bit Log Luminance encoding",                  /* 34677 */
	"JPEG 2000"                                           /* 34712 */
    };
    /** Index for 6.1.3.1 compression scheme value labels. */
    public static final int [] COMPRESSION_SCHEME_INDEX = {
	1, 2, 3, 4, 
	5, 6, 7, 8, 
	32661,
	32771,
	32773, 32766, 32809, 
	32895, 
	32896, 32897, 32898, 
	32908,
	32909, 
	32946, 
	32947,
	34676, 
	34677,
	34712
    };

    /** 6.2.5 display orientation value labels. */
    public static final String [] DISPLAY_ORIENTATION = {
	"portrait", "landscape"
    };

    public static final String [] EXTRA_SAMPLES = {
	"unspecified", "associated alpha", "unassociated alpha",
	"range or depth"
    };

    /** 7.7.3.10 flash value labels. */
    public static final String [] FLASH = {
	"yes", "no"
    };

    /** 7.7.3.12 flash return value labels. */
    public static final String [] FLASH_RETURN = {
	"yes", "no"
    };

    /** 8.2.6 gray response unit value labels for version 0.2. */
    public static final String [] GRAY_RESPONSE_UNIT_02 = {
	"", "tenths of a unit", "hundredths of a unit",
	"thousandths of a unit", "ten-thousandths of a unit",
	"hundred-thousandths of a unit"
    };
    
    /** Gray response unit value for version 2.0 of MIX, corresponding
     *  to NISO values of 1-5 */
    public static final String [] GRAY_RESPONSE_UNIT_20 = {
        "Number represents tenths of a unit",
        "Number represents hundredths of a unit",
        "Number represents thousandths of a unit",
        "Number represents ten-thousandths of a unit",
        "Number represents hundred-thousandths of a unit"
    };

   /** extra sample value for version 2.0 of MIX, corresponding
    *  to NISO values of 0-3 **/
    public static final String [] EXTRA_SAMPLE_20 = {
	    "unspecified data",
	    "associated alpha data (with pre-multiplied color)",
	    "unassociated alpha data",
	    "range or depth data"
	};
	
    /** 7.7.3.6 metering mode value labels. */
    public static final String [] METERING_MODE = {
	"unidentified", "average", "center-weighted average", "spot",
	"multispot", "pattern", "partial"
    };

    /** 6.2.4 orientation value labels. */
    public static final String [] ORIENTATION = {
	"", "normal", "reflected horiz", "rotated 180 deg", "reflected vert",
	"left top", "rotated cw 90 deg", "Right bottom", "Rotated ccw 90 deg", 
	"Unknown"
    };

    /** 6.1.6 planar configuration value labels. */
    public static final String [] PLANAR_CONFIGURATION = {
	"", "chunky", "planar"
    };

    /** 8.1.1 sampling frequency plane value labels. */
    public static final String [] SAMPLING_FREQUENCY_PLANE = {
	"", "camera/scanner focal plane", "object plane", "source object plane"
    };

    /** 8.1.2 sampling frequency unit value labels. */
    public static final String [] SAMPLING_FREQUENCY_UNIT = {
	"", "no absolute unit", "inch", "centimeter"
    };

    /** 7.7.3.7 scene illuminant value labels. */
    public static final String [] SCENE_ILLUMINANT = {
	"unidentified", "daylight", "fluorescent", "tungsten lamp",
	"flash", "standard illuminant A", "standard illuminat B",
	"standard illuminant C", "D55 illuminant", "D65 illuminant",
	"D75 illuminant"
    };
    /** Index for 7.7.3.7 scene illuminant value labels. */
    public static final int [] SCENE_ILLUMINANT_INDEX = {
	0, 1, 2, 3, 10, 17, 18, 19, 20, 21, 22
    };

    /** 6.1.5.1 segment type value labels. */
    public static final String [] SEGMENT_TYPE = {
	"strips", "tiles"
    };

    /** 7.8 sensor value labels. */
    public static final String [] SENSOR = {
	"Undefined", "MonochromeArea", "OneChipColorArea", "TwoChipColorArea",
	"ThreeChipColorArea", "ColorSequentialArea", "MonochromeLinear",
	"ColorTriLinear", "ColorSequentialLinear"
    };

    /** 8.1.7.1 (8.1.8.1) source dimension unit. */
    public static final String [] SOURCE_DIMENSION_UNIT = {
	"inches", "mm"
    };

    /** 6.1.4.4 YCbCr positioning value labels. */
    public static final String [] YCBCR_POSITIONING = {
	"", "centered", "cosited"
    };

    /** 8.3.1  TargetType. */
    public static final String [] TARGET_TYPE = {
	"external", "internal"
    };

    /** Undefined value. */
    public static final int NULL = -1;
    public static final double NILL = -1.0;

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     *
     * 6 Basic image parameters
     ******************************************************************/

    /** 6.1.1 MIME type */
    private String _mimeType;

    /** 6.1.2 Byte order */
    private String _byteOrder;

    /** 6.1.3.1 Compression scheme */
    private int _compressionScheme;
    /** 6.1.3.2 Compression level */
    private int _compressionLevel;

    /** 6.1.4.1 Color space */
    private int _colorSpace;

    /** 6.1.4.2.1 ICC profile name */
    private String _profileName;
    /** 6.1.4.2.2 ICC profile url */
    private String _profileURL;

    /** 6.1.4.3 YCbCr sub-sampling */
    private int [] _yCbCrSubSampling;
    /** 6.1.4.4 YCbCr positioning */
    private int _yCbCrPositioning;
    /** 6.1.4.5 YCbCr coefficients */
    private Rational [] _yCbCrCoefficients;
    /** 6.1.4.6 Reference black and white */
    private Rational [] _referenceBlackWhite;

    /** 6.1.5.1 Segment type */
    private int _segmentType;
    /** 6.1.5.2 Strip offsets */
    private long [] _stripOffsets;
    /** 6.1.5.3 Rows per strip */
    private long _rowsPerStrip;
    /** 6.1.5.4 Strip byte counts */
    private long [] _stripByteCounts;
    /** 6.1.5.5 Tile width */
    private long _tileWidth;
    /** 6.1.5.6 Tile length */
    private long _tileLength;
    /** 6.1.5.7 Tile offsets */
    private long [] _tileOffsets;
    /** 6.1.5.8 Tile byte counts */
    private long [] _tileByteCounts;

    /** 6.1.6 Planar configuration */
    private int _planarConfiguration;

    /** 6.2.1 Image identifier */
    private String _imageIdentifier;
    /** 6.2.1.1 Image identifier location */
    private String _imageIdentifierLocation;

    /** 6.2.2 File size */
    private long _fileSize;
    /** 6.2.3.1 Checksum method */
    private int _checksumMethod;
    /** 6.2.3.2 Checksum value */
    private String _checksumValue;

    /** 6.2.4 orientation */
    private int _orientation;

    /** 6.2.5 Display orientation */
    private int _displayOrientation;

    /** 6.2.6.1 X targeted display aspect ratio */
    private long _xTargetedDisplayAR;
    /** 6.2.6.2 Y targeted display aspect ratio */
    private long _yTargetedDisplayAR;

    /** 6.3 Preferred presentation */
    private String _preferredPresentation;

    /******************************************************************
     * 7 Image creation
     ******************************************************************/

    /** 7.1 Source type */
    private String _sourceType;

    /** 7.2 Source ID */
    private String _sourceID;

    /** 7.3 Image producer */
    private String _imageProducer;

    /** 7.4 Host computer */
    private String _hostComputer;
    /** 7.4.1 Operating system */
    private String _os;
    /** 7.4.2 OS version */
    private String _osVersion;

    /** 7.5 Device source */
    private String _deviceSource;

    /** 7.6.1.1 Scanner system manufacturer */
    private String _scannerManufacturer;
    /** 7.6.1.2.1 Scanner model name */
    private String _scannerModelName;
    /** 7.6.1.2.2 Scanner model number */
    private String _scannerModelNumber;
    /** 7.6.1.2.3 Scanner model serial number */
    private String _scannerModelSerialNo;
    /** 7.6.2.1 Scanning software */
    private String _scanningSoftware;
    /** 7.6.2.2 Scanning software version number */
    private String _scanningSoftwareVersionNo;

    /** 7.6.3 Pixel size (in meters) */
    private double _pixelSize;

    /** 7.6.3.2.1 X physical scan resolution */
    private double _xPhysScanResolution;
    /** 7.6.3.2.2 Y physical scan resolution */
    private double _yPhysScanResolution;

    /** 7.7.1 Digital camera manufacturer */
    private String _digitalCameraManufacturer;
    /** 7.7.2 Digital camera model */
    private String _digitalCameraModel;

    /** 7.7.3.1 F number */
    private double _fNumber;
    /** 7.7.3.2 Exposure time */
    private double _exposureTime;
    /** 7.7.3.3 Brightness */
    private double _brightness;
    /** 7.7.3.4 Exposure bias */
    private double _exposureBias;
    /** 7.7.3.5 Subject distance */
    private double [] _subjectDistance;
    /** 7.7.3.6 Metering mode */
    private int _meteringMode;
    /** 7.7.3.7 Scene illuminant */
    private int _sceneIlluminant;
    /** 7.7.3.8 Color temperature */
    private double _colorTemp;
    /** 7.7.3.9 Focal length (in meters) */
    private double _focalLength;
    /** 7.7.3.10 Flash */
    private int _flash;
    /** 7.7.3.11 Flash energy */
    private double _flashEnergy;
    /** 7.7.3.12 Flash return */
    private int _flashReturn;
    /** 7.7.3.13 Back light */
    private int _backLight;
    /** 7.7.3.14 Exposure index */
    private double _exposureIndex;
    /** 7.7.3.15 Auto focus */
    private int _autoFocus;
    /** 7.7.3.16.1 X print aspect ratio */
    private double _xPrintAspectRatio;
    /** 7.7.3.16.2 Y print aspect ratio */
    private double _yPrintAspectRatio;

    /** 7.8 Sensor */
    private int _sensor;

    /** 7.9 Date/time created */
    private String _dateTimeCreated;

    /** 7.10 Methodology */
    private String _methodology;

    /******************************************************************
     * Imaging performance assessment
     ******************************************************************/

    /** 8.1.1 Sampling frequency plane */
    private int _samplingFrequencyPlane;
    /** 8.1.2 Sampling frequency unit */
    private int _samplingFrequencyUnit;
    /** 8.1.3 X sampling frequency */
    private Rational _xSamplingFrequency;
    /** 8.1.4 Y sampling frequency */
    private Rational _ySamplingFrequency;
    /** 8.1.5 Image width */
    private long _imageWidth;
    /** 8.1.6 Image Length */
    private long _imageLength;
    /** 8.1.7 Source X dimension */
    private double _sourceXDimension;
    /** 8.1.8 Source X dimension unit */
    private int _sourceXDimensionUnit;
    /** 8.1.9 Source Y dimension */
    private double _sourceYDimension;
    /** 8.1.10 Source Y dimension unit */
    private int _sourceYDimensionUnit;

    /** 8.2.1 Bits per sample */
    private int [] _bitsPerSample;
    /** 8.2.2 Samples per pixel */
    private int _samplesPerPixel;
    /** 8.2.3 Extra samples */
    private int [] _extraSamples;

    /** 8.2.4.1 Colormap reference */
    private String _colormapReference;
    /** 8.2.4.2 Colormap bit code value */
    private int [] _colormapBitCodeValue;
    /** 8.2.4.3 Colormap red value */
    private int [] _colormapRedValue;
    /** 8.2.4.4 Colormap green value */
    private int [] _colormapGreenValue;
    /** 8.2.4.5 Colormap blue value */
    private int [] _colormapBlueValue;

    /** 8.2.5 Gray response curve */
    private int [] _grayResponseCurve;
    /** 8.2.6 Gray response unit */
    private int _grayResponseUnit;

    /** 8.2.7.1 Whitepoint X value */
    private Rational _whitePointXValue;
    /** 8.2.7.2 Whitepoint Y value */
    private Rational _whitePointYValue;

    /** 8.2.8.1 Primary chromaticities Red X */
    private Rational _primaryChromaticitiesRedX;
    /** 8.2.8.2 Primary chromaticities Red Y */
    private Rational _primaryChromaticitiesRedY;
    /** 8.2.8.3 Primary chromaticities Green X */
    private Rational _primaryChromaticitiesGreenX;
    /** 8.2.8.4 Primary chromaticities Green Y */
    private Rational _primaryChromaticitiesGreenY;
    /** 8.2.8.5 Primary chromaticities Blue X */
    private Rational _primaryChromaticitiesBlueX;
    /** 8.2.8.6 Primary chromaticities Blue Y */
    private Rational _primaryChromaticitiesBlueY;

    /* 8.3 Target data */
    /** 8.3.1  Target Type */
    private int _targetType;
    /** 8.3.2.1  TargetIDManufacturer */
    private String _targetIDManufacturer;
    /** 8.3.2.2  TargetIDName */
    private String _targetIDName;
    /** 8.3.2.3  TargetIDNo */
    private String _targetIDNo;
    /** 8.3.2.4  TargetIDMedia */
    private String _targetIDMedia;
    /** 8.3.3    ImageData */
    private String _imageData;
    /** 8.3.4    PerformanceData */
    private String _performanceData;
    /** 8.3.5    Profiles */
    private String _profiles;

    /* 9 Change history */
    /** 9.1.1  DateTimeProcessed */
    private String _dateTimeProcessed;
    /** 9.1.2  SourceData */
    private String _sourceData;
    /** 9.1.3  ProcessingAgency */
    private String _processingAgency;
    /** 9.1.4.1  ProcessingSoftwareName */
    private String _processingSoftwareName;
    /** 9.1.4.2  ProcessingSoftwareVersion */
    private String _processingSoftwareVersion;
    /** 9.1.5  ProcessingActions */
    private String[] _processingActions;

    /* 9.2  PreviousImageMetadata -- not currently supported */

    /* Data for Swing-based viewer. */
    private Property _viewerData;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate a <code>NisoImageMetadata</code> object.
     */
    public NisoImageMetadata ()
    {
	_autoFocus = NULL;
	_backLight = NULL;
	_brightness = NILL;
	_checksumMethod = NULL;
	_colorSpace = NULL;
	_colorTemp = NILL;
	_compressionLevel = NULL;
	_compressionScheme = NULL;
	_dateTimeProcessed = null;
	_displayOrientation = NULL;
	_exposureBias = NILL;
	_exposureIndex = NILL;
	_exposureTime = NILL;
	_fileSize = NULL;
	_flash = NULL;
	_flashEnergy = NILL;
	_flashReturn = NULL;
	_fNumber = NILL;
	_focalLength = NILL;
	_grayResponseUnit = NULL;
	_imageData = null;
	_imageLength = NULL;
	_imageWidth = NULL;
	_meteringMode = NULL;
	_orientation = NULL;
	_performanceData = null;
	_pixelSize = NILL;
	_planarConfiguration = NULL;
	_processingActions = null;
	_processingAgency = null;
	_processingSoftwareName = null;
	_processingSoftwareVersion = null;
        _profiles = null;
	_rowsPerStrip = NULL;
	_samplesPerPixel = NULL;
	_samplingFrequencyPlane = NULL;
	_samplingFrequencyUnit = NULL;
	_sceneIlluminant = NULL;
	_segmentType = NULL;
	_sensor = NULL;
	_sourceData = null;
	_sourceXDimension = NILL;
	_sourceXDimensionUnit = NULL;
	_sourceYDimension = NILL;
	_sourceYDimensionUnit = NULL;
	_tileLength = NULL;
	_tileWidth = NULL;
	_targetIDManufacturer = null;
	_targetIDMedia = null;
	_targetIDName = null;
	_targetIDNo = null;
	_targetType = NULL;
	_xPhysScanResolution = NILL;
	_xPrintAspectRatio = NILL;
	_xSamplingFrequency = null;
	_xTargetedDisplayAR = NULL;
	_yCbCrPositioning = NULL;
	_yPhysScanResolution = NILL;
	_yPrintAspectRatio = NILL;
	_ySamplingFrequency = null;
	_yTargetedDisplayAR = NULL;
	_viewerData = null;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     * 
     * Accessor methods.
     ******************************************************************/

    /** Get 7.7.3.15 auto focus. */
    public int getAutoFocus ()
    {
	return _autoFocus;
    }

    /** Get 7.7.3.13 back light. */
    public int getBackLight ()
    {
	return _backLight;
    }

    /** Get 8.2.1 bits per sample. */
    public int [] getBitsPerSample ()
    {
	return _bitsPerSample;
    }

    /** Get 7.7.3.3 Brightness. */
    public double getBrightness ()
    {
	return _brightness;
    }

    /** Get 6.1.2 byte order. */
    public String getByteOrder ()
    {
	return _byteOrder;
    }

    /** Get 6.2.3.1 Checksum method. */
    public int getChecksumMethod ()
    {
	return _checksumMethod;
    }

    /** Get 6.2.3.2 Checksum value. */
    public String getChecksumValue ()
    {
	return _checksumValue;
    }

    /** Get 8.2.4.2 colormap bit code value. */
    public int [] getColormapBitCodeValue ()
    {
	return _colormapBitCodeValue;
    }

    /** Get 8.2.4.5 colormap blue value. */
    public int [] getColormapBlueValue ()
    {
	return _colormapBlueValue;
    }

    /** Get 8.2.4.4 colormap green value. */
    public int [] getColormapGreenValue ()
    {
	return _colormapGreenValue;
    }

    /** Get 8.2.4.3 colormap red value. */
    public int [] getColormapRedValue ()
    {
	return _colormapRedValue;
    }

    /** Get 8.2.4.1 colormap reference. */
    public String getColormapReference ()
    {
	return _colormapReference;
    }

    /** Get 6.1.4.1 color space. */
    public int getColorSpace ()
    {
	return _colorSpace;
    }

    /** Get 7.7.3.8 color temperature. */
    public double getColorTemp ()
    {
	return _colorTemp;
    }

    /** Get 6.1.3.2 compression level. */
    public int getCompressionLevel ()
    {
	return _compressionLevel;
    }

    /** Get 6.1.3.1 compression scheme. */
    public int getCompressionScheme ()
    {
	return _compressionScheme;
    }

    /** Get 7.9 date/time created. */
    public String getDateTimeCreated ()
    {
	return _dateTimeCreated;
    }

    /** Get 9.1.1  DateTimeProcessed */
    public String getDateTimeProcessed ()
    {
	return _dateTimeProcessed;
    }

    /** Get 7.5 device source. */
    public String getDeviceSource ()
    {
	return _deviceSource;
    }

    /** Get 7.7.1 digital camera manufacturer. */
    public String getDigitalCameraManufacturer ()
    {
	return _digitalCameraManufacturer;
    }

    /** Get 7.7.2 digital camera model. */
    public String getDigitalCameraModel ()
    {
	return _digitalCameraModel;
    }

    /** Get 6.2.5 Display orientation. */
    public int getDisplayOrientation ()
    {
	return _displayOrientation;
    }

    /** Get 7.7.3.4 exposure bias. */
    public double getExposureBias ()
    {
	return _exposureBias;
    }

    /** Get 7.7.3.14 exposure index. */
    public double getExposureIndex ()
    {
	return _exposureIndex;
    }

    /** Get 7.7.3.2 exposure time. */
    public double getExposureTime ()
    {
	return _exposureTime;
    }

    /** Get 8.2.3 extra samples. */
    public int [] getExtraSamples ()
    {
	return _extraSamples;
    }

    /** Get 6.2.2 file size. */
    public long getFileSize ()
    {
	return _fileSize;
    }

    /** Get 7.7.3.10 flash. */
    public int getFlash ()
    {
	return _flash;
    }

    /** Get 7.7.3.11 flash energy. */
    public double getFlashEnergy ()
    {
	return _flashEnergy;
    }

    /** Get 7.7.3.12 flash return. */
    public int getFlashReturn ()
    {
	return _flashReturn;
    }

    /** Get 7.7.3.1 F number. */
    public double getFNumber ()
    {
	return _fNumber;
    }

    /** Get 7.7.3.9 focal length. */
    public double getFocalLength ()
    {
	return _focalLength;
    }

    /** Get 8.2.5 gray response curve. */
    public int [] getGrayResponseCurve ()
    {
	return _grayResponseCurve;
    }

    /** Get 8.2.6 gray response unit. */
    public int getGrayResponseUnit ()
    {
	return _grayResponseUnit;
    }

    /** Get 7.4 host computer. */
    public String getHostComputer ()
    {
	return _hostComputer;
    }

    /** Get 8.3.3    ImageData */
    public String getImageData ()
    {
	return _imageData;
    }

    /** Get 6.2.1 Image identifier. */
    public String getImageIdentifier ()
    {
	return _imageIdentifier;
    }

    /** Get 6.2.1.1 Image identifier location. */
    public String getImageIdentifierLocation ()
    {
	return _imageIdentifierLocation;
    }

    /** Get 8.1.6 image length. */
    public long getImageLength ()
    {
	return _imageLength;
    }

    /** Get 7.3 Image producer. */
    public String getImageProducer ()
    {
	return _imageProducer;
    }

    /** Get 8.1.5 image width. */
    public long getImageWidth ()
    {
	return _imageWidth;
    }

    /** Get 7.7.3.6 metering mode. */
    public int getMeteringMode ()
    {
	return _meteringMode;
    }

    /** Get 7.10 methodology. */
    public String getMethodology ()
    {
	return _methodology;
    }

    /** Get 6.1.1 MIME type. */
    public String getMimeType ()
    {
	return _mimeType;
    }

    /** Get 6.2.4 Orientation. */
    public int getOrientation ()
    {
	return _orientation;
    }

    /** Get 7.4.1 OS (operating system). */
    public String getOS ()
    {
	return _os;
    }

    /** Get 7.4.2 OS version. */
    public String getOSVersion ()
    {
	return _osVersion;
    }

    /** Get 8.3.4    PerformanceData. */
    public String getPerformanceData ()
    {
	return _performanceData;
    }

    /** Get 7.6.3.1 pixel size. */
    public double getPixelSize ()
    {
	return _pixelSize;
    }

    /** Get 6.1.6 Planar configuration. */
    public int getPlanarConfiguration ()
    {
	return _planarConfiguration;
    }

    /** Get 6.3 preferred presentation. */
    public String getPreferredPresentation ()
    {
	return _preferredPresentation;
    }

    /** Get 8.2.8.5 primary chromaticities blue X. */
    public Rational getPrimaryChromaticitiesBlueX ()
    {
	return _primaryChromaticitiesBlueX;
    }

    /** Get 8.2.8.6 primary chromaticities blue Y. */
    public Rational getPrimaryChromaticitiesBlueY ()
    {
	return _primaryChromaticitiesBlueY;
    }

    /** Get 8.2.8.3 primary chromaticities green X. */
    public Rational getPrimaryChromaticitiesGreenX ()
    {
	return _primaryChromaticitiesGreenX;
    }

    /** Get 8.2.8.4 primary chromaticities green Y. */
    public Rational getPrimaryChromaticitiesGreenY ()
    {
	return _primaryChromaticitiesGreenY;
    }

    /** Get 8.2.8.1 primary chromaticities red X. */
    public Rational getPrimaryChromaticitiesRedX ()
    {
	return _primaryChromaticitiesRedX;
    }

    /** Get 8.2.8.2 primary chromaticities red Y. */
    public Rational getPrimaryChromaticitiesRedY ()
    {
	return _primaryChromaticitiesRedY;
    }

    /** Get 9.1.5 ProcessingActions. */
    public String[] getProcessingActions ()
    {
	return _processingActions;
    }

    /** Get 9.1.3  ProcessingAgency. */
    public String getProcessingAgency ()
    {
	return _processingAgency;
    }

    /** Get 9.1.4.1  ProcessingSoftwareName */
    public String getProcessingSoftwareName ()
    {
	return _processingSoftwareName;
    }

    /** Get 9.1.4.2  ProcessingSoftwareVersion */
    public String getProcessingSoftwareVersion ()
    {
        return  _processingSoftwareVersion;
    }

    /** Get 6.1.4.2.1 ICC profile name. */
    public String getProfileName ()
    {
	return _profileName;
    }

    /** Get 8.3.5    Profiles */
    public String getProfiles ()
    {
	return _profiles;
    }

    /** Get 6.1.4.2.2 ICC profile URL. */
    public String getProfileURL ()
    {
	return _profileURL;
    }

    /** Get 6.1.4.6 Reference black and white. */
    public Rational [] getReferenceBlackWhite ()
    {
	return _referenceBlackWhite;
    }

    /** Get 6.1.5.3 Rows per strip. */
    public long getRowsPerStrip ()
    {
	return _rowsPerStrip;
    }

    /** Get 8.2.2 samples per pixel. */
    public int getSamplesPerPixel ()
    {
	return _samplesPerPixel;
    }

    /** Get 8.1.1 sampling frequency plane. */
    public int getSamplingFrequencyPlane ()
    {
	return _samplingFrequencyPlane;
    }

    /** Get 8.1.2 sampling frequency unit. */
    public int getSamplingFrequencyUnit ()
    {
	return _samplingFrequencyUnit;
    }

    /** Get 7.6.1.1 scanner manufacturer. */
    public String getScannerManufacturer ()
    {
	return _scannerManufacturer;
    }

    /** Get 7.6.1.2.1 scanner model name. */
    public String getScannerModelName ()
    {
	return _scannerModelName;
    }

    /** Get 7.6.1.2.2 scanner model number. */
    public String getScannerModelNumber ()
    {
	return _scannerModelNumber;
    }

    /** Get 7.6.1.2.3 scanner model serial number. */
    public String getScannerModelSerialNo ()
    {
	return _scannerModelSerialNo;
    }

    /** Get 7.6.2.1 scanning software. */
    public String getScanningSoftware ()
    {
	return _scanningSoftware;
    }

    /** Get 7.6.2.2 scanning software version number. */
    public String getScanningSoftwareVersionNo ()
    {
	return _scanningSoftwareVersionNo;
    }

    /** Get 7.7.3.7 scene illuminant. */
    public int getSceneIlluminant ()
    {
	return _sceneIlluminant;
    }

    /** Get 6.1.5.1 segment type. */
    public int getSegmentType ()
    {
	return _segmentType;
    }

    /** Get 7.8 sensor. */
    public int getSensor ()
    {
	return _sensor;
    }

    /** Get 9.1.2  SourceData. */
    public String getSourceData ()
    {
	return _sourceData;
    }

    /** Get 7.2 source ID. */
    public String getSourceID ()
    {
	return _sourceID;
    }

    /** Get 7.1 Source type. */
    public String getSourceType ()
    {
	return _sourceType;
    }

    public double getSourceXDimension ()
    {
	return _sourceXDimension;
    }

    public int getSourceXDimensionUnit ()
    {
	return _sourceXDimensionUnit;
    }

    public double getSourceYDimension ()
    {
	return _sourceYDimension;
    }

    public int getSourceYDimensionUnit ()
    {
	return _sourceYDimensionUnit;
    }

    /** Get 6.1.5.4 Strip byte counts. */
    public long [] getStripByteCounts ()
    {
	return _stripByteCounts;
    }

    /** Get 6.1.5.2 Strip offsets. */
    public long [] getStripOffsets ()
    {
	return _stripOffsets;
    }

    /** Get 7.7.3.5 Subject distance. */
    public double [] getSubjectDistance ()
    {
	return _subjectDistance;
    }

    /** Get 8.3.2.1  TargetIDManufacturer */
    public String getTargetIDManufacturer ()
    {
	return _targetIDManufacturer;
    }

    /** Get 8.3.2.3  TargetIDMedia */
    public String getTargetIDMedia ()
    {
	return _targetIDMedia;
    }

    /** Get 8.3.2.2  TargetIDName */
    public String getTargetIDName ()
    {
	return _targetIDName;
    }

    /** Get 8.3.2.3  TargetIDNo */
    public String getTargetIDNo ()
    {
	return _targetIDNo;
    }

    /** Get 8.3.1  Target Type */
    public int getTargetType ()
    {
	return _targetType;
    }

    /** Get 6.1.5.8 Tile byte counts. */
    public long [] getTileByteCounts ()
    {
	return _tileByteCounts;
    }

    /** Get 6.1.5.6 Tile length. */
    public long getTileLength ()
    {
	return _tileLength;
    }

    /** Get 6.1.5.7 Tile offsets. */
    public long [] getTileOffsets ()
    {
	return _tileOffsets;
    }

    /** Get 6.1.5.5 Tile width. */
    public long getTileWidth ()
    {
	return _tileWidth;
    }

    /** Get 8.2.7.1 white point X value. */
    public Rational getWhitePointXValue ()
    {
	return _whitePointXValue;
    }

    /** Get 8.2.7.2 white point Y value. */
    public Rational getWhitePointYValue ()
    {
	return _whitePointYValue;
    }

    /** Get 7.7.3.16.1 X print aspect ratio. */
    public double getXPrintAspectRatio ()
    {
	return _xPrintAspectRatio;
    }

    /** Get 7.6.3.2.1 X physcal scanning resolution. */
    public double getXPhysScanResolution ()
    {
	return _xPhysScanResolution;
    }

    /** Get 8.1.3 X sampling frequency. */
    public Rational getXSamplingFrequency ()
    {
	return _xSamplingFrequency;
    }

    /** Get 6.2.6 X targeted display aspect ratio. */
    public long getXTargetedDisplayAR ()
    {
	return _xTargetedDisplayAR;
    }

    /** Get 6.1.4.5 YCbCr coefficients. */
    public Rational [] getYCbCrCoefficients ()
    {
	return _yCbCrCoefficients;
    }

    /** Get 6.1.4.4 YCbCr positioning. */
    public int getYCbCrPositioning ()
    {
	return _yCbCrPositioning;
    }

    /** Get 6.1.4.3 YCbCr subsampling. */
    public int [] getYCbCrSubSampling ()
    {
	return _yCbCrSubSampling;
    }

    /** Get 7.6.3.2.2 Y physcal scanning resolution. */
    public double getYPhysScanResolution ()
    {
	return _yPhysScanResolution;
    }

    /** Get 7.7.3.16.2 Y print aspect ratio. */
    public double getYPrintAspectRatio ()
    {
	return _yPrintAspectRatio;
    }

    /** Get 8.1.4 Y sampling frequency. */
    public Rational getYSamplingFrequency ()
    {
	return _ySamplingFrequency;
    }

    /** Get 6.2.7 Y targeted display aspect ratio. */
    public long getYTargetedDisplayAR ()
    {
	return _yTargetedDisplayAR;
    }

    /** Get data for Swing GUI viewer. */
    public Property getViewerData ()
    {
	return _viewerData;
    }


    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /** Set 7.7.3.15 auto focus.
     * @param focus Auto focus
     */
    public void setAutoFocus (int focus)
    {
	_autoFocus = focus;
    }

    /** Set 7.7.3.13 back light.
     * @param light Back light
     */
    public void setBackLight (int light)
    {
	_backLight = light;
    }

    /** Set 8.2.1 bits per sample.
     * @param bits Bits per sample
     */
    public void setBitsPerSample (int [] bits)
    {
	_bitsPerSample = bits;
    }

    /** Set 7.7.3.3 brightness.
     * @param brightness Brightness
     */
    public void setBrightness (double brightness)
    {
	_brightness = brightness;
    }

    /** Set 6.1.2 byte order.
     * @param order Byte order
     */
    public void setByteOrder (String order)
    {
	_byteOrder = order;
    }

    /** Set 8.2.4.2 colormap bit code value.
     * @param value Bit code value
     */
    public void setColormapBitCodeValue (int [] value)
    {
	_colormapBitCodeValue = value;
    }

    /** Set 8.2.4.4 colormap blue value.
     * @param value Blue value
     */
    public void setColormapBlueValue (int [] value)
    {
	_colormapBlueValue = value;
    }

    /** Set 8.2.4.3 colormap green value.
     * @param value Green value
     */
    public void setColormapGreenValue (int [] value)
    {
	_colormapGreenValue = value;
    }

    /** Set 8.2.4.2 colormap red value.
     * @param value Red value
     */
    public void setColormapRedValue (int [] value)
    {
	_colormapRedValue = value;
    }

    /** Set 8.2.4.1 colormap reference.
     * @param reference Colormap reference
     */
    public void setColormapReference (String reference)
    {
	_colormapReference = reference;
    }

    /** Set 6.1.4.1 color space
    * @param space Color space
    */
    public void setColorSpace (int space)
    {
	_colorSpace = space;
    }

    /** Set 7.7.3.8 color temperature.
     * @param temp Color temperature
     */
    public void setColorTemp (double temp)
    {
	_colorTemp = temp;
    }

    /** Set 6.1.3.2 compression level.
     * @param level Compression level
     */
    public void setCompressionLevel (int level)
    {
	_compressionLevel = level;
    }

    /** Set 6.1.3.1 compression scheme.
     * @param scheme Compression scheme
     */
    public void setCompressionScheme (int scheme)
    {
	_compressionScheme = scheme;
    }

    /** Set 7.9 date/time created.
     *  TIFF dates get converted to ISO 8601 format.
     * @param date Date/time created
     */
    public void setDateTimeCreated (String date)
    {
	_dateTimeCreated = make8601Valid (date);
    }

    /** Set 9.1.1  DateTimeProcessed.
     *  TIFF dates get converted to ISO 8601 format.
     * @param date Date/time processed
     */
    public void setDateTimeProcessed (String date)
    {
    	_dateTimeProcessed = make8601Valid (date);
    }

    /** Set 7.5 Device source.
     * @param source Device source
     */
    public void setDeviceSource (String source)
    {
	_deviceSource = source;
    }

    /** Set 7.7.1 digital camera manufacturer.
     * @param manufacturer Camera manufacturer
     */
    public void setDigitalCameraManufacturer (String manufacturer)
    {
	_digitalCameraManufacturer = manufacturer;
    }

    /** Set 7.7.2 digital camera model.
     * @param model Camera model
     */
    public void setDigitalCameraModel (String model)
    {
	_digitalCameraModel = model;
    }

    /** Set 6.2.5 display orientation.
     * @param orientation Display orientation
     */
    public void setDisplayOrientation (int orientation)
    {
	_displayOrientation = orientation;
    }

    /** Set 7.2.3.4 exposure bias.
     * @param bias Exposure bias
     */
    public void setExposureBias (double bias)
    {
	_exposureBias = bias;
    }

    /** Set 7.2.3.14 exposure index.
     * @param index Exposure index
     */
    public void setExposureIndex (double index)
    {
	_exposureIndex = index;
    }

    /** Set 7.7.3.2 exposure time.
     * @param time Exposure time
     */
    public void setExposureTime (double time)
    {
	_exposureTime = time;
    }

    /** Set 8.2.3 extra samples.
     * @param extra Extra samples
     */
    public void setExtraSamples (int [] extra)
    {
	_extraSamples = extra;
    }	    

    /** Set 6.2.2 file size.
     * @param size File size
     */
    public void setFileSize (long size)
    {
	_fileSize = size;
    }

    /** Set 7.7.3.1 F number.
     * @param f F number
     */
    public void setFNumber (double f)
    {
	_fNumber = f;
    }

    /** Set 7.7.3.11 flash energy.
     * @param energy Flash energy
     */
    public void setFlashEnergy (double energy)
    {
	_flashEnergy = energy;
    }

    /** Set 7.7.3.12 flash return.
     * @param ret Flash return
     */
    public void setFlashReturn (int ret)
    {
	_flashReturn = ret;
    }

    /** Set 7.7.3.10 flash.
     * @param flash Flash
     */
    public void setFlash (int flash)
    {
	_flash = flash;
    }

    /** Set 7.7.3.9 focal length (double meters).
     * @param length Focal length
     */
    public void setFocalLength (double length)
    {
	_focalLength = length;
    }

    /** Set 8.2.5 gray response curve.
     * @param curve Gray response curve
     */
    public void setGrayResponseCurve (int [] curve)
    {
	_grayResponseCurve = curve;
    }

    /** Set 8.2.6 gray response unit.
     * @param unit Gray response unit
     */
    public void setGrayResponseUnit (int unit)
    {
	_grayResponseUnit = unit;
    }

    /** Set 7.4 host computer.
     * @param computer Host computer
     */
    public void setHostComputer (String computer)
    {
	_hostComputer = computer;
    }

    /** Set 8.3.3    ImageData.
     * @param imageData Image Data filename or URN
     */
    public void setImageData (String imageData)
    {
	_imageData = imageData;
    }

    /** Set 6.2.1 Image identifier.
     * @param identifier Image identifier
     */
    public void setImageIdentifier (String identifier)
    {
	_imageIdentifier = identifier;
    }

    /** Set 6.2.1 Image identifier location.
     * @param location identifier location
     */
    public void setImageIdentifierLocation (String location)
    {
	_imageIdentifierLocation = location;
    }

    /** Set 8.1.6 image length.
     * @param length Image length
     */
    public void setImageLength (long length)
    {
	_imageLength = length;
    }

    /** Set 7.3 image producer.
     * @param producer Image producer
     */
    public void setImageProducer (String producer)
    {
	_imageProducer = producer;
    }

    /** Set 8.1.5 image width.
     * @param width Image width
     */
    public void setImageWidth (long width)
    {
	_imageWidth = width;
    }

    /** Set 7.7.3.6 metering mode.
     * @param mode Metering mode
     */
    public void setMeteringMode (int mode)
    {
	_meteringMode = mode;
    }

    /** Set 7.10 methodology.
     * @param methodology Methodology
     */
    public void setMethodology (String methodology)
    {
	_methodology = methodology;
    }

    /** Set 6.1.1 MIME type.
     * @param type MIME type
     */
    public void setMimeType (String type)
    {
	_mimeType = type;
    }

    /** Set 6.2.4  orientation.
     * @param orientation Orientation
     */
    public void setOrientation (int orientation)
    {
	_orientation = orientation;
    }

    /* Set 7.4.1 OS (operating system).
     * @param os Operating system
     */
    public void setOS (String os)
    {
	_os = os;
    }

    /** Set 7.4.2 OS version.
     * @param version OS version
     */
    public void setOSVersion (String version)
    {
	_osVersion = version;
    }

    /** Set 8.3.4    PerformanceData.
     * @param  performanceData	Performance data filename or URN
     */
    public void setPerformanceData (String performanceData)
    {
	_performanceData = performanceData;
    }

    /** Set 7.6.3.1 pixel size.
     * @param size Pixel size
     */
    public void setPixelSize (double size)
    {
	_pixelSize = size;
    }

    /** Set 6.1.6 Planar configuration.
     * @param configuration Planar configuration
     */
    public void setPlanarConfiguration (int configuration)
    {
	_planarConfiguration = configuration;
    }

    /** Set 6.3 preferred presentation.
     * @param presentation Preferred presentation
     */
    public void setPreferredPresentation (String presentation)
    {
	_preferredPresentation = presentation;
    }

    /** Set 8.2.8.5 primary chromaticities blue X.
     * @param x Blue x
     */
    public void setPrimaryChromaticitiesBlueX (Rational x)
    {
	_primaryChromaticitiesBlueX = x;
    }

    /** Set 8.2.8.6 primary chromaticities blue Y.
     * @param y Blue y
     */
    public void setPrimaryChromaticitiesBlueY (Rational y)
    {
	_primaryChromaticitiesBlueY = y;
    }

    /** Set 8.2.8.3 primary chromaticities green X.
     * @param x Green x
     */
    public void setPrimaryChromaticitiesGreenX (Rational x)
    {
	_primaryChromaticitiesGreenX = x;
    }

    /** Set 8.2.8.4 primary chromaticities green Y.
     * @param y Green y
     */
    public void setPrimaryChromaticitiesGreenY (Rational y)
    {
	_primaryChromaticitiesGreenY = y;
    }

    /** Set 8.2.8.1 primary chromaticities red X.
     * @param x Red x
     */
    public void setPrimaryChromaticitiesRedX (Rational x)
    {
	_primaryChromaticitiesRedX = x;
    }

    /** Set 8.2.8.2 primary chromaticities red Y.
     * @param y Red y
     */
    public void setPrimaryChromaticitiesRedY (Rational y)
    {
	_primaryChromaticitiesRedY = y;
    }

    /** Set 9.1.5  ProcessingActions.
     *  @param actions  Array of strings giving image processing steps
     */
    public void setProcessingActions (String[] actions)
    {
	_processingActions = actions;
    }

    /** Set 9.1.3  ProcessingAgency.
     * @param processingAgency  Identifier of producing organization
     */
    public void setProcessingAgency (String processingAgency)
    {
	_processingAgency = processingAgency;
    }

    /** Set 9.1.4.1  ProcessingSoftwareName
     *  @param name  Name of the image processing software
     */
    public void setProcessingSoftwareName (String name)
    {
         _processingSoftwareName = name;
    }

    /** Set 9.1.4.2  ProcessingSoftwareVersion 
     *  @param version  Version number of the processing software 
     */
    public void setProcessingSoftwareVersion (String version)
    {
    	_processingSoftwareVersion = version;
    }

    /** Set 6.1.4.1 ICC profile name.
     * @param name Profile name
     */
    public void setProfileName (String name)
    {
	_profileName = name;
    }

    /** Set 8.3.5    Profiles.
     *  @param profiles  Color profile filename or URN
     */
    public void setProfiles (String profiles)
    {
	_profiles = profiles;
    }

    /** Set 6.1.4.2 ICC profile URL.
     * @param URL Profile URL
     */
    public void setProfileURL (String URL)
    {
	_profileURL = URL;
    }

    /** Set 6.1.4.6 reference black and white.
     * @param reference Reference
     */
    public void setReferenceBlackWhite (Rational [] reference)
    {
	_referenceBlackWhite = reference;
    }

    /** Set 6.1.5.3 Rows per strip.
     * @param rows Rows per strip
     */
    public void setRowsPerStrip (long rows)
    {
	_rowsPerStrip = rows;
    }

    /** Set 8.1.1 sampling frequency plane.
     * @param plane Sampling frequency plane
     */
    public void setSamplingFrequencyPlane (int plane)
    {
	_samplingFrequencyPlane = plane;
    }

    /** Set 8.2.2 samples per pixel.
     * @param samples Samples per pixel
     */
    public void setSamplesPerPixel (int samples)
    {
	_samplesPerPixel = samples;
    }

    /** Set 8.1.2 sampling frequency unit.
     * @param unit Sampling frequency unit
     */
    public void setSamplingFrequencyUnit (int unit)
    {
	_samplingFrequencyUnit = unit;
    }

    /** Set 7.6.1.1 scanner manufacturer.
     * @param manufacturer Scanner manufacturer
     */
    public void setScannerManufacturer (String manufacturer)
    {
	_scannerManufacturer = manufacturer;
    }

    /** Set 7.6.1.2.1 scanner model name.
     * @param name Scanner model name
     */
    public void setScannerModelName (String name)
    {
	_scannerModelName = name;
    }

    /** Set 7.6.1.2.2 scanner model number.
     * @param number Scanner model number
     */
    public void setScannerModelNumber (String number)
    {
	_scannerModelNumber = number;
    }

    /** Set 7.6.1.2.3 scanner model serial number.
     * @param number Scanner model serial number
     */
    public void setScannerModelSerialNo (String number)
    {
	_scannerModelSerialNo = number;
    }

    /** Set 7.6.2.1 scanning software.
     * @param software Scanning software
     */
    public void setScanningSoftware (String software)
    {
	_scanningSoftware = software;
    }

    /** Set 7.6.2.2 scanning software version number.
     * @param number Scanning software version number
     */
    public void setScanningSoftwareVersionNo (String number)
    {
	_scanningSoftwareVersionNo = number;
    }

    /** Set 7.7.3.7 scene illuminant.
     * @param illuminant Scene illuminant
     */
    public void setSceneIlluminant (int illuminant)
    {
	_sceneIlluminant = illuminant;
    }

    /** Set 7.8 sensor.
     * @param sensor Sensor
     */
    public void setSensor (int sensor)
    {
	_sensor = sensor;
    }

    /** Set 9.1.2  SourceData.
     * @param sourceData  Source data identifier
     */
    public void setSourceData (String sourceData)
    {
	_sourceData = sourceData;
    }

    /** Set 7.2 source ID.
     * @param id Source ID
     */
    public void setSourceID (String id)
    {
	_sourceID = id;
    }

    /** Set 7.1 source type.
     * @param type Source type
     */
    public void setSourceType (String type)
    {
	_sourceType = type;
    }

    /** Set 8.1.7 source X dimension.
     * @param x   X dimension
     */
    public void setSourceXDimension (double x)
    {
	_sourceXDimension = x;
    }

    /** Set 8.1.7.1 source X dimension unit.
     * @param unit X dimension unit
     */
    public void setSourceXDimensionUnit (int unit)
    {
	_sourceXDimensionUnit = unit;
    }

    /** Set 8.1.8 source Y dimension.
     * @param y   Y dimension
     */
    public void setSourceYDimension (double y)
    {
	_sourceYDimension = y;
    }

    /** Set 8.1.8.1 source Y dimension unit.
     * @param unit Y dimension unit
     */
    public void setSourceYDimensionUnit (int unit)
    {
	_sourceYDimensionUnit = unit;
    }

    /** Set 6.1.5.4 Strip byte counts.
     * @param counts Byte counts
     */
    public void setStripByteCounts (long [] counts)
    {
	_stripByteCounts = counts;
    }

    /** Set 6.1.5.2 Strip offsets.
     * @param offsets Strip offsets
     */
    public void setStripOffsets (long [] offsets)
    {
	_stripOffsets = offsets;
    }

    /** Set 7.7.3.5 Subject distance
     * @param distance Subject distance
     */
    public void setSubjectDistance (double [] distance)
    {
	_subjectDistance = distance;
    }

    /** Set 8.3.2.1 TargetIDManufacturer */
    public void setTargetIDManufacturer (String targetIDManufacturer)
    {
	_targetIDManufacturer = targetIDManufacturer;
    }

    /** Set 8.3.2.4 TargetIDMedia */
    public void setTargetIDMedia (String targetIDMedia)
    {
	_targetIDMedia = targetIDMedia;
    }

    /** Set 8.3.2.2 TargetIDName */
    public void setTargetIDName (String targetIDName)
    {
	_targetIDName = targetIDName;
    }

    /** Set 8.3.2.3 TargetIDNo */
    public void setTargetIDNo (String targetIDNo)
    {
	_targetIDNo = targetIDNo;
    }

    /** Set 8.3.1  TargetType */
    public void setTargetType (int targetType)
    {
	_targetType = targetType;
    }

    /** Set 6.1.5.8 Tile byte counts.
     * @param counts Byte counts
     */
    public void setTileByteCounts (long [] counts)
    {
	_tileByteCounts = counts;
    }

    /** Set 6.1.5.6 Tile length.
     * @param length Tile length
     */
    public void setTileLength (long length)
    {
	_tileLength = length;
    }

    /** Set 6.1.5.7 Tile offsets. 
     * @param offsets tile offsets
     */
    public void setTileOffsets (long [] offsets)
    {
	_tileOffsets = offsets;
    }

    /** Set 6.1.5.5 Tile width.
     * @param width Tile width
     */
    public void setTileWidth (long width)
    {
	_tileWidth = width;
    }

    /** Set 8.2.7.1 white point X value.
     * @param x White point X
     */
    public void setWhitePointXValue (Rational x)
    {
	_whitePointXValue = x;
    }

    /** Set 8.2.7.2 white point Y value.
     * @param y White point Y
     */
    public void setWhitePointYValue (Rational y)
    {
	_whitePointYValue = y;
    }

    /** Set 7.6.3.2.1 X physical scanning resolution.
     * @param x X physical scanning resolution
     */
    public void setXPhysScanResolution (double x)
    {
	_xPhysScanResolution = x;
    }

    /** Set 7.7.3.16.1 X print aspect ratio.
     * @param x X aspect ratio
     */
    public void setXPrintAspectRatio (double x)
    {
	_xPrintAspectRatio = x;
    }

    /** Set 8.1.3 X sampling frequency.
     * @param x X sampling frequency
     */
    public void setXSamplingFrequency (Rational x)
    {
	_xSamplingFrequency = x;
    }

    /** Set 6.2.6.1 X targeted display aspect ratio.
     * @param x X units
     */
    public void setXTargetedDisplayAspectRatio (long x)
    {
	_xTargetedDisplayAR = x;
    }

    /** Set 6.1.4.5 YCbCr coefficients.
     * @param coefficients Coefficients
     */
    public void setYCbCrCoefficients (Rational [] coefficients)
    {
	_yCbCrCoefficients = coefficients;
    }

    /** Set 6.1.4.4 YCbCr positioning.
     * @param positioning Positioning
     */
    public void setYCbCrPositioning (int positioning)
    {
	_yCbCrPositioning = positioning;
    }

    /** Set 6.1.4.3 YCbCr Sub-sampling.
     * @param sampling Sub-sampling
     */
    public void setYCbCrSubSampling (int [] sampling)
    {
	_yCbCrSubSampling = sampling;
    }

    /** Set 7.6.3.2.2 Y physical scanning resolution.
     * @param y Y physical scanning resolution
     */
    public void setYPhysScanResolution (double y)
    {
	_yPhysScanResolution = y;
    }

    /** Set 7.7.3.16.2 Y print aspect ratio.
     * @param y Y aspect ratio
     */
    public void setYPrintAspectRatio (double y)
    {
	_yPrintAspectRatio = y;
    }

    /** Set 8.1.4 Y sampling frequency.
     * @param y Y sampling frequency
     */
    public void setYSamplingFrequency (Rational y)
    {
	_ySamplingFrequency = y;
    }

    /** Set 6.2.6.2 Y targeted display aspect ratio.
     * @param y Y units
     */
    public void setYTargetedDisplayAspectRatio (long y)
    {
	_yTargetedDisplayAR = y;
    }

    /** Set information for Swing GUI viewer. 
     *  @param viewerData  Private data for RepTreeModel
     */
    public void setViewerData (Property viewerData)
    {
	_viewerData = viewerData;
    }

    /*  Canonicizes (canonizes? whatever) a date to ISO
     *  8601 format.  Returns null if it can't make sense of
     *  it.  Returns the date unchanged if it's already
     *  canonical. Initially this converts TIFF dates to ISO.
     */
    private String make8601Valid (String date)
    {
        try {
            if (date.charAt (4) == ':') {
                // It's a TIFF date, or a good imitation of one.
                // TIFF dates have exact offsets, making things easy.
                String yr = date.substring (0, 4);
                String mo = date.substring (5, 7);
                String da = date.substring (8, 10);
                String hr = date.substring (11, 13);
                String mi = date.substring (14, 16);
                String se = date.substring (17, 19);
                return yr + "-" + mo + "-" + da + "T" +
                    hr + ":" + mi + ":" + se;
            }
            return date;  // default
        }
        catch (Exception e) {
            // Malformed date
            return null;
        }
    }
}
