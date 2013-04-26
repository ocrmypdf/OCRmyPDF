/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

/**
 *  A class for enumerating TIFF tag numbers and labels, and
 *  associating one with the other.  This class is never
 *  instantiated; all its methods and data are static.
 */
public class TiffTags
{
    /** TIFF tag labels. */
    private static final String [] TAG_LABELS = {
        /* 254-257 */
        "NewSubFileType", "SubFileType", "ImageWidth", "ImageLength", 
        /* 258-262 */
        "BitsPerSample", "Compression", "PhotometricInterpretation", 
        /* 263-266 */
        "Thresholding", "CellWidth", "CellLength", "FillOrder", 
        /* 269-273 */
        "DocumentName", "ImageDescription", "Make", "Model", "StripOffsets", 
        /* 274-279 */
        "Orientation", "SamplesPerPixel", "RowsPerStrip", "StripByteCounts", 
        /* 280-283 */
        "MinSampleValue", "MaxSampleValue", "XResolution", "YResolution", 
        /* 284-287 */
        "PlanarConfiguration", "PageName", "XPosition", "YPosition", 
        /* 288-290 */
        "FreeOffsets", "FreeByteCounts", "GrayResponseUnit",
        /* 291-293 */
        "GrayResponseCurve", "Group3Options", "Group4Options", 
        /* 296-300 */
        "ResolutionUnit", "PageNumber", "ColorResponseUnit", 
        /* 301-316 */
        "TransferFunction", "Software", "DateTime", "Artist", "HostComputer", 
        /* 317-320 */
        "Predictor", "WhitePoint", "PrimaryChromacities", "ColorMap", 
        /* 321-324 */
        "HalftoneHints", "TileWidth", "TileLength", "TileOffsets", 
        /* 325-327 */
        "TileByteCounts", "BadFaxLines", "CleanFaxData",
        /* 328-333 */
        "ConsecutiveBadFaxLines", "SubIFDs", "InkSet", "InkNames", 
        /* 334-338 */
        "NumberOfInks", "DotRange", "TargetPrinter", "ExtraSamples", 
        /* 339-342 */
        "SampleFormat", "SMinSampleValue", "SMaxSampleValue", "TransferRange", 
        /* 343-346 */
        "ClipPath", "XClipPathUnits", "YClipPathUnits", "Indexed", 
        /* 347-400 */
        "JPEGTables", "OPIProxy", "GlobalParametersIFD",
        /* 401-405 */
        "ProfileType", "FaxProfile", "CodingMethods", "VersionYear", "ModeNumber",
        /* 512-513 */
         "JPEGProc", "JPEGInterchangeFormat", 
        /* 514-515 */
        "JPEGInterchangeFormatLength", "JPEGRestartInterval", 
        /* 517-519 */
        "JPEGLosslessPredictors", "JPEGPointTransforms", "JPEGQTables", 
        /* 520-529 */
        "JPEGDCTables", "JPEGACTables", "YCbCrCoefficients", 
        /* 530-532 */
        "YCbCrSubsampling", "YCbCrPositioning", "ReferenceBlackWhite", 
        /* 559 */
        "StripRowCounts",
        /* 32781-5 */
        "ImageID", "Matteing", "DataType", "ImageDepth", "TileDepth", 
        /* 32786-33432 */
        "CFARepeatPatternDim", "CFAPattern", "BatteryLevel", "Copyright", 
        /* 33434-33550 */
        "ExposureTime", "Fnumber", "IPTC/NAA", "ModelPixelScaleTag", 
        /* 33920-34017 */
        "IntergraphMatrixTag", "ModelTiepointTag", "Site", "ColorSequence", 
        /* 34018-34020 */
        "IT8Header", "RasterPadding", "BitsPerRunLength",
        /* 34021-3 */
        "BitsPerExtendedRunLength", "ColorTable", "ImageColorIndicator", 
        /* 34024-6 */
        "BackgroundColorIndicator", "ImageColorValue", "BackgroundColorValue", 
        /* 34027-8 */
        "PixelInensityRange", "TransparencyIndicator",
        /* 34029-34264 */
        "ColorCharacterization", "HCUsage", "ModelTransformationTag", 
        /* 34377 */
        "ImageResources",
        /* 34665-34735 */
        "ExifIFD", "InterColourProfile", "ImageLayer", "GeoKeyDirectoryTag", 
        /* 34736-34850 */
        "GeoDoubleParamsTag", "GeoAsciiParamsTag", "ExposureProgram", 
        /* 34852-34856 */
        "SpectralSensitivity", "GPSInfo", "ISOSpeedRatings", "OECF", 
        /* 34857-34908 */
        "Interlace", "TimeZoneOffset", "SelfTimerMode", "FaxRecvParams", 
        /* 34909-36867 */
        "FaxSubAddress", "FaxRecvTime", "DateTimeOriginal", 
        /* 37122-37378 */
        "CompressedBitsPerPixel", "ShutterSpeedValue", "ApertureValue", 
        /* 37379-37381 */
        "BrightnessValue", "ExposureBiasValue", "MaxApertureValue", 
        /* 37382-5 */
        "SubjectDistance", "MeteringMode", "LightSource", "Flash", 
        /* 37386-8 */
        "FocalLength", "FlashEnergy", "SpatialFrequencyResponse", 
        /* 37389-37391 */
        "Noise", "FocalPlaneXResolution", "FocalPlaneYResolution", 
        /* 37392-4 */
        "FocalPlaneResolutionUnit", "ImageNumber", "SecurityClassification", 
        /* 37395-7 */
        "ImageHistory", "SubjectLocation", "ExposureIndex", 
        /* 37398-37724 */
        "TIFF/EPStandardID", "SensingMethod", "StoNits", "ImageSourceData", 
        /* 40965- 50255 */
        "InteroperabilityIFD", "Annotations",
        /* 50706-50712 */
        "DNGVersion", "DNGBackwardVersion", "UniqueCameraModel", 
        "LocalizedCameraModel", "CFAPlaneColor", "CFALayout", "LinearizationTable",
        /* 50713-18 */
        "BlackLevelRepeatDim", "BlackLevel", "BlackLevelDeltaH",
        "BlackLevelDeltaV", "WhiteLevel", "DefaultScale",
        /* 50719-22 */
        "DefaultCropOrigin", "DefaultCropSize", "ColorMatrix1", "ColorMatrix2",
        /* 50723-26 */
        "CameraCalibration1", "CameraCalibration2", 
        "ReductionMatrix1", "ReductionMatrix2",
        /* 50727-32 */
        "AnalogBalance", "AsShotNeutral", "AsShotWhiteXY",
        "BaselineExposure", "BaselineNoise", "BaselineSharpness",
        /* 50733-5 */
        "BayerGreenSplit", "LinearResponseLimit", "CameraSerialNumber",
        /* 50736-9 */
        "LensInfo", "ChromaBlurRadius", "AntiAliasStrength", "ShadowScale",
        /* 50740-1 */
        "DNGPrivateData", "MakerNoteSafety",
        /* 50778-80 */
        "CalibrationIlluminant1", "CalibrationIlluminant2", "BestQualityScale"
    };

