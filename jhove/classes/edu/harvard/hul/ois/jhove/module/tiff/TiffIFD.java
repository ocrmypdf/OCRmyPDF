/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;
import org.xml.sax.XMLReader;
import org.xml.sax.SAXException;
import javax.xml.parsers.SAXParserFactory;

/**
 * Encapsulation of standard TIFF IFD.
 */
public class TiffIFD
    extends IFD
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** Standard TIFF 6.0 tags. */
    public static final int
        NEWSUBFILETYPE = 254,
        SUBFILETYPE = 255,
        IMAGEWIDTH = 256,
        IMAGELENGTH = 257,
        BITSPERSAMPLE = 258,
        COMPRESSION = 259,
        PHOTOMETRICINTERPRETATION = 262,
        THRESHHOLDING = 263,
        CELLWIDTH = 264,
        CELLLENGTH = 265,
        FILLORDER = 266,
        DOCUMENTNAME = 269,
        IMAGEDESCRIPTION = 270,
        MAKE = 271,
        MODEL = 272,
        STRIPOFFSETS = 273,
        ORIENTATION = 274,
        SAMPLESPERPIXEL = 277,
        ROWSPERSTRIP = 278,
        STRIPBYTECOUNTS = 279,
        MINSAMPLEVALUE = 280,
        MAXSAMPLEVALUE = 281,
        XRESOLUTION = 282,
        YRESOLUTION = 283,
        PLANARCONFIGURATION = 284,
        PAGENAME = 285,
        XPOSITION = 286,
        YPOSITION = 287,
        FREEOFFSETS = 288,
        FREEBYTECOUNTS = 289,
        GRAYRESPONSEUNIT = 290,
        GRAYRESPONSECURVE = 291,
        T4OPTIONS = 292,
        T6OPTIONS = 293,
        RESOLUTIONUNIT = 296,
        PAGENUMBER = 297,
        TRANSFERFUNCTION = 301,
        SOFTWARE = 305,
        DATETIME = 306,
        ARTIST = 315,
        HOSTCOMPUTER = 316,
        PREDICTOR = 317,
        WHITEPOINT = 318,
        PRIMARYCHROMATICITIES = 319,
        COLORMAP = 320,
        HALFTONEHINTS = 321,
        TILEWIDTH = 322,
        TILELENGTH = 323,
        TILEOFFSETS = 324,
        TILEBYTECOUNTS = 325,
        INKSET = 332,
        INKNAMES = 333,
        NUMBEROFINKS = 334,
        DOTRANGE = 336,
        TARGETPRINTER = 337,
        EXTRASAMPLES = 338,
        SAMPLEFORMAT = 339,
        SMINSAMPLEVALUE = 340,
        SMAXSAMPLEVALUE = 341,
        TRANSFERRANGE = 342,
        JPEGPROC = 512,
        JPEGINTERCHANGEFORMAT = 513,
        JPEGINTERCHANGEFORMATLENGTH = 514,
        JPEGRESTARTINTERVAL = 515,
        JPEGLOSSLESSPREDICTORS = 517,
        JPEGPOINTTRANSFORMS = 518,
        JPEGQTABLES = 519,
        JPEGDCTABLES = 520,
        JPEGACTABLES = 521,
        YCBCRCOEFFICIENTS = 529,
        YCBCRSUBSAMPLING = 530,
        YCBCRPOSITIONING = 531,
        REFERENCEBLACKWHITE = 532,
        COPYRIGHT = 33432;

    /** Fill order tag (266) labels. */
    private static final String [] FILLORDER_L = {
        "", "high-order", "low-order"
    };
    /** Indexed tag (346) labels. */
    private static final String [] INDEXED_L = {
        "not indexed", "indexed"
    };
    /** InkSet tag (332) labels. */
    private static final String [] INKSET_L = {
        "", "CMYK", "not CMYK"
    };
    /** JPEGLosslessPredictors tag (517) labels. */
    private static final String [] JPEGLOSSLESSPREDICTORS_L = {
        "", "A", "B", "C", "A+B+C", "A+((B-C)/2)", "B+((A-C)/2)", "(A+B)/2"
    };
    /** JPEGProc tag (512) labels. */
    private static final String [] JPEGPROC_L = {
        "baseline sequential process", "lossless process with Huffman coding"
    };
    private static final int [] JPEGPROC_INDEX = {
        1, 14
    };
    /** NewSubfileType tag (254) bit labels. */
    private static final String [] NEWSUBFILETYPE_L = {
        "reduced-resolution image of another image in this file",
        "single page of multi-page image",
        "transparency mask for another image in this file"
    };
    /** OPIProxy tag (351) labels. */
    private static final String [] OPIPROXY_L = {
        "no higher-resolution version exists",
        "higher-resolution version exists"
    };
    /** Predictor tag (317) labels. */
    private static final String [] PREDICTOR_L = {
        "", "no prediction scheme", "horizontal differencing"
    };
    /** SampleFormat tag (339) labels. */
    private static final String [] SAMPLEFORMAT_L = {
        "", "unsigned integer", "signed integer", "IEEE floating point",
        "undefined"
    };
    /** SubfileType tag (255) labels. */
    private static final String [] SUBFILETYPE_L = {
        "", "full-resolution image", "reduced-resolution image",
        "single page of multi-page image"
    };
    /** Threshholding tag (263) labels. */
    private static final String [] THRESHHOLDING_L = {
        "", "no dithering or halftoning", "ordered dithering or halftoning",
        "randomized process"
    };
    /** YCbCrPositioning tag (531) labels. */
    private static final String [] YCBCRPOSITIONING_L = {
        "", "centered", "cosited"
    };
    /** YCbCrSubSampling tag (530) labels. */
    private static final String [] YCBCRSUBSAMPLING_HORZ = {
        "", "width of chroma image is equal to width of associated luma image",
        "width of chroma image is 1/2 the width of associated luma image", "",
        "width of chroma image is 1/4 the width of associated luma image"
    };
    private static final String [] YCBCRSUBSAMPLING_VERT = {
        "",
        "length of chroma image is equal to length of associated luma image",
        "length of chroma image is 1/2 the length of associated luma image",
        "",
        "length of chroma image is 1/4 the length of associated luma image"
    };

    /** TIFF/IT tags. */
    private static final int
        SITE = 34016,
        COLORSEQUENCE = 34017,
        IT8HEADER = 34018,
        RASTERPADDING = 34019,
        BITSPERRUNLENGTH = 34020,
        BITSPEREXTENDEDRUNLENGTH = 34021,
        COLORTABLE = 34022,
        IMAGECOLORINDICATOR = 34023,
        BACKGROUNDCOLORINDICATOR = 34024,
        IMAGECOLORVALUE = 34025,
        BACKGROUNDCOLORVALUE = 34026,
        PIXELINTENSITYRANGE = 34027,
        TRANSPARENCYINDICATOR = 34028,
        COLORCHARACTERIZATION = 34029,
        HCUSAGE = 34030;

    public static final String[] BACKGROUNDCOLORINDICATOR_L = {
        "background not defined", "Background color defined", 
        "full transparency, background color not defined"
    };
    public static final String [] HCUSAGE_L = {
        "high resolution CT contone information",
        "line art (line work) information", "trapping information"
    };
    public static final String[] IMAGECOLORINDICATOR_L = {
        "image not defined", "image color defined",
        "full transparency, image color not defined"
    };
    /* RasterPadding tag (34019) labels */
    private static final String [] RASTERPADDING_L = {
        "1 byte", "2 bytes", "4 bytes", "512 bytes", "1024 bytes"
    };
    private static final int [] RASTERPADDING_INDEX = {
        0, 1, 2, 9, 10
    };
    public static final String [] TRANSPARENCYINDICATOR_L = {
        "no transparency", "transparency used"
    };

    /** TIFF/EP tags. */
    private static final int
        CFAREPEATPATTERNDIM = 33421,
        CFAPATTERN = 33422,
        BATTERYLEVEL = 33423,
        EXPOSURETIME = 33434,
        FNUMBER = 33437,
        IPTCNAA = 33723,
        ICC_PROFILE = 34675,
        EXPOSUREPROGRAM = 34850,
        SPECTRALSENSITIVITY = 34852,
        ISOSPEEDRATINGS = 34855,
        OECF = 34856,
        INTERLACE = 34857,
        TIMEZONEOFFSET = 34858,
        SELFTIMERMODE = 34859,
        DATETIMEORIGINAL = 36867,
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
        FLASHENERGY = 37387,
        SPATIALFREQUENCYRESPONSE = 37388,
        NOISE = 37389,
        FOCALPLANEXRESOLUTION = 37390,
        FOCALPLANEYRESOLUTION = 37391,
        FOCALPLANERESOLUTIONUNIT = 37392,
        IMAGENUMBER = 37393,
        SECURITYCLASSIFICATION = 37394,
        IMAGEHISTORY = 37395,
        SUBJECTLOCATION = 37396,
        EXPOSUREINDEX = 37397,
        TIFFEPSTANDARDID = 37398,
        SENSINGMETHOD = 37399;
    /** TIFF/EP tag labels. */
    private static final String [] EXPOSUREPROGRAM_L = {
        "unidentified", "manual", "program normal", "aperature priority",
        "shutter priority", "program creative", "program action",
        "portrait mode", "landscape mode"
    };
    private static final String [] FLASH_L = {
        "did not fire", "fired", "fired, return not sensed",
        "fired, return sensed",
        "fired, fill flash mode, camera has no flash return sensing capability",
        "fired, fill flash mode, return not sensed",
        "fired, fill flash mode, return sensed",
        "did not fire, flash 'off' mode",
        "did not fire, 'auto' mode",
        "fired, 'auto' mode, camera has no flash return sensing capability",
        "fired, 'auto' mode, return not sensed",
        "fired, 'auto' mode, return sensed",
        "camera does not have a flash unit"
    };
    private static final int [] FLASH_INDEX = {
        0, 1, 5, 7, 9, 13, 15, 16, 24, 25, 29, 31, 32
    };
    private static final String [] FOCALPLANERESOLUTIONUNIT_L = {
        "", "inch", "metre", "centimetre", "millimetre", "micrometre"
    };

    /** Exif tags. */
    private static final int
        EXIFIFD = 34665,
        GPSINFOIFD = 34853,
        INTEROPERABILITYIFD = 40965;

    /** GeoTIFF tags. */
    private static final int
        GEOKEYDIRECTORYTAG = 34735,
        GEODOUBLEPARAMSTAG = 34736,
        GEOASCIIPARAMSTAG = 34737,
        MODELTIEPOINTTAG = 33922,
        MODELPIXELSCALETAG = 33550,
        MODELTRANSFORMATIONTAG = 34264;
    /** GeoTIFF key values. */
    public static final int 
        GTMODELTYPEGEOKEY = 1024,
        GTRASTERTYPEGEOKEY = 1025,
        GTCITATIONGEOKEY = 1026,
        GEOGRAPHICTYPEGEOKEY = 2048,
        GEOGCITATIONGEOKEY = 2049,
        GEOGGEODETICDATUMGEOKEY = 2050,
        GEOGPRIMEMERIDIANGEOKEY = 2051,
        GEOGLINEARUNITSGEOKEY = 2052,
        GEOGLINEARUNITSIZEGEOKEY = 2053,
        GEOGANGULARUNITSGEOKEY = 2054,
        GEOGANGULARUNITSIZEGEOKEY = 2055,
        GEOGELLIPSOIDGEOKEY = 2056,
        GEOGSEMIMAJORAXISGEOKEY = 2057,
        GEOGSEMIMINORAXISGEOKEY = 2058,
        GEOGINVFLATTENINGGEOKEY = 2059,
        GEOGAZIMUTHUNITSGEOKEY = 2060,
        GEOGPRIMEMERIDIANLONGGEOKEY = 2061,
        PROJECTEDCSTYPEGEOKEY = 3072,
        PCSCITATIONGEOKEY = 3073,
        PROJECTIONGEOKEY = 3074,
        PROJCOORDTRANSGEOKEY = 3075,
        PROJLINEARUNITSGEOKEY = 3076,
        PROJLINEARUNITSIZEGEOKEY = 3077,
        PROJSTDPARALLEL1GEOKEY = 3078,
        PROJSTDPARALLEL2GEOKEY = 3079,
        PROJNATORIGINLONGGEOKEY = 3080,
        PROJNATORIGINLATGEOKEY = 3081,
        PROJFALSEEASTINGGEOKEY = 3082,
        PROJFALSENORTHINGGEOKEY = 3083,
        PROJFALSEORIGINLONGGEOKEY = 3084,
        PROJFALSEORIGINLATGEOKEY = 3085,
        PROJFALSEORIGINEASTINGGEOKEY = 3086,
        PROJFALSEORIGINNORTHINGGEOKEY = 3087,
        PROJCENTERLONGGEOKEY = 3088,
        PROJCENTERLATGEOKEY = 3089,
        PROJCENTEREASTINGGEOKEY = 3090,
        PROJFALSEORIGINNORTHINGGEOKEY_2 = 3091,
        PROJSCALEATNATORIGINGEOKEY = 3092,
        PROJSCALEATCENTERGEOKEY = 3093,
        PROJAZIMUTHANGLEGEOKEY = 3094,
        PROJSTRAIGHTVERTPOLELONGEOKEY = 3095,
        VERTICALCSTYPEGEOKEY = 4096,
        VERTICALCITATIONGEOKEY = 4097,
        VERTICALDATUMGEOKEY = 4098,
        VERTICALUNITSGEOKEY = 4099;

    /** PageMaker 6.0 tags. */
    private static final int
        SUBIFDS = 330,
        CLIPPATH = 343,
        XCLIPPATHUNITS = 344,
        YCLIPPATHUNITS = 345,
        INDEXED = 346,
        OPIPROXY = 351,
        IMAGEID = 32781;

    /** Photoshop 'Advanced Tiff' tags. */
    private static final int
        JPEGTABLES = 347,
        IMAGESOURCEDATA = 37724;
    
    /** More Photoshop TIFF tags. 
    */
    private static final int
        PHOTOSHOPPROPS = 34377,
        ANNOTATIONS = 50255;

    /** Class F tags. */
    private static final int
        BADFAXLINES = 326,
        CLEANFAXDATA = 327,
        CONSECUTIVEBADFAXLINES = 328;

    /** XMP tag. */
    private static final int
        XMP = 700;

    /** TIFF/FX tags. */
    private static final int
        GLOBALPARAMETERSIFD = 400,
        STRIPROWCOUNTS = 559,
        IMAGELAYER = 34732;

    public static final String [] IMAGELAYER_L = {
            "", "Background", "Mask", "Foreground"
    };
    
    
    /** DNG tags. */
    private static final int
        DNGVERSION = 50706,
        DNGBACKWARDVERSION = 50707,
        UNIQUECAMERAMODEL = 50708,
        LOCALIZEDCAMERAMODEL = 50709,
        CFAPLANECOLOR = 50710,
        CFALAYOUT = 50711,
        LINEARIZATIONTABLE = 50712,
        BLACKLEVELREPEATDIM = 50713,
        BLACKLEVEL = 50714, 
        BLACKLEVELDELTAH = 50715,
        BLACKLEVELDELTAV = 50716,
        WHITELEVEL = 50717,
        DEFAULTSCALE = 50718,
        DEFAULTCROPORIGIN = 50719,
        DEFAULTCROPSIZE = 50720,
        COLORMATRIX1 = 50721,
        COLORMATRIX2 = 50722,
        CAMERACALIBRATION1 = 50723,
        CAMERACALIBRATION2 = 50724,
        REDUCTIONMATRIX1 = 50725,
        REDUCTIONMATRIX2 = 50726,
        ANALOGBALANCE = 50727,
        ASSHOTNEUTRAL = 50728,
        ASSHOTWHITEXY = 50729,
        BASELINEEXPOSURE = 50730,
        BASELINENOISE = 50731,
        BASELINESHARPNESS = 50732,
        BAYERGREENSPLIT = 50733,
        LINEARRESPONSELIMIT = 50734,
        CAMERASERIALNUMBER = 50735,
        LENSINFO = 50736,
        CHROMABLURRADIUS = 50737,
        ANTIALIASSTRENGTH = 50738,
        SHADOWSCALE = 50739,         // Undocumented tag
        DNGPRIVATEDATA = 50740,
        MAKERNOTESAFETY = 50741,
        CALIBRATIONILLUMINANT1 = 50778,
        CALIBRATIONILLUMINANT2 = 50779,
        BESTQUALITYSCALE = 50780;

    public static final String [] CFALAYOUT_L = {
            "", "Rectangular", "Staggered Layout A", "Staggered Layout B",
            "Staggered Layout C", "Staggered Layout D"
    };
    public static final String[] MAKERNOTESAFETY_L = {
            "Unsafe", "Safe"
    };

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** NISO Z39.87/AIIM 20-2002 image metadata. */
    private NisoImageMetadata _niso;

    /** NewSubfileType tag (254). */
    private long _newSubfileType;
    /** SubfileType tag (255). */
    private int _subfileType;
    /** PhotometricInterpretation tag (262). */
    private int _photometricInterpretation;
    /** Threshholding tag (263). */
    private int _threshholding;
    /** Cell width tag (264). */
    private int _cellWidth;
    /** Cell length tag (265). */
    private int _cellLength;
    /** Fill order tag (266). */
    private int _fillOrder;
    /** Document name tag (269). */
    private String _documentName;
    /** Image description tag (270). */
    private String _imageDescription;
    /** Minimum sample value tag (280). */
    private int [] _minSampleValue;
    /** Maximum sample value tag (281). */
    private int [] _maxSampleValue;
    /** Page name tag (285). */
    private String _pageName;
    /** X position tag (286). */
    private Rational _xPosition;
    /** Y position tag (287). */
    private Rational _yPosition;
    /** Free offsets tag (288). */
    private long [] _freeOffsets;
    /** Free byte counts tag (289). */
    private long [] _freeByteCounts;
    /** CCITT Group 3 compression options tag (292). */
    private long _t4Options;
    /** CCITT Group 4 compression options tag (293). */
    private long _t6Options;
    /** Page number tag (297). */
    private int [] _pageNumber;
    /** Transfer function tag (301). */
    private boolean _transferFunction;
    /** Date/time tag (306). */
    private String _dateTime;
    /** Compression differencing predictor tag (317). */
    private int _predictor;
    /** Halftone hints tag (321). */
    private int [] _halftoneHints;
    /** Bad fax lines tag (326). */
    private long _badFaxLines;
    /** Clean fax data tag (327). */
    private short _cleanFaxData;
    /** Consecutive bad fax lines tag (328). */
    private long _consecutiveBadFaxLines;
    /** Ink set tag (332). */
    private int _inkSet;
    /** InkNames tag (322). */
    private String [] _inkNames;
    /** Sub IFDs tag (330). */
    private long [] _subIFDs;
    /** Number of inks tag (334). */
    private int _numberOfInks;
    /** Dot range tag (336). */
    private int [] _dotRange;
    /** Target printer tag (337). */
    private String _targetPrinter;
    /** Sample format tag (339). */
    private int [] _sampleFormat;
    /** Transfer range tag (342). */
    private int [] _transferRange;
    /** Clip path tag (343). */
    private int [] _clipPath;
    /** X clip path units tag (344). */
    private long _xClipPathUnits;
    /** Y clip path units tag (345). */
    private long _yClipPathUnits;
    /** Indexed tag (346). */
    private int _indexed;
    /** JPEG tables tag (347). */
    private int [] _jpegTables;
    /** OPI proxy tag (351). */
    private int _opiProxy;
    /** JPEG Proc tag (512). */
    private int _jpegProc;
    /** JPEG interchange format tag (513). */
    private long _jpegInterchangeFormat;
    /** JPEG interchange format length tag (514). */
    private long _jpegInterchangeFormatLength;
    /** JPEG restart interval tag (515). */
    private int _jpegRestartInterval;
    /** JPEG lossless predictors tag (517). */
    private int [] _jpegLosslessPredictors;
    /** JPEG point transforms tag (518). */
    private int [] _jpegPointTransforms;
    /** JPEG Q tables tag (519). */
    private long [] _jpegQTables; 
    /** JPEG DC tables tag (520). */
    private long [] _jpegDCTables; 
    /** JPEG AC tables tag (521). */
    private long [] _jpegACTables; 
    /** Copyright tag (33432). */
    private String _copyright;
    /** Exif IFD tag (34665). */
    private long _exifIFD;
    /** GPSInfo IFD tag (34853). */
    private long _gpsInfoIFD;
    /** GlobalParametersIFD tag (400). */
    private long _globalParametersIFD;
    /** Photoshop Properties tag (34377). */
    private int[] _photoshopProperties;
    /** ImageSourceData tag (37724). */
    private int [] _imageSourceData;
    /** Exif Interoperability IFD tag (40965). */
    private long _interoperabilityIFD;
    /** Annotations tag (50255). */
    private int[] _annotations;

    /* TIFF/IT tags. */
    private int _backgroundColorIndicator;
    private int _backgroundColorValue;
    private int _bitsPerExtendedRunLength;
    private int _bitsPerRunLength;
    private String _colorCharacterization;
    private String _colorSequence;
    private int [] _colorTable;
    private long _hcUsage;
    private int _imageColorIndicator;
    private int _imageColorValue;
    private String _it8Header;
    private int [] _pixelIntensityRange;
    private int _rasterPadding;
    private String _site;
    private int _transparencyIndicator;

    /* TIFF/EP tags. */
    private Rational _aperatureValue;
    private String _batteryLevel;
    private int [] _cfaRepeatPatternDim;
    private int [] _cfaPattern;
    private Rational _compressedBitsPerPixel;
    private int _exposureProgram;
    private int _flash;
    private int _focalPlaneResolutionUnit;
    private Rational _focalPlaneXResolution;
    private Rational _focalPlaneYResolution;
    private int [] _interColourProfile;
    private String _imageHistory;
    private long _imageNumber;
    private int _interlace;
    private long [] _iptc;
    private int [] _isoSpeedRatings;
    private Rational _maxAperatureValue;
    private int [] _noise;
    private int [] _oecf;
    private String _securityClassification;
    private int _selfTimerMode;
    private Rational _shutterSpeedValue;
    private int [] _spatialFrequencyResponse;
    private String _spectralSensitivity;
    private int [] _subjectLocation;
    private String _tiffEPStandardID;
    private int [] _timeZoneOffset;

    /* GeoTIFF tags. */
    private String _geoAsciiParamsTag;
    private double[] _geoDoubleParamsTag;
    private int [] _geoKeyDirectoryTag;
    private double[] _modelPixelScaleTag;
    private double[] _modelTiepointTag;
    private double[] _modelTransformationTag;
    
    /* XMP property. */
    private Property _xmpProp;
    
    /* Tiff/FX tag values. */
    private long[] _stripRowCounts;
    private int[] _imageLayer;

    /** Exif IFD object. */
    private ExifIFD _theExifIFD;
    /** GPSInfo IFD object. */
    private GPSInfoIFD _theGPSInfoIFD;
    /** Exif Interoperability IFD. */
    private InteroperabilityIFD _theInteroperabilityIFD;
    /** GlobalParameters IFD. */
    private GlobalParametersIFD _theGlobalParametersIFD;
    
    /* DNG tag values.  The spec says that some of these tags go into
     * a "raw IFD," which isn't defined. Until this is explained,
     * throw it all in here. */
    private int[] _dngVersion;
    private int[] _dngBackwardVersion;
    private String _uniqueCameraModel;
    private String _localizedCameraModel;  // Note: This is specified as Unicode
    private int[] _cfaPlaneColor;
    private int _cfaLayout;
    private int[] _linearizationTable;
    private int[] _blackLevelRepeatDim;
    // BlackLevel can be SHORT or LONG or RATIONAL.
    // To avoid having to store multiple versions, we will convert
    // SHORT or LONG values to RATIONAL.
    private Rational[] _blackLevel;
    private Rational[] _blackLevelDeltaH;
    private Rational[] _blackLevelDeltaV;
    // Though BlackLevel can be RATIONAL, WhiteLevel can't.  
    // There must be a rational explanation.
    private long[] _whiteLevel;
    private Rational[] _defaultScale;
    private Rational _bestQualityScale;
    private Rational[] _defaultCropOrigin;
    private Rational[] _defaultCropSize;
    private int _calibrationIlluminant1;
    private int _calibrationIlluminant2;
    private Rational[] _colorMatrix1;
    private Rational[] _colorMatrix2;   // for calculating revolutions, no doubt
    private Rational[] _cameraCalibration1;
    private Rational[] _cameraCalibration2;
    private Rational[] _reductionMatrix1;
    private Rational[] _reductionMatrix2;
    private Rational[] _analogBalance;
    private Rational[] _asShotNeutral;
    private Rational[] _asShotWhiteXY;
    private Rational _baselineExposure;
    private Rational _baselineNoise;
    private Rational _baselineSharpness;
    private int _bayerGreenSplit;
    private Rational _linearResponseLimit;
    private String _cameraSerialNumber;
    private Rational[] _lensInfo;
    private Rational _chromaBlurRadius;
    private Rational _antiAliasStrength;
    private int[] _dngPrivateData;
    private int _makerNoteSafety;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate an <code>TiffIFD</code> object.
     * @param offset IFD offset
     * @param info  The RepInfo object
     * @param raf TIFF file
     * @param bigEndian True if big-endian file
     */
    public TiffIFD (long offset, RepInfo info, RandomAccessFile raf,
                    boolean bigEndian)
    {
        super (offset, info, raf, bigEndian);

        /* Define a NISO metadata object and set defaults. */
        _niso = new NisoImageMetadata ();
        _niso.setMimeType("image/tiff");
        _niso.setCompressionScheme (1);
        _niso.setOrientation (1);
        _niso.setPlanarConfiguration (1);
        _niso.setRowsPerStrip (4294967295L);
        _niso.setSamplesPerPixel (1);
        _niso.setByteOrder(bigEndian ? "big-endian" : "little-endian");

        /* Set non-NISO defaults. */
        _photometricInterpretation = NULL;
        _cellLength = NULL;
        _cellWidth = NULL;
        _fillOrder = NULL;
        _indexed = 0;
        _inkSet = NULL;
        _jpegInterchangeFormat = NULL;
        _jpegInterchangeFormatLength = NULL;
        _jpegProc = NULL;
        _jpegRestartInterval = NULL;
        _newSubfileType = 0L;
        _numberOfInks = NULL;
        _opiProxy = NULL;
        _predictor = NULL;
        _subfileType = NULL;
        _t4Options = NULL;
        _t6Options = NULL;
        _threshholding = 1;
        _xClipPathUnits = NULL;
        _yClipPathUnits = NULL;

        /* TIFF/IT defaults. */
        _backgroundColorIndicator = 0;
        _backgroundColorValue = NULL;
        _bitsPerExtendedRunLength = 16;
        _bitsPerRunLength = 8;
        _hcUsage = NULL;
        _imageColorIndicator = 0;
        _imageColorValue = NULL;
        _rasterPadding = 0;
        _transparencyIndicator = 0;

        /* TIFF/EP defaults. */
        _exposureProgram = NULL;
        _flash = NULL;
        _focalPlaneResolutionUnit = NULL;
        _gpsInfoIFD = NULL;
        _imageNumber = NULL;
        _selfTimerMode = NULL;

        /* Exif defaults. */
        _exifIFD = NULL;
        _focalPlaneResolutionUnit = NULL;
        _imageNumber = NULL;
        _interlace = NULL;
        _interoperabilityIFD = NULL;
        _globalParametersIFD = NULL;
        
        /* Class F/RFC 1324 defaults. */
        _badFaxLines = NULL;
        _cleanFaxData = NULL;
        _consecutiveBadFaxLines = NULL;
        
        /* XMP default. */
        _xmpProp = null;
        
        /* Tiff/FX defaults. */
        _stripRowCounts = null;
        _imageLayer = null;
        
        /* DNG defaults. */
        _dngVersion = null;
        _dngBackwardVersion = null;
        _uniqueCameraModel = null;
        _localizedCameraModel = null;
        _cfaPlaneColor = null;
        _cfaLayout = NULL;
        _linearizationTable = null;
        _blackLevelRepeatDim = null;
        _blackLevel = null;
        _blackLevelDeltaH = null;
        _blackLevelDeltaV = null;
        _whiteLevel = null;
        _defaultScale = null;
        _bestQualityScale = null;
        _defaultCropOrigin = null;
        _defaultCropSize = null;
        _calibrationIlluminant1 = NULL;
        _calibrationIlluminant2 = NULL;
        _colorMatrix1 = null;
        _colorMatrix2 = null;
        _cameraCalibration1 = null;
        _cameraCalibration2 = null;
        _reductionMatrix1 = null;
        _reductionMatrix2 = null;
        _analogBalance = null;
        _asShotNeutral = null;
        _asShotWhiteXY = null;
        _baselineExposure = null;
        _baselineNoise = null;
        _baselineSharpness = null;
        _bayerGreenSplit = NULL;
        _linearResponseLimit = null;
        _cameraSerialNumber = null;
        _lensInfo = null;
        _chromaBlurRadius = null;
        _antiAliasStrength = null;
        _dngPrivateData = null;
        _makerNoteSafety = NULL;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /** Returns the value of the APERTUREVALUE (37378) tag.  Note typo in
     *  function name. */
    public Rational getAperatureValue ()
    {
        return _aperatureValue;
    }

    /** Returns the value of the TIFF/IT BACKGROUNDCOLORINDICATOR
     *  (34024) tag. */
    public int getBackgroundColorIndicator ()
    {
        return _backgroundColorIndicator;
    }

    /** Returns the value of the BACKGROUNDCOLORVALUE
     *  (34026) tag. */
    public int getBackgroundColorValue ()
    {
        return _backgroundColorValue;
    }

    /** Returns the value of the BATTERYLEVEL (33423) tag. */
    public String getBatteryLevel ()
    {
        return _batteryLevel;
    }

    /** Returns the value of the BITSPEREXTENDEDRUNLENGTH
     *  (34021) tag. */
    public int getBitsPerExtendedRunLength ()
    {
        return _bitsPerExtendedRunLength;
    }

    /** Returns the value of the BITSPERRUNLENGTH (34020) tag. */
    public int getBitsPerRunLength ()
    {
        return _bitsPerRunLength;
    }

    /** Returns the value of the CELLLENGTH (265) tag. */
    public int getCellLength ()
    {
        return _cellLength;
    }

    /** Returns the value of the CELLWIDTH (264) tag. */
    public int getCellWidth ()
    {
        return _cellWidth;
    }

    /** Returns the value of the CFAPATTERN (33422) tag. */
    public int [] getCFAPattern ()
    {
        return _cfaPattern;
    }

    /** Returns the value of the CFAREPEATPATTERNDIM
     *  (33421) tag. */
    public int [] getCFARepeatPatternDim ()
    {
        return _cfaRepeatPatternDim;
    }

    /** Returns the value of the CLIPPATH (343) tag. */
    public int [] getClipPath ()
    {
        return _clipPath;
    }

    /** Returns the value of the COLORSEQUENCE 
     *  (34017) tag. */
    public String getColorSequence ()
    {
        return _colorSequence;
    }

    /** Returns the value of the COLORTABLE (34022) tag. */
    public int [] getColorTable ()
    {
        return _colorTable;
    }

    /** Returns the value of the COMPRESSEDBITSPERPIXEL
     *  (37122) tag. */
    public Rational getCompressedBitsPerPixel ()
    {
        return _compressedBitsPerPixel;
    }

    /** Returns the value of the COPYRIGHT (33432) tag. */
    public String getCopyright ()
    {
        return _copyright;
    }

    /** Returns the value of the DATETIME (306) tag. */
    public String getDateTime ()
    {
        return _dateTime;
    }

    /** Returns the value of the DOCUMENTNAME (269) tag. */
    public String getDocumentName ()
    {
        return _documentName;
    }

    /** Returns the value of the DOTRANGE (336) tag. */
    public int [] getDotRange ()
    {
        return _dotRange;
    }

    /** Return the offset of the Exif IFD. */
    public long getExifIFD ()
    {
        return _exifIFD;
    }

    /** Return the offset of the GlobalParameters IFD. */
    public long getGlobalParametersIFD ()
    {
        return _globalParametersIFD;
    }

    /** Returns the value of the EXPOSUREPROGRAM (34850) tag. */
    public int getExposureProgram ()
    {
        return _exposureProgram;
    }

    /** Returns the value of the FILLORDER (266) tag. */
    public int getFillOrder ()
    {
        return _fillOrder;
    }

    /** Returns the value of the FOCALPLANERESOLUTIONUNIT
     *  (37392) tag. */
    public int getFocalPlaneResolutionUnit ()
    {
        return _focalPlaneResolutionUnit;
    }

    /** Returns the value of the FOCALPLANEXRESOLUTION
     *  (37390) tag. */
    public Rational getFocalPlaneXResolution ()
    {
        return _focalPlaneXResolution;
    }

    /** Returns the value of the FOCALPLANEYRESOLUTION 
     *  (37390) tag. */
    public Rational getFocalPlaneYResolution ()
    {
        return _focalPlaneYResolution;
    }

    /** Returns the value of the GEOKEYDIRECTORYTAG
     *  (34735) tag. */
    public int [] getGeoKeyDirectoryTag ()
    {
        return _geoKeyDirectoryTag;
    }

    /** Return the offset of the GPSInfo IFD. */
    public long getGPSInfoIFD ()
    {
        return _gpsInfoIFD;
    }

    /** Returns the value of the IMAGECOLORINDICATOR
     *  (34023) tag. */
    public int getImageColorIndicator ()
    {
        return _imageColorIndicator;
    }

    /** Returns the value of the IMAGECOLORVALUE (34025) tag. */
    public int getImageColorValue ()
    {
        return _imageColorValue;
    }

    /** Returns the value of the IMAGEDESCRIPTION (270) tag. */
    public String getImageDescription ()
    {
        return _imageDescription;
    }

    /** Returns the value of the IMAGEHISTORY (37395) tag. */
    public String getImageHistory ()
    {
        return _imageHistory;
    }

    /** Returns the value of the IMAGELAYER (34732) tag. */
    public int[] getImageLayer ()
    {
        return _imageLayer;
    }

    /** Returns the value of the IMAGENUMBER (37393) tag. */
    public long getImageNumber ()
    {
        return _imageNumber;
    }

    /** Returns the value of the IMAGESOURCEDATA
     *  (37724) tag. */
    public int [] getImageSourceData ()
    {
        return _imageSourceData;
    }

    /** Returns the value of the PHOTOSHOPPROPS
     *  (34377) tag. */
    public int [] getPhotoshopProperties ()
    {
        return _photoshopProperties;
    }

    /** Returns the value of the ANNOTATIONS
     *  (50255) tag. */
    public int [] getAnnotations ()
    {
        return _annotations;
    }

    /** Returns the value of the INKNAMES (333) tag. */
    public String [] getInkNames ()
    {
        return _inkNames;
    }

    /** Returns the value of the INKSET (332) tag. */
    public int getInkSet ()
    {
        return _inkSet;
    }

    /** Returns the value of the INTERLACE (34857) tag. */
    public int getInterlace ()
    {
        return _interlace;
    }

    /** Returns the offset of the Exif Interoperability IFD. */
    public long getInteroperabilityIFD ()
    {
        return _interoperabilityIFD;
    }

    /** Returns the value of the ICC_PROFILE tag. */
    public int [] getInterColourProfile ()
    {
        return _interColourProfile;
    }
    
    /** Returns the value of the INDEXED (364) tag. */
    public int getIndexed ()
    {
        return _indexed;
    }
    
    public long getJpegInterchangeFormat ()
    {
        return _jpegInterchangeFormat;
    }

    /** Returns the value of the IPTCNAA (33723) tag. */
    public long [] getIPTCNAA ()
    {
        return _iptc;
    }

    /** Returns the value of the ISOSPEEDRATINGS
     *  (34855) tag. */
    public int [] getISOSpeedRatings ()
    {
        return _isoSpeedRatings;
    }

    /** Returns the value of the IT8HEADER (34018) tag. */
    public String getIT8Header ()
    {
        return _it8Header;
    }

    /** Returns the value of the JPEGPROC (512) tag. */
    public int getJPEGProc ()
    {
        return _jpegProc;
    }

    /** Returns the value of the MAXAPERTUREVALUE (37381)
     *  tag.  Note typo in function name. */
    public Rational getMaxAperatureValue ()
    {
        return _maxAperatureValue;
    }
    
    /** Returns the value of the MODELTIEPOINTTAG (33922)
     *  tag. */
    public double[] getModelTiepointTag ()
    {
        return _modelTiepointTag;
    }

    /** Returns the value of the MODELTRANSFORMATIONTAG
     *  (34264) tag. */
    public double[] getModelTransformationTag ()
    {
        return _modelTransformationTag;
    }

    /** Returns the value of the NEWSUBFILETYPE (254) tag. */
    public long getNewSubfileType ()
    {
        return _newSubfileType;
    }

    /** Returns the constructed NisoImageMetadata. */
    public NisoImageMetadata getNisoImageMetadata ()
    {
        return _niso;
    }

    /** Returns the value of the NOISE (37389) tag. */
    public int [] getNoise ()
    {
        return _noise;
    }

    /** Returns the value of the NUMBEROFINKS (334) tag. */
    public int getNumberOfInks ()
    {
        return _numberOfInks;
    }

    /** Returns the value of the OECF (34856) tag. */
    public int [] getOECF ()
    {
        return _oecf;
    }

    /** Returns the value of the PAGENAME (285) tag. */
    public String getPageName ()
    {
        return _pageName;
    }

    /** Returns the value of the PAGENUMBER (297) tag. */
    public int [] getPageNumber ()
    {
        return _pageNumber;
    }

    /** Returns the value of the PIXELINTENSITYRANGE (34027) tag. */
    public int [] getPixelIntensityRange ()
    {
        return _pixelIntensityRange;
    }

    /** Returns the value of the RASTERPADDING (34019) tag. */
    public int getRasterPadding ()
    {
        return _rasterPadding;
    }

    /** Returns the value of the SECURITYCLASSIFICATION (37394) tag. */
    public String getSecurityClasssification ()
    {
        return _securityClassification;
    }

    /** Returns the value of the SELFTIMERMODE (34859) tag. */
    public int getSelfTimerMode ()
    {
        return _selfTimerMode;
    }

    /** Returns the value of the SHUTTERSPEEDVALUE (37377) tag. */
    public Rational getShutterSpeedValue ()
    {
        return _shutterSpeedValue;
    }

    /** Returns the value of the SITE (34016) tag. */
    public String getSite ()
    {
        return _site;
    }

    /** Returns the value of the SPATIALFREQUENCYRESPONSE (37388) tag. */
    public int [] getSpatialFrequencyResponse ()
    {
        return _spatialFrequencyResponse;
    }

    /** Returns the value of the SPECTRALSENSITIVITY (34852) tag. */
    public String getSpectralSensitivity ()
    {
        return _spectralSensitivity;
    }
    
    /** Returns the value of the STRIPROWCOUNTS (559) tag. */
    public long[] getStripRowCounts ()
    {
        return _stripRowCounts;
    }

    /** Returns the value of the SUBIFDS (330) tag. */
    public long [] getSubIFDs ()
    {
        return _subIFDs;
    }

    /** Returns the value of the SUBJECTLOCATION (37396) tag. */
    public int [] getSubjectLocation ()
    {
        return _subjectLocation;
    }

    /** Returns the value of the T4OPTIONS (292) tag. */
    public long getT4Options ()
    {
        return _t4Options;
    }

    /** Returns the value of the T6OPTIONS (293) tag. */
    public long getT6Options ()
    {
        return _t6Options;
    }

    /** Returns the Exif IFD object, or null if none. */
    public ExifIFD getTheExifIFD ()
    {
        return _theExifIFD;
    }

    /** Returns the GPS info IFD object, or null if none. */
    public GPSInfoIFD getTheGPSInfoIFD ()
    {
        return _theGPSInfoIFD;
    }

    /** Returns the Interoperability IFD object,
     *  or null if none. */
    public InteroperabilityIFD getTheInteroperabilityIFD ()
    {
        return _theInteroperabilityIFD;
    }

    /** Returns the GlobalParameters IFD object, or null if none. */
    public GlobalParametersIFD getTheGlobalParametersIFD ()
    {
        return _theGlobalParametersIFD;
    }

    /** Returns the value of the THRESHHOLDING (263) tag. */
    public int getThreshholding ()
    {
        return _threshholding;
    }

    /** Returns the value of the TIFFEPSTANDARDID (37398) tag. */
    public String getTIFFEPStandardID ()
    {
        return _tiffEPStandardID;
    }

    /** Returns the value of the TIMEZONEOFFSET (34858) tag. */
    public int [] getTimeZoneOffset ()
    {
        return _timeZoneOffset;
    }

    /** Returns the value of the TRANSPARENCYINDICATOR (34028) tag. */
    public int getTransparencyIndicator ()
    {
        return _transparencyIndicator;
    }

    /** Returns the value of the XCLIPPATHUNITS (344) tag. */
    public long getXClipPathUnits ()
    {
        return _xClipPathUnits;
    }
    
    /** Returns the value of the XPOSITION (286) tag. */
    public Rational getXPosition ()
    {
        return _xPosition;
    }

    /** Returns the value of the XPOSITION (287) tag. */
    public Rational getYPosition ()
    {
        return _yPosition;
    }
    
    /** Returns the value of the DNGVERSION (50706) tag. */
    public int[] getDNGVersion ()
    {
        return _dngVersion;
    }
    
    /** Returns the value of the DNG UNIQUECAMERAMODEL (50708) tag. */
    public String getUniqueCameraModel ()
    {
        return _uniqueCameraModel;
    }
    
    /** Returns the value of the CFAPlaneColor (50710) tag. */
    public int[] getCFAPlaneColor ()
    {
        return _cfaPlaneColor;
    }
    
    /** Returns the value of the AsShotNeutral (50728) tag. */
    public Rational[] getAsShotNeutral ()
    {
        return _asShotNeutral;
    }
    
    /** Returns the value of the AsShotWhiteXY (50729) tag. */
    public Rational[] getAsShotWhiteXY ()
    {
        return _asShotWhiteXY;
    }

    /** Get the IFD properties. */
    public Property getProperty (boolean rawOutput)
                throws TiffException
    {
        List<Property> entries = new LinkedList<Property> ();
        // This function has gotten obscenely large.  Split it up.
        addNisoProperties (entries, rawOutput);
        addMiscProperties (entries, rawOutput);
        addTiffITProperties (entries, rawOutput);
        addTiffEPProperties (entries, rawOutput);
        addGeoTiffProperties (entries, rawOutput);
        addTiffFXProperties (entries, rawOutput);
        addDNGProperties (entries, rawOutput);
        return propertyHeader ("TIFF", entries);
    }


    private void addNisoProperties (List<Property> entries, boolean rawOutput)
    {
        entries.add (new Property ("NisoImageMetadata",
                                   PropertyType.NISOIMAGEMETADATA, _niso));
    }

        /* Add non-NISO properties. */
    private void addMiscProperties (List<Property> entries, boolean rawOutput)
    {
        if (_imageDescription != null) {
            entries.add (new Property ("ImageDescription", PropertyType.STRING,
                                       _imageDescription));
        }
        if (_dateTime != null) {
            entries.add (new Property ("DateTime", PropertyType.STRING,
                                       _dateTime));
        }
        if (_newSubfileType != 0L || rawOutput) {
            entries.add (addBitmaskProperty ("NewSubfileType",
                                             _newSubfileType,
                                             NEWSUBFILETYPE_L, rawOutput));
        }
        else {
            // if 0, always report as a raw number
            entries.add (new Property ("NewSubfileType", PropertyType.LONG,
                                    new Long (_newSubfileType)));
        }
        if (_subfileType != NULL && (_subfileType != 0 || rawOutput)) {
            entries.add (addIntegerProperty ("SubfileType", _subfileType - 1,
                                             SUBFILETYPE_L, rawOutput));
        }
        else if (_subfileType != NULL) {
            // if 0, always report as a raw number
            entries.add (new Property ("SubfileType", PropertyType.LONG,
                                    new Long (_subfileType)));
        }
        if (_documentName != null) {
            entries.add (new Property ("DocmentName", PropertyType.STRING,
                                       _documentName));
        }
        if (_pageName != null) {
            entries.add (new Property ("PageName", PropertyType.STRING,
                                       _pageName));
        }
        if (_pageNumber != null) {
            entries.add (new Property ("PageNumber", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _pageNumber));
        }
        if (_xPosition != null) {
            entries.add (addRationalProperty ("XPosition", _xPosition,
                                              rawOutput));
        }
        if (_yPosition != null) {
            entries.add (addRationalProperty ("YPosition", _yPosition,
                                              rawOutput));
        }
        if (_copyright != null) {
            entries.add (new Property ("Copyright", PropertyType.STRING,
                                       _copyright));    
        }
        if (_fillOrder != NULL) {
            entries.add (addIntegerProperty ("FillOrder", _fillOrder,
                                             FILLORDER_L, rawOutput));
        }
        entries.add (new Property ("SampleFormat", PropertyType.INTEGER,
                                   PropertyArity.ARRAY, _sampleFormat));
        if (_minSampleValue != null) {
            entries.add (new Property ("MinSampleValue", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _minSampleValue));
        }
        if (_maxSampleValue != null) {
            entries.add (new Property ("MaxSampleValue", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _maxSampleValue));
        }
        if (_inkSet != NULL) {
            entries.add (addIntegerProperty ("InkSet", _inkSet, INKSET_L,
                                         rawOutput));
        }
        if (_numberOfInks != NULL) {
            entries.add (new Property ("NumberOfInks", PropertyType.INTEGER,
                                   new Integer (_numberOfInks)));
        }
        if (_inkNames != null) {
            entries.add (new Property ("InkNames", PropertyType.STRING,
                                       PropertyArity.ARRAY, _inkNames));
        }
        if (_dotRange != null) {
            entries.add (new Property ("DotRange", PropertyType.INTEGER,
                                   PropertyArity.ARRAY, _dotRange));
        }
        if (_targetPrinter != null) {
            entries.add (new Property ("TargetPrinter", PropertyType.STRING,
                                       _targetPrinter));
        }
        if (_halftoneHints != null) {
            entries.add (new Property ("HalftoneHints", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _halftoneHints));
        }
        if (_cellLength != NULL) {
            entries.add (new Property ("CellLength", PropertyType.INTEGER,
                                   new Integer (_cellLength)));
        }
        if (_cellWidth != NULL) {
            entries.add (new Property ("CellWidth", PropertyType.INTEGER,
                                   new Integer (_cellWidth)));
        }
        if (_transferFunction) {
            entries.add (new Property ("TransferFunction", PropertyType.BOOLEAN,
                                   new Boolean (true)));
        }
        if (_transferRange != null) {
            entries.add (new Property ("TransferRange", PropertyType.INTEGER,
                                   PropertyArity.ARRAY, _transferRange));
        }
        entries.add (new Property ("Threshholding", PropertyType.INTEGER,
                                   new Integer (_threshholding)));
        if (_predictor != NULL) {
            entries.add (addIntegerProperty ("Predictor", _predictor,
                                         PREDICTOR_L, rawOutput));
        }
        if (_t4Options != NULL) {
            entries.add (new Property ("T4Options", PropertyType.LONG,
                                   new Long (_t4Options)));
        }
        if (_t6Options != NULL) {
            entries.add (new Property ("T6Options", PropertyType.LONG,
                                   new Long (_t6Options)));
        }
        if (_jpegProc != NULL) {
            entries.add (addIntegerProperty ("JPEGProc", _jpegProc,
                                             JPEGPROC_L, JPEGPROC_INDEX,
                                             rawOutput));
        }
        if (_jpegInterchangeFormat != NULL) {
            entries.add (new Property ("JPEGInterchangeFormat",
                                       PropertyType.LONG,
                                       new Long (_jpegInterchangeFormat)));
        }
        if (_jpegInterchangeFormatLength != NULL) {
            entries.add (new Property ("JPEGInterchangeFormatLength",
                                       PropertyType.LONG,
                                       new Long (_jpegInterchangeFormatLength)));
        }
        if (_jpegRestartInterval != NULL) {
            entries.add (new Property ("JPEGRestartInterval",
                                       PropertyType.INTEGER,
                                       new Integer (_jpegRestartInterval)));
        }
        if (_jpegLosslessPredictors != null) {
            entries.add (addIntegerArrayProperty ("JPEGLosslessPredictors",
                                                  _jpegLosslessPredictors,
                                                  JPEGLOSSLESSPREDICTORS_L,
                                                  rawOutput));
        }
        if (_jpegPointTransforms != null) {
            entries.add (new Property ("JPEGPointTransforms",
                                       PropertyType.INTEGER,
                                       PropertyArity.ARRAY,
                                       _jpegPointTransforms));
        }
        if (_jpegQTables != null) {
            entries.add (new Property ("JPEGQTables", PropertyType.LONG,
                                       PropertyArity.ARRAY, _jpegQTables));
        }
        if (_jpegDCTables != null) {
            entries.add (new Property ("JPEGDCTables", PropertyType.LONG,
                                       PropertyArity.ARRAY, _jpegDCTables));
        }
        if (_jpegACTables != null) {
            entries.add (new Property ("JPEGACTables", PropertyType.LONG,
                                       PropertyArity.ARRAY, _jpegACTables));
        }
        if (_jpegTables != null) {
            entries.add (new Property ("JPEGTables", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _jpegTables));
        }
        if (_imageSourceData != null) {
            entries.add (new Property ("ImageSourceData", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _imageSourceData));
        }
        if (_photoshopProperties != null) {
            entries.add (new Property ("PhotoshopProperties", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _photoshopProperties));
        }
        if (_annotations != null) {
            entries.add (new Property ("Annotations", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _annotations));
        }
        if (_clipPath != null) {
            entries.add (new Property ("ClipPath", PropertyType.INTEGER,
                                       PropertyArity.ARRAY, _clipPath));
        }
        if (_xClipPathUnits != NULL) {
            entries.add (new Property ("XClipPathUnits", PropertyType.LONG,
                                       new Long (_xClipPathUnits)));
        }
        if (_yClipPathUnits != NULL) {
            entries.add (new Property ("YClipPathUnits", PropertyType.LONG,
                                       new Long (_yClipPathUnits)));
        }
        if (_cleanFaxData != NULL) {
            entries.add (new Property ("CleanFaxData", PropertyType.LONG,
                                       new Long (_cleanFaxData)));
        }
        if (_badFaxLines != NULL) {
            entries.add (new Property ("BadFaxLines", PropertyType.LONG,
                                       new Long (_badFaxLines)));
        }
        if (_consecutiveBadFaxLines != NULL) {
            entries.add (new Property ("ConsecutiveBadFaxLines",
                                       PropertyType.LONG,
                                       new Long (_consecutiveBadFaxLines)));
        }
        if (_freeByteCounts != null) {
            entries.add (new Property ("FreeByteCounts", PropertyType.LONG,
                                       PropertyArity.ARRAY, _freeByteCounts));
        }
        if (_freeOffsets != null) {
            entries.add (new Property ("FreeOffsets", PropertyType.LONG,
                                       PropertyArity.ARRAY, _freeOffsets));
        }
    }
    
    private void addTiffITProperties (List<Property> entries, boolean rawOutput)
    {
        /* Add TIFF/IT properties. */

        List<Property> itList = new LinkedList<Property> ();
        if (_site != null) {
            itList.add (new Property ("Site", PropertyType.STRING, _site));
        }
        if (_colorTable != null) {
            itList.add (new Property ("ColorTable", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _colorTable));
        }
        itList.add (addIntegerProperty ("BackgroundColorIndicator",
                                        _backgroundColorIndicator,
                                        BACKGROUNDCOLORINDICATOR_L,
                                        rawOutput));
        if (_backgroundColorValue != NULL) {
            itList.add (new Property ("BackgroundColorValue",
                                      PropertyType.INTEGER,
                                      new Integer (_backgroundColorValue)));
        }
        itList.add (addIntegerProperty ("ImageColorIndicator",
                                        _imageColorIndicator,
                                        IMAGECOLORINDICATOR_L, rawOutput));
        itList.add (addIntegerProperty ("TransparencyIndicator",
                                        _transparencyIndicator,
                                        TRANSPARENCYINDICATOR_L, rawOutput));
        if (_imageColorValue != NULL) {
            itList.add (new Property ("ImageColorValue", PropertyType.INTEGER,
                                      new Integer (_imageColorValue)));
        }
        if (_colorCharacterization != null) {
            itList.add (new Property ("ColorCharacterization",
                                      PropertyType.STRING,
                                      _colorCharacterization));
        }
        if (_colorSequence != null) {
            itList.add (new Property ("ColorSequence", PropertyType.STRING,
                                      _colorSequence));
        }
        if (_hcUsage != NULL) {
            itList.add (addBitmaskProperty ("HCUsage", _hcUsage, HCUSAGE_L,
                                            rawOutput));
        }
        if (_it8Header != null) {
            itList.add (new Property ("IT8Header", PropertyType.STRING,
                                      _it8Header));
        }
        if (_pixelIntensityRange != null) {
            itList.add (new Property ("PixelIntensityRange",
                                      PropertyType.INTEGER,
                                      PropertyArity.ARRAY,
                                      _pixelIntensityRange));
        }
        itList.add (addIntegerProperty ("RasterPadding", _rasterPadding,
                                        RASTERPADDING_L, rawOutput));
        itList.add (new Property ("BitsPerRunLength", PropertyType.INTEGER,
                                  new Integer (_bitsPerRunLength)));
        itList.add (new Property ("BitsPerExtendedRunLength",
                                  PropertyType.INTEGER,
                                  new Integer (_bitsPerExtendedRunLength)));
        entries.add (new Property ("TIFFITProperties", PropertyType.PROPERTY,
                                   PropertyArity.LIST, itList));
    }
    

        /* Add TIFF/EP properties. */
    private void addTiffEPProperties (List<Property> entries, boolean rawOutput)
    {
        List<Property> epList = new LinkedList<Property> ();
        if (_cfaRepeatPatternDim != null) {
            epList.add (new Property ("CFARepeatPatternDim",
                                      PropertyType.INTEGER,
                                      PropertyArity.ARRAY,
                                      _cfaRepeatPatternDim));
        }
        if (_cfaPattern != null) {
            epList.add (new Property ("CFAPattern", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _cfaPattern));
        }
        if (_batteryLevel != null) {
            epList.add (new Property ("BatteryLevel", PropertyType.STRING,
                                      _batteryLevel));
        }
        if (_iptc != null) {
            epList.add (new Property ("IPTCNAA", PropertyType.LONG,
                                      PropertyArity.ARRAY, _iptc));
        }
        if (_interColourProfile != null) {
            epList.add (new Property ("InterColourProfile",
                                      PropertyType.BOOLEAN,
                                      Boolean.TRUE));
        }
        if (_exposureProgram != NULL) {
            epList.add (addIntegerProperty ("ExposureProgram",
                                            _exposureProgram,
                                            EXPOSUREPROGRAM_L, rawOutput));
        }
        if (_spectralSensitivity != null) {
            epList.add (new Property ("SpectralSensitivity",
                                      PropertyType.STRING,
                                      _spectralSensitivity));
        }
        if (_isoSpeedRatings != null)  {
            epList.add (new Property ("ISOSpeedRatings",
                                      PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _isoSpeedRatings));
        }
        if (_oecf != null)  {
            epList.add (new Property ("OECF", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _oecf));
        }
        if (_interlace != NULL)  {
            epList.add (new Property ("Interlace", PropertyType.INTEGER,
                                      new Integer (_interlace)));
        }
        if (_timeZoneOffset != null)  {
            epList.add (new Property ("TimeZoneOffset", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _timeZoneOffset));
        }
        if (_selfTimerMode != NULL)  {
            epList.add (new Property ("SelfTimerMode", PropertyType.INTEGER,
                                      new Integer (_selfTimerMode)));
        }
        if (_compressedBitsPerPixel != null)  {
            epList.add (addRationalProperty ("CompressedBitsPerPixel",
                                             _compressedBitsPerPixel,
                                             rawOutput));
        }
        if (_shutterSpeedValue != null)  {
            epList.add (addRationalProperty ("ShutterSpeedValue",
                                             _shutterSpeedValue, rawOutput));
        }
        if (_aperatureValue != null)  {
            epList.add (addRationalProperty ("AperatureValue",
                                             _aperatureValue, rawOutput));
        }
        if (_maxAperatureValue != null)  {
            epList.add (addRationalProperty ("MaxAperatureValue",
                                             _maxAperatureValue, rawOutput));
        }
        if (_flash != NULL) {
            epList.add (addIntegerProperty ("FLASH", _flash, FLASH_L,
                                            FLASH_INDEX, rawOutput));
        }
        if (_spatialFrequencyResponse != null)  {
            epList.add (new Property ("SpatialFrequencyResponse",
                                      PropertyType.INTEGER,
                                      PropertyArity.ARRAY,
                                      _spatialFrequencyResponse));
        }
        if (_noise != null)  {
            epList.add (new Property ("Noise", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _noise));
        }
        if (_focalPlaneXResolution != null)  {
            epList.add (addRationalProperty ("FocalPlaneXResolution",
                                             _focalPlaneXResolution,
                                             rawOutput));
        }
        if (_focalPlaneYResolution != null)  {
            epList.add (addRationalProperty ("FocalPlaneYResolution",
                                             _focalPlaneYResolution,
                                             rawOutput));
        }
        if (_focalPlaneResolutionUnit != NULL) {
            epList.add (addIntegerProperty ("FocalPlaneResolutionUnit",
                                            _focalPlaneResolutionUnit,
                                            FOCALPLANERESOLUTIONUNIT_L,
                                            rawOutput));
        }
        if (_imageNumber != NULL) {
            epList.add (new Property ("ImageNumber", PropertyType.LONG,
                                      new Long (_imageNumber)));
        }
        if (_securityClassification != null) {
            epList.add (new Property ("SecurityClassification",
                                      PropertyType.STRING,
                                      _securityClassification));
        }
        if (_imageHistory != null) {
            epList.add (new Property ("ImageHistory", PropertyType.STRING,
                                      _imageHistory));
        }
        if (_subjectLocation != null) {
            epList.add (new Property ("SubjectLocation", PropertyType.INTEGER,
                                      PropertyArity.ARRAY, _subjectLocation));
        }
        if (_tiffEPStandardID != null) {
            epList.add (new Property ("TIFFEPSStandardID",
                                      PropertyType.STRING,
                                      _tiffEPStandardID));
        }
        if (epList.size () > 0) {
            entries.add (new Property ("TIFFEPProperties",
                                       PropertyType.PROPERTY,
                                       PropertyArity.LIST, epList));
        }
        
        if (_xmpProp != null) {
            entries.add (_xmpProp);
        }
    }
    
    
    private void addGeoTiffProperties (List<Property> entries, boolean rawOutput)
            throws TiffException
    {
        /* Add GeoTIFF properties. */

        List<Property> dirList = new LinkedList<Property> ();
        if (_geoKeyDirectoryTag != null) {
            dirList.add (new Property ("Version", PropertyType.INTEGER,
                                       new Integer (_geoKeyDirectoryTag[0])));
            dirList.add (new Property ("Revision", PropertyType.STRING,
                               Integer.toString (_geoKeyDirectoryTag[1]) + "."+
                               Integer.toString (_geoKeyDirectoryTag[2])));
            dirList.add (new Property ("NumberOfKeys", PropertyType.INTEGER,
                                       new Integer (_geoKeyDirectoryTag[3])));
            for (int i=0; i<_geoKeyDirectoryTag[3]; i++) {
                int j = i*4 + 4;
                int key      = _geoKeyDirectoryTag[j];
                int location = _geoKeyDirectoryTag[j+1];
                int count    = _geoKeyDirectoryTag[j+2];
                int offset   = _geoKeyDirectoryTag[j+3];

                int ival = 0;
                double dval = 0.0;
                String sval = "NULL";
                if (location == 0) {
                    ival = offset;
                }
                else if (location == 34736) {
                    dval = _geoDoubleParamsTag[offset];
                }
                else if (location == 34737) {
                    try {
                        sval = _geoAsciiParamsTag.substring (offset, offset + count-1);
                    }
                    catch (Exception e) {
                        throw new TiffException ("Invalid GeoKeyDirectory tag");
                    }
                }

                if (key == GTMODELTYPEGEOKEY) {
                    dirList.add (addIntegerProperty ("GTModelType", ival,
                                             GeoTiffStrings.MODELTYPE,
                                             GeoTiffStrings.MODELTYPE_INDEX,
                                             rawOutput));
                }
                else if (key == GTRASTERTYPEGEOKEY) {
                    dirList.add (addIntegerProperty ("GTRasterType", ival,
                                             GeoTiffStrings.RASTERTYPE,
                                             GeoTiffStrings.RASTERTYPE_INDEX,
                                                     rawOutput));
                }
                else if (key == GTCITATIONGEOKEY) {
                    dirList.add (new Property ("GTCitation",
                                               PropertyType.STRING, sval));
                }
                else if (key == GEOGRAPHICTYPEGEOKEY) {
                    dirList.add (addIntegerProperty ("GeographicType", ival,
                                             GeoTiffStrings.GEOGRAPHICS,
                                             GeoTiffStrings.GEOGRAPHICS_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGCITATIONGEOKEY) {
                    dirList.add (new Property ("GeogCitation",
                                               PropertyType.STRING, sval));
                }
                else if (key == GEOGGEODETICDATUMGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogGeodeticDatum", ival,
                                     GeoTiffStrings.GEODETICDATUM,
                                     GeoTiffStrings.GEODETICDATUM_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGPRIMEMERIDIANGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogPrimeMeridian", ival,
                                     GeoTiffStrings.PRIMEMERIDIAN,
                                     GeoTiffStrings.PRIMEMERIDIAN_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGPRIMEMERIDIANLONGGEOKEY) {
                    dirList.add (new Property ("GeogPrimeMeridianLong",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGLINEARUNITSGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogLinearUnits", ival,
                                             GeoTiffStrings.LINEARUNITS,
                                             GeoTiffStrings.LINEARUNITS_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGLINEARUNITSIZEGEOKEY) {
                    dirList.add (new Property ("GeogLinearUnitSize",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGANGULARUNITSGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogAngularUnits", ival,
                                             GeoTiffStrings.ANGULARUNITS,
                                             GeoTiffStrings.ANGULARUNITS_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGANGULARUNITSIZEGEOKEY) {
                    dirList.add (new Property ("GeogAngularUnitSize",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGELLIPSOIDGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogEllipsoid", ival,
                                             GeoTiffStrings.ELLIPSOID,
                                             GeoTiffStrings.ELLIPSOID_INDEX,
                                                     rawOutput));
                }
                else if (key == GEOGSEMIMAJORAXISGEOKEY) {
                    dirList.add (new Property ("GeogSemiMajorAxis",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGSEMIMINORAXISGEOKEY) {
                    dirList.add (new Property ("GeogSemiMinorAxis",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGINVFLATTENINGGEOKEY) {
                    dirList.add (new Property ("GeogInvFlattening",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == GEOGAZIMUTHUNITSGEOKEY) {
                    dirList.add (addIntegerProperty ("GeogAzimuthUnits", ival,
                                             GeoTiffStrings.ANGULARUNITS,
                                             GeoTiffStrings.ANGULARUNITS_INDEX,
                                                     rawOutput));
                }
                else if (key == PROJECTEDCSTYPEGEOKEY) {
                    dirList.add (addIntegerProperty ("ProjectedCSType", ival,
                                     GeoTiffStrings.PROJECTEDCSTYPE,
                                     GeoTiffStrings.PROJECTEDCSTYPE_INDEX,
                                                     rawOutput));
                }
                else if (key == PCSCITATIONGEOKEY) {
                    dirList.add (new Property ("PCSCitation",
                                               PropertyType.STRING, sval));
                }
                else if (key == PROJECTIONGEOKEY) {
                    dirList.add (addIntegerProperty ("Projection", ival,
                                             GeoTiffStrings.PROJECTION,
                                             GeoTiffStrings.PROJECTION_INDEX,
                                                     rawOutput));
                }
                else if (key == PROJCOORDTRANSGEOKEY) {
                    dirList.add (addIntegerProperty ("ProjCoordTrans", ival,
                             GeoTiffStrings.COORDINATETRANSFORMATION,
                             GeoTiffStrings.COORDINATETRANSFORMATION_INDEX,
                                                     rawOutput));
                }
                else if (key == PROJLINEARUNITSGEOKEY) {
                    dirList.add (addIntegerProperty ("ProjLinearUnits", ival,
                                             GeoTiffStrings.LINEARUNITS,
                                             GeoTiffStrings.LINEARUNITS_INDEX,
                                                     rawOutput));
                }
                else if (key == PROJLINEARUNITSIZEGEOKEY) {
                    dirList.add (new Property ("ProjLinearUnitSize",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJSTDPARALLEL1GEOKEY) {
                    dirList.add (new Property ("ProjStdParallel1",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJSTDPARALLEL2GEOKEY) {
                    dirList.add (new Property ("ProjStdParallel2",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJNATORIGINLONGGEOKEY) {
                    dirList.add (new Property ("ProjNatOriginLong",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJNATORIGINLATGEOKEY) {
                    dirList.add (new Property ("ProjNatOriginLat",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSEEASTINGGEOKEY) {
                    dirList.add (new Property ("ProjFalseEasting",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSENORTHINGGEOKEY) {
                    dirList.add (new Property ("ProjFalseNorthing",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSEORIGINLONGGEOKEY) {
                    dirList.add (new Property ("ProjFalseOriginLong",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSEORIGINLATGEOKEY) {
                    dirList.add (new Property ("ProjFalseOriginLat",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSEORIGINEASTINGGEOKEY) {
                    dirList.add (new Property ("ProjFalseOriginEasting",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJFALSEORIGINNORTHINGGEOKEY ||
                         key == PROJFALSEORIGINNORTHINGGEOKEY_2) {
                    dirList.add (new Property ("ProjFalseOriginNorthing",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJCENTERLONGGEOKEY) {
                    dirList.add (new Property ("ProjCenterLong",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJCENTERLATGEOKEY) {
                    dirList.add (new Property ("ProjCenterLat",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJCENTEREASTINGGEOKEY) {
                    dirList.add (new Property ("ProjCenterEasting",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJSCALEATNATORIGINGEOKEY) {
                    dirList.add (new Property ("ProjScaleAtNatOrigin",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJSCALEATCENTERGEOKEY) {
                    dirList.add (new Property ("ProjScaleAtCenter",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJAZIMUTHANGLEGEOKEY) {
                    dirList.add (new Property ("ProjAzimuthAngle",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == PROJSTRAIGHTVERTPOLELONGEOKEY) {
                    dirList.add (new Property ("ProjStraightVertPoleLong",
                                               PropertyType.DOUBLE,
                                               new Double (dval)));
                }
                else if (key == VERTICALCSTYPEGEOKEY) {
                    dirList.add (addIntegerProperty ("VerticalCSType", ival,
                                     GeoTiffStrings.VERTICALCSTYPE,
                                     GeoTiffStrings.VERTICALCSTYPE_INDEX,
                                                     rawOutput));
                }
                else if (key == VERTICALCITATIONGEOKEY) {
                    dirList.add (new Property ("VerticalCitation",
                                               PropertyType.STRING, sval));
                }
                else if (key == VERTICALDATUMGEOKEY) {
                    dirList.add (addIntegerProperty ("VerticalDatum", ival,
                                     GeoTiffStrings.VERTICALCSDATUM,
                                     GeoTiffStrings.VERTICALCSDATUM_INDEX,
                                                     rawOutput));
                }
                else if (key == VERTICALUNITSGEOKEY) {
                    dirList.add (addIntegerProperty ("VerticalUnits", ival,
                                             GeoTiffStrings.LINEARUNITS,
                                             GeoTiffStrings.LINEARUNITS_INDEX,
                        rawOutput));
                }
            }
        }
        List<Property> geoList = new LinkedList<Property> ();
        if (dirList.size () > 0) {
            geoList.add (new Property ("GeoKeyDirectory",
                                       PropertyType.PROPERTY,
                                       PropertyArity.LIST, dirList));
        }

        if (_modelTiepointTag != null) {
            geoList.add (new Property ("ModelTiepointTag", PropertyType.DOUBLE,
                                       PropertyArity.ARRAY,_modelTiepointTag));
        }
        if (_modelPixelScaleTag != null) {
            geoList.add (new Property ("ModelPixelScaleTag",
                                       PropertyType.DOUBLE,
                                       PropertyArity.ARRAY,
                                       _modelPixelScaleTag));
        }
        if (_modelTransformationTag != null) {
            geoList.add (new Property ("ModelTransformationTag",
                                       PropertyType.DOUBLE,
                                       PropertyArity.ARRAY,
                                       _modelTransformationTag));
        }

        if (geoList.size () > 0) {
            entries.add (new Property ("GeoTIFFProperties",
                                       PropertyType.PROPERTY,
                                       PropertyArity.LIST, geoList));
        }
    }
    
    /* Add Tiff/FX properties */
    private void addTiffFXProperties (List<Property> entries, boolean rawOutput)
    {
        if (_stripRowCounts != null)  {
            entries.add (new Property ("StripRowCounts",
                                      PropertyType.LONG,
                                      PropertyArity.ARRAY,
                                      _stripRowCounts));
        }
        if (_imageLayer != null) {
            // Do up ImageLayer as a property with two subproperties.
            Property[] layerProps = new Property[2];
            try {
                layerProps[0] = addIntegerProperty ("LayerType", _imageLayer[0],
                                IMAGELAYER_L,
                                rawOutput);
                layerProps[1] = new Property ("OrdinalNumber",
                                PropertyType.INTEGER,
                                new Integer (_imageLayer[1]));
                                
                entries.add (new Property ("ImageLayer",
                                           PropertyType.PROPERTY,
                                           PropertyArity.ARRAY,
                                           layerProps));
            }
            // Don't blow up on incorrect array size
            catch (Exception e) {}
        }
    }

    /* Adds DNG properties. */
    private void addDNGProperties (List<Property> entries, boolean rawOutput)
    {
        setDNGDefaults ();
        List<Property> dngList = new LinkedList<Property> ();
        if (_dngVersion != null) {
            dngList.add (new Property ("DNGVersion",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    _dngVersion));
        }
        if (_dngBackwardVersion != null) {
            dngList.add (new Property ("DNGBackwardVersion",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    _dngBackwardVersion));
        }
        if (_uniqueCameraModel != null) {
            dngList.add (new Property ("UniqueCameraModel",
                    PropertyType.STRING,
                    _uniqueCameraModel));
        }
        if (_localizedCameraModel != null) {
            dngList.add (new Property ("LocalizedCameraModel",
                    PropertyType.STRING,
                    _localizedCameraModel));
        }
        if (_cfaPlaneColor != null) {
            dngList.add (new Property ("CFAPlaneColor",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    _cfaPlaneColor));
        }
        if (_cfaLayout != NULL) {
            dngList.add (addIntegerProperty ("CFALayout", _cfaLayout,
                                             CFALAYOUT_L, rawOutput));
        }
        if (_linearizationTable != null) {
            dngList.add (new Property ("LinearizationTable",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    _linearizationTable));
        }
        if (_blackLevelRepeatDim != null) {
            dngList.add (new Property ("BlackLevelRepeatDim",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    _blackLevelRepeatDim));
        }
        if (_blackLevel != null) {
            dngList.add (new Property ("BlackLevel",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _blackLevel));
        }
        if (_blackLevelDeltaH != null) {
            dngList.add (new Property ("BlackLevelDeltaH",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _blackLevelDeltaH));
        }
        if (_blackLevelDeltaV != null) {
            dngList.add (new Property ("BlackLevelDeltaV",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _blackLevelDeltaV));
        }
        if (_whiteLevel != null) {
            dngList.add (new Property ("WhiteLevel",
                    PropertyType.LONG,
                    PropertyArity.ARRAY,
                    _whiteLevel));
        }
        if (_defaultScale != null) {
            dngList.add (new Property ("DefaultScale",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _defaultScale));
        }
        if (_bestQualityScale != null) {
            dngList.add (new Property ("BestQualityScale",
                    PropertyType.RATIONAL,
                    _bestQualityScale));
        }
        if (_defaultCropOrigin != null) {
            dngList.add (new Property ("DefaultCropOrigin",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _defaultCropOrigin));
        }
        if (_defaultCropSize != null) {
            dngList.add (new Property ("DefaultCropSize",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _defaultCropSize));
        }
        if (_calibrationIlluminant1 != NULL) {
            dngList.add (new Property ("CalibrationIlluminant1",
                    PropertyType.INTEGER,
                    new Integer (_calibrationIlluminant1)));
        }
        if (_calibrationIlluminant2 != NULL) {
            dngList.add (new Property ("CalibrationIlluminant2",
                    PropertyType.INTEGER,
                    new Integer (_calibrationIlluminant2)));
        }
        if (_colorMatrix1 != null) {
            dngList.add (new Property ("ColorMatrix1",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _colorMatrix1));
        }
        if (_colorMatrix2 != null) {
            dngList.add (new Property ("ColorMatrix2",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _colorMatrix2));
        }
        if (_cameraCalibration1 != null) {
            dngList.add (new Property ("CameraCalibration1",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _cameraCalibration1));
        }
        if (_cameraCalibration2 != null) {
            dngList.add (new Property ("CameraCalibration2",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _cameraCalibration2));
        }
        if (_reductionMatrix1 != null) {
            dngList.add (new Property ("ReductionMatrix1",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _reductionMatrix1));
        }
        if (_reductionMatrix2 != null) {
            dngList.add (new Property ("ReductionMatrix2",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _reductionMatrix2));
        }
        if (_analogBalance != null) {
            dngList.add (new Property ("AnalogBalance",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _analogBalance));
        }
        if (_asShotNeutral != null) {
            dngList.add (new Property ("AsShotNeutral",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _asShotNeutral));
        }
        if (_asShotWhiteXY != null) {
            dngList.add (new Property ("AsShotWhiteXY",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _asShotWhiteXY));
        }
        if (_baselineExposure != null) {
            dngList.add (new Property ("BaselineExposure",
                    PropertyType.RATIONAL,
                    _baselineExposure));
        }
        if (_baselineNoise != null) {
            dngList.add (new Property ("BaselineNoise",
                    PropertyType.RATIONAL,
                    _baselineNoise));
        }
        if (_baselineNoise != null) {
            dngList.add (new Property ("BaselineSharpness",
                    PropertyType.RATIONAL,
                    _baselineSharpness));
        }
        if (_bayerGreenSplit != NULL) {
            dngList.add (new Property ("BayerGreenSplit",
                    PropertyType.INTEGER,
                    new Integer (_bayerGreenSplit)));
        }
        if (_linearResponseLimit != null) {
            dngList.add (new Property ("LinearResponseLimit",
                    PropertyType.RATIONAL,
                    _linearResponseLimit));
        }
        if (_cameraSerialNumber != null) {
            dngList.add (new Property ("CameraSerialNumber",
                    PropertyType.STRING,
                    _cameraSerialNumber));
        }
        if (_lensInfo != null) {
            dngList.add (new Property ("LensInfo",
                    PropertyType.RATIONAL,
                    PropertyArity.ARRAY,
                    _lensInfo));
        }
        if (_chromaBlurRadius != null) {
            dngList.add (new Property ("ChromaBlurRadius",
                    PropertyType.RATIONAL,
                    _chromaBlurRadius));
        }
        if (_antiAliasStrength != null) {
            dngList.add (new Property ("AntiAliasStrength",
                    PropertyType.RATIONAL,
                    _antiAliasStrength));
        }
        if (_dngPrivateData != null) {
            dngList.add (new Property ("DNGPrivateData",
                    PropertyType.INTEGER,
                    _dngPrivateData));
        }
        if (_makerNoteSafety != NULL) {
            dngList.add (addIntegerProperty ("MakerNoteSafety", _makerNoteSafety,
                                             MAKERNOTESAFETY_L, rawOutput));
        }
        if (dngList.size () > 0) {
            entries.add (new Property ("DNGProperties",
                                       PropertyType.PROPERTY,
                                       PropertyArity.LIST, dngList));
        }
        
    }


    /** ColorPlanes is an undefined primary in the TIFF spec. It's
     *  actually a non-obvious definition which is something of a
     *  pain to calculate.
     */
    private int calcColorPlanes ()
    {
        if (_photometricInterpretation == TiffProfileDNG.CFA) {
            // In this case, it's the number of unique colors
            // in the CFA pattern.  (You mean you didn't already
            // know that?)
            int nUnique = 0;
            if (_cfaPattern == null) {
                // It's broken; return 1 so we don't try to
                // allocate zero-length objects.
                return 1;
            }
            int[] uniqueColors = new int[_cfaPattern.length];
            for (int i = 0; i < _cfaPattern.length; i++) {
                boolean unique = true;
                int color = _cfaPattern[i];
                for (int j = 0; j < nUnique; j++) {
                    if (color == uniqueColors[j]) {
                        unique = false;
                        break;
                    }
                }
                if (unique) {
                    uniqueColors[nUnique++] = color;
                }
                
            }
            return nUnique;
        }
        else {
            return _niso.getSamplesPerPixel();
        }
    }

    /** Set the default values for any DNG tags that haven't been
     *  encountered yet.  If _dngVersion is zero, apply the IFD 0
     *  defaults; if PhotometricInterpretation is CFA or RawLinear,
     *  apply the Raw IFD defaults. */
    private void setDNGDefaults ()
    {
        if (_dngVersion != null) {
            // Apply "IFD 0" defaults
            if (_dngBackwardVersion == null) {
                _dngBackwardVersion = new int[4];
                // The default value is _dngVersion with the last two
                // bytes set to zero.
                _dngBackwardVersion[0] = _dngVersion[0];
                _dngBackwardVersion[1] = _dngVersion[1];
                _dngBackwardVersion[2] = 0;
                _dngBackwardVersion[3] = 0;
            }
            
            if (_uniqueCameraModel != null && _localizedCameraModel == null) {
                _localizedCameraModel = _uniqueCameraModel;
            }
            
            if (_calibrationIlluminant1 == NULL) {
                _calibrationIlluminant1 = 0;
            }
            if (_baselineExposure == null) {
                _baselineExposure = new Rational (0, 1);
            }
            if (_baselineNoise == null) {
                _baselineNoise = new Rational (1, 1);
            }
            if (_baselineSharpness == null) {
                _baselineSharpness = new Rational (1, 1);
            }
            if (_linearResponseLimit == null) {
                _linearResponseLimit = new Rational (1, 1);
            }
            if (_makerNoteSafety == NULL) {
                _makerNoteSafety = 0;
            }
            // There are some IFD 0 defaults which depend on the value of
            // "ColorPlanes," which is derived from information in the Raw IFD.
            // This would require processing the IFD's out of order, so those
            // defaults (AnalogBalance) go unreported.
        }
        
        if (_photometricInterpretation == TiffProfileDNG.CFA ||
                _photometricInterpretation == TiffProfileDNG.LINEAR_RAW) {
            // Apply "Raw IFD" defaults.  This really isn't sufficient
            // information to establish a file as DNG, but the properties
            // are in their own category, so it's fairly harmless to leave
            // them in even if it's actually, for example, a TIFF-EP file.

            if (_cfaPlaneColor == null) {
                _cfaPlaneColor = new int[] {0, 1, 2};
            }
            
            if (_cfaLayout == NULL) {
                _cfaLayout = 1;
            }
            
            // The size of the LinearizationTable is -- I quote -- N.
            // This is NOT useful.  Skip that default.
            
            if (_blackLevelRepeatDim == null) {
                _blackLevelRepeatDim = new int[] { 1, 1 };
            }
            
            Rational zero = new Rational (0, 1);
            if (_blackLevel == null) {
                _blackLevel = new Rational [_blackLevelRepeatDim[0] *
                                            _blackLevelRepeatDim[1] *
                                            _niso.getSamplesPerPixel()];
                for (int i = 0; i < _blackLevel.length; i++) {
                    _blackLevel[i] = zero;
                }
            }
            
            if (_blackLevelDeltaH == null) {
                _blackLevelDeltaH = new Rational [(int) _niso.getImageWidth()];
                for (int i = 0; i < _blackLevelDeltaH.length; i++) {
                    _blackLevelDeltaH[i] = zero;
                }
            }

            if (_blackLevelDeltaV == null) {
                _blackLevelDeltaV = new Rational [(int) _niso.getImageLength()];
                for (int i = 0; i < _blackLevelDeltaV.length; i++) {
                    _blackLevelDeltaV[i] = zero;
                }
            }
            
            if (_whiteLevel == null) {
                _whiteLevel = new long[_niso.getSamplesPerPixel()];
                long defWhite = (1L << _niso.getBitsPerSample()[0] - 1);
                for (int i = 0; i < _whiteLevel.length; i++) {
                    _whiteLevel[i] = defWhite;
                }
            }
            
            Rational one = new Rational (1, 1);
            if (_defaultScale == null) {
                _defaultScale = new Rational[] { one, one };
            }
            
            if (_bestQualityScale == null) {
                _bestQualityScale = one;
            }
            
            if (_defaultCropOrigin == null) {
                _defaultCropOrigin = new Rational[] {zero, zero};
            }
            
            if (_defaultCropSize == null) {
                _defaultCropSize = new Rational[2];
                _defaultCropSize[0] = new Rational (_niso.getImageWidth(), 1);
                _defaultCropSize[1] = new Rational (_niso.getImageLength(), 1);
            }
            int colorPlanes = calcColorPlanes ();
            if (_cameraCalibration1 == null) {
                // Identity matrix with dimension of ColorPlanes*ColorPlanes
                _cameraCalibration1 = identityMatrix (colorPlanes);
            }
            if (_cameraCalibration2 == null) {
                // Identity matrix with dimension of ColorPlanes*ColorPlanes
                _cameraCalibration2 = identityMatrix (colorPlanes);
            }
            if (_bayerGreenSplit == NULL && _photometricInterpretation == TiffProfileDNG.CFA) {
                _bayerGreenSplit = 0;
            }
            if (_antiAliasStrength == null) {
                _antiAliasStrength = new Rational (1, 1);
            }
        }
    }


    /** Create a Rational identity matrix of the specified size. */
    private Rational [] identityMatrix (int dim)
    {
        Rational[] val = new Rational [dim * dim];
        // Set them all to zero, then overwrite the diagonal values
        // to one.
        int i;
        for (i = 0; i < dim * dim; i++) {
            val[i] = new Rational (0, 1);
        }
        for (i = 0; i < dim; i++) {
            val[dim * i + i] = new Rational (1, 1);
        }
        return val;
    }

    /** Looks up an IFD tag. */
    public void lookupTag (int tag, int type, long count, long value)
        throws TiffException
    {
        try {
            if (tag == APERTUREVALUE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _aperatureValue = readRational (count, value);
            }
            else if (tag == ARTIST) {
                checkType  (tag, type, ASCII);
                _niso.setImageProducer (readASCII (count, value));

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == BACKGROUNDCOLORINDICATOR) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _backgroundColorIndicator = readByte (type, count, value);
            }
            else if (tag == BACKGROUNDCOLORVALUE) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _backgroundColorValue = readByte (type, count, value);
            }
            else if (tag == BADFAXLINES) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _badFaxLines = readLong (type, count, value);
            }
            else if (tag == BATTERYLEVEL) {
                checkType  (tag, type, RATIONAL, ASCII);
                if (type == RATIONAL) {
                    Rational r = readRational (count, value);
                    _batteryLevel = Double.toString (r.toDouble ());
                }
                else {
                    _batteryLevel = readASCII (count, value);
                }
            }                                      
            else if (tag == BITSPEREXTENDEDRUNLENGTH) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _bitsPerExtendedRunLength = readShort (type, count, value);
            }
            else if (tag == BITSPERRUNLENGTH) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _bitsPerRunLength = readShort (type, count, value);
            }
            else if (tag == BITSPERSAMPLE) {
                checkType  (tag, type, SHORT);
                _niso.setBitsPerSample (readShortArray (type, count, value));
            }
            else if (tag == BRIGHTNESSVALUE) {
                checkType  (tag, type, SRATIONAL);
                if (count == 1) {
                    _niso.setBrightness (readSignedRational (count,
						       value).toDouble ());
                }
                else {
                    Rational [] r = readSignedRationalArray (count, value);
                    _niso.setBrightness (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == CELLLENGTH) {
                checkType  (tag, type, SHORT);
                _cellLength = readShort (type, count, value);
            }
            else if (tag == CELLWIDTH) {
                checkType  (tag, type, SHORT);
                _cellWidth = readShort (type, count, value);
            }
            else if (tag == CFAPATTERN) {
                checkType  (tag, type, BYTE);
                _cfaPattern = readByteArray (type, count, value);
            }
            else if (tag == CFAREPEATPATTERNDIM) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 2);
                _cfaRepeatPatternDim = readShortArray (type, count, value);
            }
            else if (tag == CLEANFAXDATA) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _badFaxLines = readShort (type, count, value);
            }
            else if (tag == CLIPPATH) {
                checkType  (tag, type, BYTE);
                _clipPath = readByteArray (type, count, value);
            }
            else if (tag == COLORCHARACTERIZATION) {
                checkType  (tag, type, ASCII);
                _colorCharacterization = readASCII (count, value);
            }
            else if (tag == COLORSEQUENCE) {
                checkType  (tag, type, ASCII);
                _colorSequence = readASCII (count, value);
            }
            else if (tag == COLORMAP) {
                checkType  (tag, type, SHORT);
                int [] colorMap = readShortArray (type, count, value);
                int [] bitCode = new int [colorMap.length];
                int [] red     = new int [colorMap.length];
                int [] green   = new int [colorMap.length];
                int [] blue    = new int [colorMap.length];
                int len = colorMap.length/3;
                int len2= 2*len;
                for (int i=0; i<len; i++) {
                    bitCode[i] = i;
                    red[i]     = colorMap[i];
                    green[i]   = colorMap[i + len];
                    blue[i]    = colorMap[i + len2];
                }
                _niso.setColormapBitCodeValue (bitCode);
                _niso.setColormapRedValue (red);
                _niso.setColormapGreenValue (green);
                _niso.setColormapBlueValue (blue);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == COLORTABLE) {
                checkType  (tag, type, BYTE);
                _colorTable = readByteArray (type, count, value);
            }
            else if (tag == COMPRESSEDBITSPERPIXEL) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _compressedBitsPerPixel = readRational (count, value);
            }
            else if (tag == COMPRESSION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                int scheme = readShort (type, count, value);
                _niso.setCompressionScheme (scheme);
                if (scheme == 5) {
                    // Set default predictor if none has been set
                    if (_predictor == NULL) {
                        _predictor = 1;
                    }
                    if ( _version < 5) {
                        _version = 5;
                    }
                }
                if (scheme == 6 && _version < 6) {
                    _version = 6;
                }
                if (scheme == 3 && _t4Options == NULL) {
                    // Set default t4Options only if compression is 3
                    _t4Options = 0;
                }
                if (scheme == 4 && _t6Options == NULL) {
                    // Set default t6Options only if compression is 4
                    _t6Options = 0;
                }
                if (scheme == 6) {
                    _info.setMessage(new InfoMessage
                          ("TIFF compression scheme 6 is deprecated"));
                }

            }
            else if (tag == CONSECUTIVEBADFAXLINES) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _consecutiveBadFaxLines = readLong (type, count, value);
            }
            else if (tag == COPYRIGHT) {
                checkType  (tag, type, ASCII);
                _copyright = readASCII (count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == DATETIME) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 20);
                _dateTime = readASCII (count, value);
                _niso.setDateTimeCreated (_dateTime);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == DATETIMEORIGINAL) {
                checkType  (tag, type, ASCII);
                checkCount (tag, count, 20);
                _niso.setDateTimeCreated (readASCII (count, value));
            }
            else if (tag == DOCUMENTNAME) {
                checkType  (tag, type, ASCII);
                _documentName = readASCII (count, value);
            }
            else if (tag == DOTRANGE) {
                checkType  (tag, type, BYTE, SHORT);
                checkCount (tag, count, 2);
                _dotRange = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == EXIFIFD) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _exifIFD = readLong (type, count, value);
            }
            else if (tag == EXPOSUREBIASVALUE) {
                checkType  (tag, type, SRATIONAL);
                if (count == 1) {
                    _niso.setExposureBias (readSignedRational (count,
							 value).toDouble ());
                }
                else {
                    Rational [] r = readSignedRationalArray (count, value);
                    _niso.setExposureBias (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == EXPOSUREPROGRAM) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _exposureProgram = readShort (type, count, value);
            }
            else if (tag == EXPOSURETIME) {
                checkType  (tag, type, RATIONAL);
                if (count == 1) {
                    _niso.setExposureTime (readRational (count,
							 value).toDouble ());
                }
                else {
                    Rational [] r = readRationalArray (count, value);
                    _niso.setExposureTime (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == EXTRASAMPLES) {
                checkType  (tag, type, SHORT);
                _niso.setExtraSamples (readShortArray (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == FILLORDER) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _fillOrder = readShort (type, count, value);
            }
            else if (tag == FLASH) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _flash = readShort (type, count, value);
                _niso.setFlash (_flash);
                _niso.setFlashReturn (((_flash & 0X6) != 0) ? 1 : 0);
            }
            else if (tag == FLASHENERGY) {
                checkType  (tag, type, RATIONAL);
                if (count == 1) {
                    _niso.setFlashEnergy (readRational (count,
							value).toDouble ());
                }
                else {
                    Rational [] r = readRationalArray (count, value);
                    _niso.setFlashEnergy (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == FNUMBER) {
                checkType  (tag, type, RATIONAL);
                if (count == 1) {
                    _niso.setFNumber (readRational (count, value).toDouble ());
                }
                else {
                    Rational [] r = readRationalArray (count, value);
                    _niso.setFNumber (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == FOCALLENGTH) {
                checkType  (tag, type, RATIONAL);
                if (count == 1) {
                    _niso.setFocalLength (readRational (count,
							value).toDouble ());
                }
                else {
                    Rational [] r = readRationalArray (count, value);
                    _niso.setFocalLength (average (r[0], r[1]).toDouble ());
                }
            }
            else if (tag == FOCALPLANERESOLUTIONUNIT) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _focalPlaneResolutionUnit = readShort (type, count, value);
                if (_niso.getSamplingFrequencyUnit () != NULL) {
                    _niso.setSamplingFrequencyUnit (_focalPlaneResolutionUnit);
                }
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
            else if (tag == FREEBYTECOUNTS) {
                checkType  (tag, type, LONG);
                _freeByteCounts = readLongArray (type, count, value);
            }
            else if (tag == FREEOFFSETS) {
                checkType  (tag, type, LONG);
                _freeOffsets = readLongArray (type, count, value);
            }
            else if (tag == GEOASCIIPARAMSTAG) {
                checkType  (tag, type, ASCII);
                _geoAsciiParamsTag = readASCII (count, value);
            }
            else if (tag == GEODOUBLEPARAMSTAG) {
                checkType  (tag, type, DOUBLE);
                _geoDoubleParamsTag = readDoubleArray (count, value);
            }
            else if (tag == GEOKEYDIRECTORYTAG) {
                checkType  (tag, type, SHORT);
                _geoKeyDirectoryTag = readShortArray (type, count, value);
                int num = _geoKeyDirectoryTag[3];
                int prevKey = -1;
                for (int i=0; i<num; i++) {
                    int j = i*4 + 4;
                    int key = _geoKeyDirectoryTag[j];
                    if (prevKey > key) {
                        throw new TiffException ("GeoKey " + key +
                                                 " out of sequence");
                    }
                    prevKey = key;
                }
            }
            else if (tag == GLOBALPARAMETERSIFD) {
                checkType  (tag, type, LONG, IFD);
                // RFC 2301 allows only IFD, but the latest working
                // draft allows LONG.  Even though allowing LONG 
                // technically isn't allowed yet, letting it by seems
                // reasonable, since other IFD tags can be LONG.
                checkCount (tag, count, 1);
                _globalParametersIFD = readLong (type, count, value);
            }
            else if (tag == GPSINFOIFD) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _gpsInfoIFD = readLong (type, count, value);
            }
            else if (tag == GRAYRESPONSECURVE) {
                checkType  (tag, type, SHORT);
                _niso.setGrayResponseCurve (readShortArray (type, count,
                                                            value));
            }
            else if (tag == GRAYRESPONSEUNIT) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setGrayResponseUnit (readShort (type, count, value));
            }
            else if (tag == HALFTONEHINTS) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 2);
                _halftoneHints = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == HCUSAGE) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _hcUsage = readLong (type, count, value);
            }
            else if (tag == HOSTCOMPUTER) {
                checkType  (tag, type, ASCII);
                _niso.setHostComputer (readASCII (count, value));

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == IMAGEDESCRIPTION) {
                checkType  (tag, type, ASCII);
                _imageDescription = readASCII (count, value);
            }
            else if (tag == IMAGEID) {
                checkType  (tag, type, ASCII);
                _niso.setImageIdentifier (readASCII (count, value));
            }
            else if (tag == IMAGECOLORINDICATOR) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _imageColorIndicator = readByte (type, count, value);
            }
            else if (tag == IMAGECOLORVALUE) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _imageColorValue = readByte (type, count, value);
            }
            else if (tag == IMAGEHISTORY) {
                checkType  (tag, type, ASCII);
                _imageHistory = readASCII (count, value);
            }
            else if (tag == IMAGELAYER) {
                checkType (tag, type, SHORT, LONG);
                checkCount (tag, count, 2);
                _imageLayer = readShortArray (type, count, value);
            }
            else if (tag == IMAGELENGTH) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _niso.setImageLength (readLong (type, count, value));
            }
            else if (tag == IMAGENUMBER) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _imageNumber = readLong (type, count, value);
            }
            else if (tag == IMAGESOURCEDATA) {
                checkType  (tag, type, UNDEFINED);
                //_imageSourceData = readByteArray (type, count, value);
                // GDM 16-Sep-2005:
                // The ImageSourceData tag sometimes has a gigantic
                // amount of data, and we don't actually do anything with
                // it in the current version of JHOVE except determine if
                // it's there.  
                _imageSourceData = new int[] {1};
            }
            else if (tag == PHOTOSHOPPROPS) {
                // Can't find any info on what type is expected.
                _photoshopProperties = readByteArray (type, count, value);
            }
            else if (tag == ANNOTATIONS) {
                // Can't find any info on what type is expected.
                _annotations = readByteArray (type, count, value);
            }
            else if (tag == IMAGEWIDTH) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _niso.setImageWidth (readLong (type, count, value));
            }
            else if (tag == INDEXED) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _indexed = readShort (type, count, value);
            }
            else if (tag == INKNAMES) {
                checkType  (tag, type, ASCII);
                _inkNames = readASCIIArray (count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == INKSET) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _inkSet = readShort (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == ICC_PROFILE) {
                checkType  (tag, type, UNDEFINED);
                _interColourProfile = readByteArray (type, count, value);
            }
            else if (tag == INTERLACE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _interlace = readShort (type, count, value);
            }
            else if (tag == INTEROPERABILITYIFD) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _interoperabilityIFD = readLong (type, count, value);
            }
            else if (tag == IPTCNAA) {
                
                if (type == ASCII) {
                    String s = readASCII (count, value);
                    long [] larray = new long [s.length ()];
                    for (int i=0; i<s.length (); i++) {
                        larray[i] = (int) s.charAt (i);
                    }
                    _iptc = larray;
                }
                else if (type == LONG) {
                    _iptc = readLongArray (type, count, value);
                }
                else {
                    checkType  (tag, type, BYTE, UNDEFINED);
                    int[] b = readByteArray(type, count, value);
                    long [] larray = new long [b.length];
                    for (int i = 0; i < b.length; i++) {
                        larray[i] = b[i];
                        _iptc = larray;
                    }
                }
            }
            else if (tag == ISOSPEEDRATINGS) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _isoSpeedRatings = readShortArray (tag, count, value);
            }
            else if (tag == IT8HEADER) {
                checkType  (tag, type, ASCII);
                _it8Header = readASCII (count, value);
            }
            else if (tag == JPEGACTABLES) {
                checkType  (tag, type, LONG);
                _jpegACTables = readLongArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGDCTABLES) {
                checkType  (tag, type, LONG);
                _jpegDCTables = readLongArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGINTERCHANGEFORMAT) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _jpegInterchangeFormat = readLong (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGINTERCHANGEFORMATLENGTH) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _jpegInterchangeFormatLength = readLong (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGLOSSLESSPREDICTORS) {
                checkType  (tag, type, SHORT);
                _jpegLosslessPredictors = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGPOINTTRANSFORMS) {
                checkType  (tag, type, SHORT);
                _jpegPointTransforms = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGPROC) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _jpegProc = readShort (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGQTABLES) {
                checkType  (tag, type, LONG);
                _jpegQTables = readLongArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGRESTARTINTERVAL) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _jpegRestartInterval = readShort (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == JPEGTABLES) {
                checkType  (tag, type, UNDEFINED);
                _jpegTables = readByteArray (type, count, value);
            }
            else if (tag == LIGHTSOURCE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setSceneIlluminant (readShort (type, count, value));
            }
            else if (tag == MAKE) {
                checkType  (tag, type, ASCII);
                _niso.setScannerManufacturer (readASCII (count, value));
            }
            else if (tag == MAXAPERTUREVALUE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _maxAperatureValue = readRational (count, value);
            }
            else if (tag == MAXSAMPLEVALUE) {
                checkType  (tag, type, SHORT);
                _maxSampleValue = readShortArray (type, count, value);
            }
            else if (tag == METERINGMODE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setMeteringMode (readShort (type, count, value));
            }
            else if (tag == MINSAMPLEVALUE) {
                checkType  (tag, type, SHORT);
                _minSampleValue = readShortArray (type, count, value);
            }
            else if (tag == MODEL) {
                checkType  (tag, type, ASCII);
                _niso.setScannerModelName (readASCII (count, value));
            }
            else if (tag == MODELPIXELSCALETAG) {
                checkType  (tag, type, DOUBLE);
                checkCount (tag, count, 3);
                _modelPixelScaleTag = readDoubleArray (count, value);
            }
            else if (tag == MODELTIEPOINTTAG) {
                checkType  (tag, type, DOUBLE);
                _modelTiepointTag = readDoubleArray (count, value);
            }
            else if (tag == MODELTRANSFORMATIONTAG) {
                checkType  (tag, type, DOUBLE);
                checkCount (tag, count, 16);
                _modelTransformationTag = readDoubleArray (count, value);
            }
            else if (tag == NEWSUBFILETYPE) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _newSubfileType = readLong (type, count, value);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == NOISE) {
                checkType  (tag, type, UNDEFINED);
                _noise = readByteArray (type, count, value);
            }
            else if (tag == NUMBEROFINKS) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _numberOfInks = readShort (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == OECF) {
                checkType  (tag, type, UNDEFINED);
                _oecf = readByteArray (tag, count, value);
            }
            else if (tag == OPIPROXY) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _opiProxy = readShort (type, count, value);
            }
            else if (tag == ORIENTATION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setOrientation (readShort (type, count, value));
            }
            else if (tag == PAGENAME) {
                checkType  (tag, type, ASCII);
                _pageName = readASCII (count, value);
            }
            else if (tag == PAGENUMBER) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 2);
                _pageNumber = readShortArray (type, count, value);
            }
            else if (tag == PHOTOMETRICINTERPRETATION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _photometricInterpretation = readShort (type, count, value);
                _niso.setColorSpace (_photometricInterpretation);

                // Set default values appropriate to interpretation, 
                // only if no value has been set.
                if (_photometricInterpretation == 5) {
                    if (_inkSet == NULL) {
                        _inkSet = 1;
                    }
                    if (_numberOfInks == NULL) {
                        _numberOfInks = 4;   
                    }
                }
            	else if (_photometricInterpretation == 6) {
            	    if (_niso.getYCbCrCoefficients() == null) {
            		_niso.setYCbCrCoefficients (new
            		    Rational [] {new Rational (299, 1000),
            				 new Rational (587, 1000),
            				 new Rational (114, 1000)});
            	    }
            	    if (_niso.getYCbCrPositioning () == NULL) {
            		_niso.setYCbCrPositioning (1);
            	    }
            	    if (_niso.getYCbCrSubSampling () == null) {
            		_niso.setYCbCrSubSampling (new int [] {2, 2});
            	    }
            	}
            
            	int colorSpace = _niso.getColorSpace ();
            	if (colorSpace == 3 || colorSpace == 4) {
            	    if (_version < 5) {
            		_version = 5;
            	    }
            	}
            	else if (colorSpace == 5 || colorSpace == 6 ||
            		 colorSpace == 8) {
                        if (_version < 6) {
                        _version = 6;
                        }
            	}
            }
            else if (tag == PIXELINTENSITYRANGE) {
                checkType  (tag, type, BYTE);
                _pixelIntensityRange = readShortArray (type, count, value);
            }
            else if (tag == PLANARCONFIGURATION) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setPlanarConfiguration (readShort (type, count, value));
            }
            else if (tag == PREDICTOR) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _predictor = readShort (type, count, value);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == PRIMARYCHROMATICITIES) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 6);
                Rational [] rarray = readRationalArray (count, value);
                _niso.setPrimaryChromaticitiesRedX   (rarray[0]);
                _niso.setPrimaryChromaticitiesRedY   (rarray[1]);
                _niso.setPrimaryChromaticitiesGreenX (rarray[2]);
                _niso.setPrimaryChromaticitiesGreenY (rarray[3]);
                _niso.setPrimaryChromaticitiesBlueX  (rarray[4]);
                _niso.setPrimaryChromaticitiesBlueY  (rarray[5]);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == RASTERPADDING) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _rasterPadding = readShort (type, count, value);
            }
            else if (tag == REFERENCEBLACKWHITE) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 6);
                _niso.setReferenceBlackWhite (readRationalArray(count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == RESOLUTIONUNIT) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setSamplingFrequencyUnit (readShort(type, count, value));
            }
            else if (tag == ROWSPERSTRIP) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _niso.setRowsPerStrip (readLong (type, count, value));
            }
            else if (tag == SAMPLEFORMAT) {
                checkType  (tag, type, SHORT);
                _sampleFormat = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == SAMPLESPERPIXEL) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setSamplesPerPixel (readShort (type, count, value));
            }
            else if (tag == SECURITYCLASSIFICATION) {
                checkType  (tag, type, ASCII);
                _securityClassification = readASCII (count, value);
            }
            else if (tag == SELFTIMERMODE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _selfTimerMode = readShort (type, count, value);
            }
            else if (tag == SENSINGMETHOD) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setSensor (readShort (type, count, value));
            }
            else if (tag == SITE) {
                checkType  (tag, type, ASCII);
                _site = readASCII (count, value);
            }
            else if (tag == STRIPROWCOUNTS) {
                checkType  (tag, type, LONG);
                _stripRowCounts = readLongArray(type, count, value);
            }
            else if (tag == SUBJECTDISTANCE) {
                checkType  (tag, type, RATIONAL, SRATIONAL);
                double [] darray = new double [2];
                if (count == 1) {
                    darray[0] = readRational (count, value).toDouble ();
                    darray[1] = darray[0];
                }
                else {
                    Rational [] r;
                    if (type == RATIONAL) {
                        r = readRationalArray (count, value);
                    }
                    else {
                        r = readSignedRationalArray (count, value);
                    }
                    darray[0] = r[0].toDouble ();
                    if (r.length > 1) {
                        darray[1] = r[1].toDouble ();
                    }
                    else {
                        darray[1] = darray[0];
                    }
                }
                _niso.setSubjectDistance (darray);
            }
            else if (tag == SOFTWARE) {
                checkType  (tag, type, ASCII);
                _niso.setScanningSoftware (readASCII (count, value));

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == SPATIALFREQUENCYRESPONSE) {
                checkType  (tag, type, UNDEFINED);
                _spatialFrequencyResponse = readByteArray (type, count, value);
            }
            else if (tag == SPECTRALSENSITIVITY) {
                checkType  (tag, type, ASCII);
                _spectralSensitivity = readASCII (count, value);
            }
            else if (tag == STRIPBYTECOUNTS) {
                checkType  (tag, type, SHORT, LONG);
                _niso.setStripByteCounts (readLongArray (type, count, value));
            }
            else if (tag == STRIPOFFSETS) {
                checkType  (tag, type, SHORT, LONG);
                _niso.setStripOffsets (readLongArray (type, count, value));
            }
            else if (tag == SUBFILETYPE) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _subfileType = readShort (type, count, value);
            }
            else if (tag == SUBIFDS) {
                checkType  (tag, type, LONG, IFD);
                _subIFDs = readLongArray (type, count, value);
            }
            else if (tag == SUBJECTLOCATION) {
                checkType  (tag, type, SHORT);
                _subjectLocation = readShortArray (type, count, value);
            }
            else if (tag == T4OPTIONS) {
                checkType  (tag, type, LONG);
                _t4Options = readShort (type, count, value);
            }
            else if (tag == T6OPTIONS) {
                checkType  (tag, type, LONG);
                _t6Options = readShort (type, count, value);
            }
            else if (tag == TARGETPRINTER) {
                checkType  (tag, type, ASCII);
                _targetPrinter = readASCII (count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == THRESHHOLDING) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _threshholding = readShort (type, count, value);
            }
            else if (tag == TIFFEPSTANDARDID) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 4);
                int [] iarray = readShortArray (type, count, value);
                _tiffEPStandardID = Integer.toString (iarray[0]) + "." +
                                    Integer.toString (iarray[1]) + "." +
                                    Integer.toString (iarray[2]) + "." +
                                    Integer.toString (iarray[3]);
            }
            else if (tag == TILEBYTECOUNTS) {
                checkType  (tag, type, SHORT, LONG);
                _niso.setTileByteCounts (readLongArray (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == TILELENGTH) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _niso.setTileLength (readLong (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == TILEOFFSETS) {
                checkType  (tag, type, SHORT, LONG);
                _niso.setTileOffsets (readLongArray (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == TILEWIDTH) {
                checkType  (tag, type, SHORT, LONG);
                checkCount (tag, count, 1);
                _niso.setTileWidth (readLong (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == TIMEZONEOFFSET) {
                checkType  (tag, type, SSHORT);
                _timeZoneOffset = readSShortArray (type, count, value);
            }
            else if (tag == TRANSFERFUNCTION) {
                /* Transfer function arrays potentially can have millions
                 * of elements, so we just report presence */
                checkType  (tag, type, SHORT);
                _transferFunction = true;
            }
            else if (tag == TRANSFERRANGE) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 6);
                _transferRange = readShortArray (type, count, value);

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == TRANSPARENCYINDICATOR) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _transparencyIndicator = readByte (type, count, value);
            }
            else if (tag == WHITEPOINT) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 2);
                Rational [] rarray = readRationalArray (count, value);
                _niso.setWhitePointXValue (rarray[0]);
                _niso.setWhitePointYValue (rarray[0]);

                if (_version < 5) {
                    _version = 5;
                }
            }
            else if (tag == XCLIPPATHUNITS) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _xClipPathUnits = readLong (type, count, value);
            }
            else if (tag == XPOSITION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _xPosition = readRational (count, value);
            }
            else if (tag == XRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _niso.setXSamplingFrequency (readRational (count,
                                                           value));
            }
            else if (tag == YCBCRCOEFFICIENTS) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 3);
                _niso.setYCbCrCoefficients (readRationalArray (count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == YCBCRPOSITIONING) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 1);
                _niso.setYCbCrPositioning (readShort (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == YCBCRSUBSAMPLING) {
                checkType  (tag, type, SHORT);
                checkCount (tag, count, 2);
                _niso.setYCbCrSubSampling(readShortArray (type, count, value));

                if (_version < 6) {
                    _version = 6;
                }
            }
            else if (tag == YCLIPPATHUNITS) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _yClipPathUnits = readLong (type, count, value);
            }
            else if (tag == YPOSITION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _yPosition = readRational (count, value);
            }
            else if (tag == YRESOLUTION) {
                checkType  (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _niso.setYSamplingFrequency (readRational (count,
                                                           value));
            }
            else if (tag == XMP) {
                checkType (tag, type, UNDEFINED, BYTE);
                _xmpProp = readXMP (count, value);
            }
            else if (tag == DNGVERSION) {
                checkType (tag, type, BYTE);
                checkCount (tag, count, 4);
                _dngVersion = readByteArray (type, count, value);
            }
            else if (tag == DNGBACKWARDVERSION) {
                checkType (tag, type, BYTE);
                checkCount (tag, count, 4);
                _dngBackwardVersion = readByteArray (type, count, value);
            }
            else if (tag == UNIQUECAMERAMODEL) {
                checkType (tag, type, ASCII);
                _uniqueCameraModel = readASCII(count, value);
            }
            else if (tag == LOCALIZEDCAMERAMODEL) {
                checkType (tag, type, ASCII, BYTE);
                // This tag is specified as UTF-8
                byte[] lcm = readTrueByteArray(type, count, value);
                // Trim off trailing null (s)
                int len = lcm.length;
                while (len > 0 && lcm[len - 1] == 0) {
                    len--;
                }
                _localizedCameraModel = new String (lcm, 0, len);
                
            }
            else if (tag == CFAPLANECOLOR) {
                checkType (tag, type, BYTE);
                _cfaPlaneColor = readByteArray (type, count, value);
            }
            else if (tag == CFALAYOUT) {
                checkType (tag, type, SHORT);
                _cfaLayout = readShort(type, count, value);
            }
            else if (tag == LINEARIZATIONTABLE) {
                checkType (tag, type, SHORT);
                _linearizationTable = readShortArray(type, count, value);
            }
            else if (tag == BLACKLEVELREPEATDIM) {
                checkType (tag, type, SHORT);
                _blackLevelRepeatDim = readShortArray(type, count, value);
            }
            else if (tag == BLACKLEVEL) {
                // Just to make things complicated, this can be SHORT, LONG
                // or RATIONAL.  To give these a least common (pardon the 
                // expression) denominator, we convert all to rational.
                if (type == RATIONAL) {
                    _blackLevel = readRationalArray(count, value);
                }
                else {
                    checkType (tag, type, SHORT, LONG);
                    long[] ibl = readLongArray(type, count, value);
                    _blackLevel = new Rational[(int) count];
                    for (int i = 0; i < count; i++) {
                        _blackLevel[i] = new Rational (ibl[i], 1);
                    }
                }
            }
            else if (tag == BLACKLEVELDELTAH) {
                checkType (tag, type, SRATIONAL);
                _blackLevelDeltaH = readSignedRationalArray (count, value);
            }
            else if (tag == BLACKLEVELDELTAV) {
                checkType (tag, type, SRATIONAL);
                _blackLevelDeltaV = readSignedRationalArray (count, value);
            }
            else if (tag == WHITELEVEL) {
                checkType (tag, type, SHORT, LONG);
                _whiteLevel = readLongArray (type, count, value);
            }
            else if (tag == DEFAULTSCALE) {
                checkType (tag, type, RATIONAL);
                checkCount (tag, count, 2);
                _defaultScale = readRationalArray (count, value);
            }
            else if (tag == BESTQUALITYSCALE) {
                checkType (tag, type, RATIONAL);
                checkCount (tag, count, 1);
                _bestQualityScale = readRational (count, value);
            }
            else if (tag == DEFAULTCROPORIGIN) {
                checkCount (tag, count, 2);
                // Just to make things complicated, this can be SHORT, LONG
                // or RATIONAL.  To give these a least common (pardon the 
                // expression) denominator, we convert all to rational.
                if (type == RATIONAL) {
                    _defaultCropOrigin = readRationalArray(count, value);
                }
                else {
                    checkType (tag, type, SHORT, LONG);
                    long[] lco = readLongArray(type, count, value);
                    _defaultCropOrigin = new Rational[(int) count];
                    for (int i = 0; i < count; i++) {
                        _defaultCropOrigin[i] = new Rational (lco[i], 1);
                    }
                }
            }
            else if (tag == DEFAULTCROPSIZE) {
                checkCount (tag, count, 2);
                if (type == RATIONAL) {
                    _defaultCropSize = readRationalArray(count, value);
                }
                else {
                    checkType (tag, type, SHORT, LONG);
                    long[] lcs = readLongArray(type, count, value);
                    _defaultCropSize = new Rational[(int) count];
                    for (int i = 0; i < count; i++) {
                        _defaultCropSize[i] = new Rational (lcs[i], 1);
                    }
                }
            }
            else if (tag == CALIBRATIONILLUMINANT1) {
                checkCount (tag, count, 1);
                checkType (tag, type, SHORT);
                _calibrationIlluminant1 = readShort(type, count, value);
            }
            else if (tag == CALIBRATIONILLUMINANT2) {
                checkCount (tag, count, 1);
                checkType (tag, type, SHORT);
                _calibrationIlluminant2 = readShort(type, count, value);
            }
            else if (tag == COLORMATRIX1) {
                checkType (tag, type, SRATIONAL);
                _colorMatrix1 = readSignedRationalArray (count, value);
            }
            else if (tag == COLORMATRIX2) {
                checkType (tag, type, SRATIONAL);
                _colorMatrix2 = readSignedRationalArray (count, value);
            }
            else if (tag == CAMERACALIBRATION1) {
                checkType (tag, type, SRATIONAL);
                _colorMatrix1 = readSignedRationalArray (count, value);
            }
            else if (tag == CAMERACALIBRATION2) {
                checkType (tag, type, SRATIONAL);
                _colorMatrix2 = readSignedRationalArray (count, value);
            }
            else if (tag == REDUCTIONMATRIX1) {
                checkType (tag, type, SRATIONAL);
                _reductionMatrix1 = readSignedRationalArray (count, value);
            }
            else if (tag == REDUCTIONMATRIX2) {
                checkType (tag, type, SRATIONAL);
                _reductionMatrix2 = readSignedRationalArray (count, value);
            }
            else if (tag == ANALOGBALANCE) {
                checkType (tag, type, RATIONAL);
                _analogBalance = readRationalArray (count, value);
            }
            else if (tag == ASSHOTNEUTRAL) {
                // this can be either SHORT or RATIONAL
                checkType (tag, type, SHORT, RATIONAL);
                if (type == SHORT) {
                    int[] asn = readShortArray (type, count, value);
                    _asShotNeutral = new Rational [(int) count];
                    for (int i = 0; i < count; i++) {
                        _asShotNeutral[i] = new Rational (asn[i], 1);
                    }
                }
                else {
                    _asShotNeutral = readRationalArray (count, value);
                }
            }
            else if (tag == ASSHOTWHITEXY) {
                checkType (tag, type, RATIONAL);
                checkCount (tag, count, 2);
                _asShotWhiteXY = readRationalArray (count, value);
            }
            else if (tag == BASELINEEXPOSURE) {
                checkType (tag, type, SRATIONAL);
                _baselineExposure = readSignedRational (count, value);
            }
            else if (tag == BASELINENOISE) {
                checkType (tag, type, RATIONAL);
                _baselineNoise = readRational (count, value);
            }
            else if (tag == BASELINESHARPNESS) {
                checkType (tag, type, RATIONAL);
                _baselineSharpness = readRational (count, value);
            }
            else if (tag == BAYERGREENSPLIT) {
                checkType (tag, type, LONG);
                _bayerGreenSplit = (int) readLong(type, count, value);
            }
            else if (tag == LINEARRESPONSELIMIT) {
                checkType (tag, type, RATIONAL);
                _linearResponseLimit = readRational (count, value);
            }
            else if (tag == CAMERASERIALNUMBER) {
                checkType (tag, type, ASCII);
                _cameraSerialNumber = readASCII(count, value);
            }
            else if (tag == LENSINFO) {
                checkType (tag, type, RATIONAL);
                checkCount (tag, count, 4);
                _lensInfo = readRationalArray (count, value);
            }
            else if (tag == CHROMABLURRADIUS) {
                checkType (tag, type, RATIONAL);
                _chromaBlurRadius = readRational (count, value);
            }
            else if (tag == ANTIALIASSTRENGTH) {
                checkType (tag, type, RATIONAL);
                _antiAliasStrength = readRational (count, value);
            }
            else if (tag == SHADOWSCALE) {
                _info.setMessage (new InfoMessage ("Undocumented TIFF tag ",
                    "ShadowScale (50739)"));
            }
            else if (tag == DNGPRIVATEDATA) {
                checkType (tag, type, BYTE);
                _dngPrivateData = readByteArray (type, count, value);
            }
            else if (tag == MAKERNOTESAFETY) {
                checkType (tag, type, SHORT);
                _makerNoteSafety = readShort (type, count, value);
            }
            else {
                _info.setMessage (new InfoMessage ("Unknown TIFF IFD " +
                                                    "tag: " + tag, value));
            }
        }
        catch (IOException e) {
            throw new TiffException ("Read error for tag " + tag, value);
        }
    }

    /** Perform initializations that have to wait until after the
     * IFD has been parsed.
     */
    protected void postParseInitialization ()
    {
        int samplesPerPixel = _niso.getSamplesPerPixel ();
        int [] bitsPerSample = _niso.getBitsPerSample ();
        if (bitsPerSample == null) {
            bitsPerSample = new int [samplesPerPixel];
            for (int i=0; i<samplesPerPixel; i++) {
                bitsPerSample[i] = 1;
            }
            _niso.setBitsPerSample (bitsPerSample);
        }
        int bps1 = (1<<bitsPerSample[0]) - 1;
        if (_maxSampleValue == null) {
            _maxSampleValue = new int [samplesPerPixel];
            for (int i=0; i<samplesPerPixel; i++) {
                _maxSampleValue[i] = bps1;
            }

        }
        if (_minSampleValue == null) {
            _minSampleValue = new int [samplesPerPixel];
            for (int i=0; i<samplesPerPixel; i++) {
                _minSampleValue[i] = 0;
            }
        }
        if (_sampleFormat == null) {
            _sampleFormat = new int [samplesPerPixel];
            for (int i=0; i<samplesPerPixel; i++) {
                _sampleFormat[i] = 1;
            }
        }
          /* The default transfer function is expressed as an array
           * of 2^BitsPerSample elements.  If BitsPerSample is 24,
           * this would paraylze processing for many minutes, if it
           * didn't just run out of memory.  So it was a nice idea... */
//        if (_photometricInterpretation == 0 ||
//            _photometricInterpretation == 1 ||
//            _photometricInterpretation == 2 ||
//            _photometricInterpretation == 3 ||
//            _photometricInterpretation == 6) {
//            // Set default transfer function only for indicated 
//            // photometricInterpretations.
//            if (_transferFunction == null) {
//                int n = 1<<bitsPerSample[0];
//                _transferFunction = new int [n];
//                _transferFunction[0] = 0;
//                for (int i=1; i<n; i++) {
//                    _transferFunction[i] =
//			(int) Math.floor (Math.pow (i/(n-1.0), 2.2)*65535 +
//					  0.5);
//                }
//            }
//        }
	if (_photometricInterpretation == 5) {
	    if (_dotRange == null) {
		_dotRange = new int [2];
		_dotRange[0] = 0;
		_dotRange[1] = bps1;
	    }
	}
        if (_photometricInterpretation == 2 ||
	    _photometricInterpretation == 6) {
            // set defaults for transferRange and referenceBlackWhite only if
            // the photometricInterpretation is RGB or YCbCr.
            if (_transferRange == null) {
                _transferRange = new int [6];
                _transferRange[0] =_transferRange[2] =_transferRange[4] = 0;
                _transferRange[1] =_transferRange[3] =_transferRange[5] = bps1;
            }
            if (_niso.getReferenceBlackWhite () == null) {
                Rational [] reference = new Rational[6];
                reference[0] = reference[2] = reference[4] = new Rational(0,1);
                reference[1] = reference[3] = reference[5] = new Rational(bps1,
									  1);
                _niso.setReferenceBlackWhite (reference);
            }
        }
        if (_pixelIntensityRange == null) {
            _pixelIntensityRange = new int [2];
            _pixelIntensityRange[0] = 0;
            _pixelIntensityRange[1] = bps1;
        }
    }

    public void setTheExifIFD (ExifIFD exif)
    {
        _theExifIFD = exif;
    }

    public void setTheGPSInfoIFD (GPSInfoIFD gpsInfo)
    {
        _theGPSInfoIFD = gpsInfo;
    }

    public void setTheInteroperabilityIFD (InteroperabilityIFD interOp)
    {
        _theInteroperabilityIFD = interOp;
    }
    
    public void setTheGlobalParametersIFD (GlobalParametersIFD gp)
    {
        _theGlobalParametersIFD = gp;
    }

    /* Read XMP data from the tag, and return as a string. */
    private Property readXMP (long count, long value)
                throws TiffException
    {
        Property xmpProp = null;
        final String badMetadata = "Invalid or ill-formed XMP metadata"; 
        try {
            byte[] buf = readTrueByteArray (BYTE, count, value);
            ByteArrayInputStream strm = 
                new ByteArrayInputStream (buf);
            ByteArrayXMPSource src = new ByteArrayXMPSource (strm);

            // Create an InputSource to feed the parser.
            SAXParserFactory factory = 
                            SAXParserFactory.newInstance();
            factory.setNamespaceAware (true);
            XMLReader parser = factory.newSAXParser ().getXMLReader ();
            //InputStream stream = new XMLWrapperStream 
            //    (new StreamInputStream (metadata, getFile ()), "dummyroot");
            XMPHandler handler = new XMPHandler ();
            parser.setContentHandler (handler);
            // We have to parse twice.  The first time, we may get
            // an encoding change as part of an exception thrown.  If this
            // happens, we create a new InputSource with the encoding, and
            // continue.
            try {
                parser.parse (src);
                xmpProp = src.makeProperty ();
                return xmpProp;
            }
            catch (SAXException se) {
                String msg = se.getMessage ();
                if (msg != null && msg.startsWith ("ENC=")) {
                    String encoding = msg.substring (5);
                    try {
                        //Reader rdr = new InputStreamReader (stream, encoding);
                        src = new ByteArrayXMPSource (strm, encoding);
                        parser.parse (src);
                    }
                    catch (UnsupportedEncodingException uee) {
                        throw new TiffException (badMetadata);
                    }
                }
                xmpProp = src.makeProperty ();
                return xmpProp;
            }
        }
        catch (TiffException e) {
            throw e;
        }
        catch (Exception f) {
            return null;
        }
    }
}
