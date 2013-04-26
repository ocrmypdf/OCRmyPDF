/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Encapsulation of a GPSInfo IFD (for TIFF/EP and Exif).
 */
public class GPSInfoIFD
    extends IFD
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** GPSVersionID tag. */
    private static final int GPSVERSIONID = 0;
    /** GPSLatitudeRef tag. */
    private static final int GPSLATITUDEREF = 1;
    /** GPSLatitude tag. */
    private static final int GPSLATITUDE = 2;
    /** GPSLongitudeRef tag. */
    private static final int GPSLONGITUDEREF = 3;
    /** GPSLongitude tag. */
    private static final int GPSLONGITUDE = 4;
    /** GPSAltitudeRef tag. */
    private static final int GPSALTITUDEREF = 5;
    /** GPSAltitude tag. */
    private static final int GPSALTITUDE = 6;
    /** GPSTimeStamp tag. */
    private static final int GPSTIMESTAMP = 7;
    /** GPSSatellites tag. */
    private static final int GPSSATELLITES = 8;
    /** GPSStatus tag. */
    private static final int GPSSTATUS = 9;
    /** GPSMeasureMode tag. */
    private static final int GPSMEASUREMODE = 10;
    /** GPSDOP tag. */
    private static final int GPSDOP = 11;
    /** GPSSpeedRef tag. */
    private static final int GPSSPEEDREF = 12;
    /** GPSSpeed tag. */
    private static final int GPSSPEED = 13;
    /** GPSTrackRef tag. */
    private static final int GPSTRACKREF = 14;
    /** GPSTrack tag. */
    private static final int GPSTRACK = 15;
    /** GPSImgDirectionRef tag. */
    private static final int GPSIMGDIRECTIONREF = 16;
    /** GPSImgDirection tag. */
    private static final int GPSIMGDIRECTION = 17;
    /** GPSMapDatum tag. */
    private static final int GPSMAPDATUM = 18;
    /** GPSDestLatitudeRef tag. */
    private static final int GPSDESTLATITUDEREF = 19;
    /** GPSDestLatitude tag. */
    private static final int GPSDESTLATITUDE = 20;
    /** GPSDestLongitudeRef tag. */
    private static final int GPSDESTLONGITUDEREF = 21;
    /** GPSDestLongitude tag. */
    private static final int GPSDESTLONGITUDE = 22;
    /** GPSDestBearingRef tag. */
    private static final int GPSDESTBEARINGREF = 23;
    /** GPSDestBearing tag. */
    private static final int GPSDESTBEARING = 24;
    /** GPSDestDistanceRef tag. */
    private static final int GPSDESTDISTANCEREF = 25;
    /** GPSDestDistance tag. */
    private static final int GPSDESTDISTANCE = 26;
    /** GPSProcessingMethod tag. */
    private static final int GPSPROCESSINGMETHOD = 27;
    /** GPSAreaInformation tag. */
    private static final int GPSAREAINFORMATION = 28;
    /** GPSDateStamp tag. */
    private static final int GPSDATESTAMP = 29;
    /** GPSDifferential tag. */
    private static final int GPSDIFFERENTIAL = 30;

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** GPSVersionID (Tag 0). */
    private int [] _gpsVersionID;
    /** GPSLatitudeRef (1). */
    private String _gpsLatitudeRef;
    /** GPSLatitude (2). */
    private Rational [] _gpsLatitude;
    /** GPSLongitudeRef (3). */
    private String _gpsLongitudeRef;
    /** GPSLongitude (4). */
    private Rational [] _gpsLongitude;
    /** GPSAltitudeRef (5). */
    private int _gpsAltitudeRef;
    /** GPSAltitude (6). */
    private Rational _gpsAltitude;
    /** GPSTimeStamp (7). */
    private Rational [] _gpsTimeStamp;
    /** GPSSatellites (8). */
    private String _gpsSatellites;
    /** GPSStatus (9). */
    private String _gpsStatus;
    /** GPSMeasureMode (10). */
    private String _gpsMeasureMode;
    /** GPSDOP (11). */
    private Rational _gpsDOP;
    /** GPSSpeedRef (12). */
    private String _gpsSpeedRef;
    /** GPSSpeed (13). */
    private Rational _gpsSpeed;
    /** GPSTrackRef (14). */
    private String _gpsTrackRef;
    /** GPSTrack (15). */
    private Rational _gpsTrack;
    /** GPSImgDirectionRef (16). */
    private String _gpsImgDirectionRef;
    /** GPSImgDirection (17). */
    private Rational _gpsImgDirection;
    /** GPSMapDatum (18). */
    private String _gpsMapDatum;
    /** GPSDestLatitudeRef (19). */
    private String _gpsDestLatitudeRef;
    /* GPSDestLatitude (20). */
    private Rational [] _gpsDestLatitude;
    /** GPSDestLongitudeRef (21). */
    private String _gpsDestLongitudeRef;
    /** GPSDestLongitude (22). */
    private Rational [] _gpsDestLongitude;
    /** GPSDestBearingRef (23). */
    private String _gpsDestBearingRef;
    /** GPSDestBearing (24). */
    private Rational _gpsDestBearing;
    /** GPSDestDistanceRef (25). */
    private String _gpsDestDistanceRef;
    /** GPSDestDistance (26). */
    private Rational _gpsDestDistance;

    /* The following four tags are for Exif only, not TIFF/EP. */

    /** GPSProcessingMethod (27). */
    private int [] _gpsProcessingMethod;
    /** GPSAreaInformation (28). */
    private int [] _gpsAreaInformation;
    /** GPSDateStamp (29). */
    private String _gpsDateStamp;
    /** GPSDifferential (30). */
    private int _gpsDifferential;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate an <code>GPSInfoIFD</code> object.
     * @param offset IFD offset
     * @param info   The RepInfo object
     * @param raf TIFF file
     * @param bigEndian True if big-endian file
     */
    public GPSInfoIFD (long offset, RepInfo info, RandomAccessFile raf,
		       boolean bigEndian)
    {
	super (offset, info, raf, bigEndian);

        _gpsAltitudeRef  = NULL;
        _gpsDifferential = NULL;

	/* Set Exif defaults. */
	_gpsVersionID = new int [] {2, 2, 0, 0};
	_gpsAltitudeRef = 0;
	_gpsSpeedRef = "K";
	_gpsTrackRef = "T";
	_gpsImgDirectionRef = "T";
	_gpsDestBearingRef  = "T";
	_gpsDestDistanceRef = "K";
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /** Get the GPSAltitude (6). */
    public Rational getGPSAltitude ()
    {
	return _gpsAltitude;
    }

    /** Get the GPSAltitudeRef (5). */
    public int getGPSAltitudeRef ()
    {
	return _gpsAltitudeRef;
    }

    /** Get the GPSDateStamp (29). */
    public String getGPSDateStamp ()
    {
	return _gpsDateStamp;
    }

    /** Get the GPSDestBearing (24). */
    public Rational getGPSDestBearing ()
    {
	return _gpsDestBearing;
    }

    /** Get the GPSDestBearingRef (23). */
    public String getGPSDestBearingRef ()
    {
	return _gpsDestBearingRef;
    }

    /** Get the GPSDestDistance (26). */
    public Rational getGPSDestDistance ()
    {
	return _gpsDestDistance;
    }

    /** Get the GPSDestDistanceRef (25). */
    public String getGPSDestDistanceRef ()
    {
	return _gpsDestDistanceRef;
    }

    /** Get the GPSDestLatitude (20). */
    public Rational [] getGPSDestLatitude ()
    {
	return _gpsDestLatitude;
    }

    /** Get the GPSDestLatitudeRef (19). */
    public String getGPSDestLatitudeRef ()
    {
	return _gpsDestLatitudeRef;
    }

    /** Get the GPSDestLongitude (22). */
    public Rational [] getGPSDestLongitude ()
    {
	return _gpsDestLongitude;
    }

    /** Get the GPSDestLongitudeRef (21). */
    public String getGPSDestLongitudeRef ()
    {
	return _gpsDestLongitudeRef;
    }

    /** Get the GPSDifferential (30). */
    public int getGPSDifferential ()
    {
	return _gpsDifferential;
    }

    /** Get the GPSDOP (11). */
    public Rational getGPSDOP ()
    {
	return _gpsDOP;
    }

    /** Get the GPSImgDirection (17). */
    public Rational getGPSImgDirection ()
    {
	return _gpsImgDirection;
    }

    /** Get the GPSImgDirectionRef (16). */
    public String getGPSImgDirectionRef ()
    {
	return _gpsImgDirectionRef;
    }

    /** Get the GPSLatitude (2). */
    public Rational [] getGPSLatitude ()
    {
	return _gpsLatitude;
    }

    /** Get the GPSLatitudeRef (1). */
    public String getGPSLatitudeRef ()
    {
	return _gpsLatitudeRef;
    }

    /** Get the GPSLongitude (4). */
    public Rational [] getGPSLongitude ()
    {
	return _gpsLongitude;
    }

    /** Get the GPSLongitudeRef (3). */
    public String getGPSLongitudeRef ()
    {
	return _gpsLongitudeRef;
    }

    /** Get the GPSMapDatum (18). */
    public String getGPSMapDatum ()
    {
	return _gpsMapDatum;
    }

    /** Get the GPSMeasureMode (10). */
    public String getGPSMeasureMode ()
    {
	return _gpsMeasureMode;
    }

    /** Get the GPSProcessingMethod (27). */
    public int [] getGPSProcessingMethod ()
    {
	return _gpsProcessingMethod;
    }

    /** Get the GPSSatellites (8). */
    public String getGPSSatellites ()
    {
	return _gpsSatellites;
    }

    /** Get the GPSSpeed (13). */
    public Rational getGPSSpeed ()
    {
	return _gpsSpeed;
    }

    /** Get the GPSSpeedRef (12). */
    public String getGPSSpeedRef ()
    {
	return _gpsSpeedRef;
    }

    /** Get the GPSStatus (9). */
    public String getGPStatus ()
    {
	return _gpsStatus;
    }

    /** Get the GPSTimeStamp (7). */
    public Rational [] getGPTimeStamp ()
    {
	return _gpsTimeStamp;
    }

    /** Get the GPSTrack (15). */
    public Rational getGPSTrack ()
    {
	return _gpsTrack;
    }

    /** Get the GPSTrackRef (14). */
    public String getGPSTrackRef ()
    {
	return _gpsTrackRef;
    }

    /** Get the GPSVersionID (1). */
    public int [] getGPSVersionID ()
    {
	return _gpsVersionID;
    }

    /** Get the IFD properties. */
    public Property getProperty (boolean rawOutput)
    {
	List entries = new LinkedList ();
	entries.add (new Property ("GPSVersionID", PropertyType.STRING,
				   Integer.toString (_gpsVersionID[0]) + "." +
				   Integer.toString (_gpsVersionID[1]) + "." +
				   Integer.toString (_gpsVersionID[2]) + "." +
				   Integer.toString (_gpsVersionID[3])));
	if (_gpsLatitudeRef != null) {
	    entries.add (new Property ("GPSLatitudeRef", PropertyType.STRING,
				       _gpsLatitudeRef));
	}
	if (_gpsLatitude != null) {
	    entries.add (new Property ("GPSLatitude", PropertyType.RATIONAL,
				       PropertyArity.ARRAY, _gpsLatitude));
	}
	if (_gpsLongitudeRef != null) {
	    entries.add (new Property ("GPSLongitudeRef", PropertyType.STRING,
				       _gpsLongitudeRef));
	}
	if (_gpsLongitude != null) {
	    entries.add (new Property ("GPSLongitude", PropertyType.RATIONAL,
				       PropertyArity.ARRAY, _gpsLongitude));
	}
	entries.add (new Property ("GPSAltitudeRef", PropertyType.INTEGER,
				   new Integer (_gpsAltitudeRef)));
	if (_gpsAltitude != null) {
	    entries.add (new Property ("GPSAltitude", PropertyType.RATIONAL,
				       _gpsAltitude));
	}
	if (_gpsTimeStamp != null) {
	    entries.add (new Property ("GPSTimeStamp", PropertyType.RATIONAL,
				       PropertyArity.ARRAY, _gpsTimeStamp));
	}
	if (_gpsSatellites != null) {
	    entries.add (new Property ("GPSSatellites", PropertyType.STRING,
				       _gpsSatellites));
	}
	if (_gpsStatus != null) {
	    entries.add (new Property ("GPSStatus", PropertyType.STRING,
				       _gpsStatus));
	}
	if (_gpsMeasureMode != null) {
	    entries.add (new Property ("GPSMeasureMode", PropertyType.STRING,
				       _gpsMeasureMode));
	}
	if (_gpsDOP != null) {
	    entries.add (new Property ("GPSDOP", PropertyType.RATIONAL,
				       _gpsDOP));
	}
	entries.add (new Property ("GPSSpeedRef", PropertyType.STRING,
				   _gpsSpeedRef));
	if (_gpsSpeed != null) {
	    entries.add (new Property ("GPSSpeed", PropertyType.RATIONAL,
				       _gpsSpeed));
	}
	entries.add (new Property ("GPSTrackRef", PropertyType.STRING,
				   _gpsTrackRef));
	if (_gpsTrack != null) {
	    entries.add (new Property ("GPSTrack", PropertyType.RATIONAL,
				       _gpsTrack));
	}
	entries.add (new Property ("GPSImgDirectionRef", PropertyType.STRING,
				   _gpsImgDirectionRef));
	if (_gpsImgDirection != null) {
	    entries.add (new Property ("GPSImgDirection",
				       PropertyType.RATIONAL,
				       _gpsImgDirection));
	}
	if (_gpsMapDatum != null) {
	    entries.add (new Property ("GPSMapDatum", PropertyType.STRING,
				       _gpsMapDatum));
	}
	if (_gpsDestLatitudeRef != null) {
	    entries.add (new Property ("GPSDestLatitudeRef",
				       PropertyType.STRING,
				       _gpsDestLatitudeRef));
	}
	if (_gpsDestLatitude != null) {
	    entries.add (new Property ("GPSDestLatitude",
				       PropertyType.RATIONAL,
				       PropertyArity.ARRAY,
				       _gpsDestLatitude));
	}
	if (_gpsDestLongitudeRef != null) {
	    entries.add (new Property ("GPSDestLongitudeRef",
				       PropertyType.STRING,
				       _gpsDestLongitudeRef));
	}
	if (_gpsDestLongitude != null) {
	    entries.add (new Property ("GPSDestLongitude",
				       PropertyType.RATIONAL,
				       PropertyArity.ARRAY,
				       _gpsDestLongitude));
	}
	entries.add (new Property ("GPSDestBearingRef", PropertyType.STRING,
				   _gpsDestBearingRef));
	if (_gpsDestBearing != null) {
	    entries.add (new Property ("GPSDestBearing",
				       PropertyType.RATIONAL,
				       _gpsDestBearing));
	}
	entries.add (new Property ("GPSDestDistanceRef", PropertyType.STRING,
				   _gpsDestDistanceRef));
	if (_gpsDestDistance != null) {
	    entries.add (new Property ("GPSDestDistance",
				       PropertyType.RATIONAL,
				       _gpsDestDistance));
	}
	if (_gpsDestDistanceRef != null) {
	    entries.add (new Property ("GPSDestDistanceRef",
				       PropertyType.STRING,
				       _gpsDestDistanceRef));
	}
	if (_gpsProcessingMethod != null) {
	    entries.add (new Property ("GPSProcessingMethod",
				       PropertyType.INTEGER,
				       PropertyArity.ARRAY,
				       _gpsProcessingMethod));
	}
	if (_gpsAreaInformation != null) {
	    entries.add (new Property ("GPSAreaInformation",
				       PropertyType.INTEGER,
				       PropertyArity.ARRAY,
				       _gpsAreaInformation));
	}
	if (_gpsDateStamp != null) {
	    entries.add (new Property ("GPSDateStamp", PropertyType.STRING,
				       _gpsDateStamp));
	}
	entries.add (new Property ("GPSDifferential", PropertyType.INTEGER,
				   new Integer (_gpsDifferential)));

	return propertyHeader ("GPSInfo", entries);
    }

    /** Lookup an IFD tag. */
    public void lookupTag (int tag, int type, long count, long value)
	throws TiffException
    {
	try {
	    if (tag == GPSALTITUDE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsAltitude = readRational (count, value);
	    }
	    else if (tag == GPSALTITUDEREF) {
		checkType  (tag, type, BYTE);
		checkCount (tag, count, 1);
		_gpsAltitudeRef = readByte (type, count, value);
	    }
	    else if (tag == GPSDATESTAMP) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 11);
		_gpsDateStamp = readASCII (count, value);
	    }
	    else if (tag == GPSDESTBEARING) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsDestBearing = readRational (count, value);
	    }
	    else if (tag == GPSDESTBEARINGREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsDestBearingRef = readASCII (count, value);
	    }
	    else if (tag == GPSDESTDISTANCE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsDestDistance = readRational (count, value);
	    }
	    else if (tag == GPSDESTDISTANCEREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsDestDistanceRef = readASCII (count, value);
	    }
	    else if (tag == GPSDESTLATITUDE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 3);
		_gpsDestLatitude = readRationalArray (count, value);
	    }
	    else if (tag == GPSDESTLATITUDEREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsDestLatitudeRef = readASCII (count, value);
	    }
	    else if (tag == GPSDESTLONGITUDE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 3);
		_gpsDestLongitude = readRationalArray (count, value);
	    }
	    else if (tag == GPSDESTLONGITUDEREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsDestLongitudeRef = readASCII (count, value);
	    }
	    else if (tag == GPSDIFFERENTIAL) {
		checkType  (tag, type, SHORT);
		checkCount (tag, count, 1);
		_gpsDifferential = readShort (type, count, value);
	    }
	    else if (tag == GPSDOP) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsDOP = readRational (count, value);
	    }
	    else if (tag == GPSIMGDIRECTION) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsImgDirection = readRational (count, value);
	    }
	    else if (tag == GPSIMGDIRECTIONREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsImgDirectionRef = readASCII (count, value);
	    }
	    else if (tag == GPSLATITUDE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 3);
		_gpsLatitude = readRationalArray (count, value);
	    }
	    else if (tag == GPSLATITUDEREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsLatitudeRef = readASCII (count, value);
	    }
	    else if (tag == GPSLONGITUDE) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 3);
		_gpsLongitude = readRationalArray (count, value);
	    }
	    else if (tag == GPSLONGITUDEREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsLongitudeRef = readASCII (count, value);
	    }
	    else if (tag == GPSMAPDATUM) {
		checkType  (tag, type, ASCII);
		_gpsMapDatum = readASCII (count, value);
	    }
	    else if (tag == GPSMEASUREMODE) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsMeasureMode = readASCII (count, value);
	    }
	    else if (tag == GPSPROCESSINGMETHOD) {
		checkType  (tag, type, UNDEFINED);
		_gpsProcessingMethod = readByteArray (type, count, value);
	    }
	    else if (tag == GPSSATELLITES) {
		checkType  (tag, type, ASCII);
		_gpsSatellites = readASCII (count, value);
	    }
	    else if (tag == GPSSPEED) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsSpeed = readRational (count, value);
	    }
	    else if (tag == GPSSPEEDREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsSpeedRef = readASCII (count, value);
	    }
	    else if (tag == GPSSTATUS) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsStatus = readASCII (count, value);
	    }
	    else if (tag == GPSTIMESTAMP) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 3);
		_gpsTimeStamp = readRationalArray (count, value);
	    }
	    else if (tag == GPSTRACK) {
		checkType  (tag, type, RATIONAL);
		checkCount (tag, count, 1);
		_gpsTrack = readRational (count, value);
	    }
	    else if (tag == GPSTRACKREF) {
		checkType  (tag, type, ASCII);
		checkCount (tag, count, 2);
		_gpsTrackRef = readASCII (count, value);
	    }
	    else if (tag == GPSVERSIONID) {
		checkType  (tag, type, BYTE);
		checkCount (tag, count, 4);
		_gpsVersionID = readByteArray (type, count, value);
	    }
	    else {
		_info.setMessage (new ErrorMessage ("Unknown GPSInfo IFD tag",
						    "Tag = " + tag, value));
	    }
	}
	catch (IOException e) {
	    throw new TiffException ("Read error for tag" + tag, value);
	}
    }
}