    /** TIFF tag label indices. */
    private static final int [] TAG_INDEX = {
        254, 255, 256, 257,
	258, 259, 262,
	263, 264, 265, 266,
	269, 270, 271, 272, 273,
	274, 277, 278, 279,
	280, 281, 282, 283,
	284, 285, 286, 287,
	288, 289, 290,
	291, 292, 293,
	296, 297, 300,
	301, 305, 306, 315, 316,
	317, 318, 319, 320,
	321, 322, 323, 324,
	325, 326, 327,
	328, 330, 332, 333,
	334, 336, 337, 338,
	339, 340, 341, 342,
        343, 344, 345, 346,
	347, 351, 400,
	401, 402, 403, 404, 405,
        512, 513,
	514, 515,
	517, 518, 519,
        520, 521, 529,
	530, 531, 532,
	559,
        32781, 32995, 32996, 32997, 32998,
	33421, 33422, 33423, 33432,
	33434, 33437, 33723, 33550,
	33920, 33922, 34016, 34017,
        34018, 34019, 34020,
	34021, 34022, 34023,
	34024, 34025, 34026,
        34027, 34028,
	34029, 34030, 34264,
	34377,
	34665, 34675, 34732, 34735,
	34736, 34737, 34850,
	34852, 34853, 34855, 34856,
	34857, 34858, 34859, 34908,
	34909, 34910, 36867,
	37122, 37377, 37378,
	37379, 37380, 37381,
	37382, 37383, 37384, 37385,
	37386, 37387, 37388,
	37389, 37390, 37391,
	37392, 37393, 37394,
	37395, 37396, 37397,
	37398, 37399, 37439, 37724,
	40965, 50255,
	50706, 50707, 50708, 50709, 50710, 50711, 50712,
        50713, 50714, 50715, 50716, 50717, 50718,
        50719, 50720, 50721, 50722,
	50723, 50724, 50725, 50726,
        50727, 50728, 50729, 50730, 50731, 50732,
        50733, 50734, 50735,
        50736, 50737, 50738, 50739,
        50740, 50741,
        50778, 50779, 50780
    };


    /** A private constructor just to make sure nobody
       instantiates the class by mistake. */
    private TiffTags ()
    {
    }


    /**
     * Return tag name by number.
     */
    public static String tagName (int tag)
    {
        // Data integrity check.
        if (TAG_INDEX.length != TAG_LABELS.length) {
            //System.out.println ("Data integrity error in TiffTags");
        }
        String name = null;
        int n = -1;
        for (int i=0; i<TAG_INDEX.length; i++) {
            if (tag == TAG_INDEX[i]) {
                n = i;
                break;
            }
        }
        if (n > -1) {
            name = TAG_LABELS[n];
        }
        else {
            name = Integer.toString (tag);
        }
        return name;
    }
} 
