/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2005 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.util.*;

/**
 * Encapsulation of the AES Metadata for Audio documents
 *
 * @author Gary McGath
 *
 */
public class AESAudioMetadata 
{
    /******************************************************************
     * PUBLIC CLASS FIELDS.
     ******************************************************************/

    /** Big-endian constant. */
    public static final int BIG_ENDIAN = 0;

    /** Little-endian constant. */
    public static final int LITTLE_ENDIAN = 1;

    /** Analog / digital labels. */
    public static final String [] A_D = {
    "ANALOG", "PHYS_DIGITAL", "FILE_DIGITAL"
    };
    
    /** Values for primary identifier type */
    public static final String
        FILE_NAME = "FILE_NAME",
        OTHER = "OTHER";

    /** Constant for an undefined integer value. */
    public static final int NULL = -1;
    /** Constant for an undefined floating-point value. */
    public static final double NILL = -1.0;

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     *
     ******************************************************************/

    /** Constant value for the SchemaVersion field */
    public static final String SCHEMA_VERSION = "1.02b";
    
    /** Constant value for the disposition field */
    private static final String DEFAULT_DISPOSITION = "validation";

    private String _analogDigitalFlag;
    private String _appSpecificData;
    private String _audioDataEncoding;
    private int _byteOrder;
    private String _disposition;
    private List _faceList;
    private long _firstSampleOffset;
    private String _format;
    private List _formatList;
    private int _numChannels;
    private String _primaryIdentifier;
    private String _primaryIdentifierType;
    private String _primaryIdentifierOtherType;
    private String _schemaVersion;
    private String _specificationVersion;
    private String[] _use;

    /* Most recently added FormatRegion */
    private FormatRegion _curFormatRegion;
    /* Most recently added Face */
    private Face _curFace;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate a <code>NisoImageMetadata</code> object.
     */
    public AESAudioMetadata ()
    {
        _schemaVersion = SCHEMA_VERSION;
        _disposition = DEFAULT_DISPOSITION;
        _analogDigitalFlag = null;
        _format = null;
        _specificationVersion = null;
        _audioDataEncoding = null;
        _primaryIdentifier = null;
        _primaryIdentifierType = null;
        _use = null;

        // We add one format region to get started.  In practice,
        // that one is all we're likely to need. but more can be
        // added if necessary.
        _formatList = new LinkedList ();
        _faceList = new LinkedList ();
        addFormatRegion ();
        addFace ();
        _numChannels = NULL;
        _byteOrder = NULL;
        _firstSampleOffset = NULL;
    }
    
    /******************************************************************
     * PUBLIC STATIC INTERFACES.
     * 
     ******************************************************************/
    /**
     *  Public interface to the nested FormatRegion object.  Instances
     *  of this should be created only by addFormatRegion, but can be
     *  accessed through the public methods of this interface.
     */
    public static interface FormatRegion {
        /** Returns the bit depth. */
        public int getBitDepth ();
        /** Returns the bitrate reduction (compression information).
         *  This will be an array of seven strings (which may be
         *  empty, but should never be null) interpreted as follows:
         *  <ul>
         *  <li>0: codecName
         *  <li>1: codecNameVersion
         *  <li>2: codecCreatorApplication
         *  <li>3: codecCreatorApplicationVersion
         *  <li>4: codecQuality
         *  <li>5: dataRate
         *  <li>6: dataRateMode
         *  </ul> 
         */
        public String[] getBitrateReduction ();
        /** Returns the sample rate. */
        public double getSampleRate ();
        /** Returns the word size. */
        int getWordSize ();
        /** Returns <code>true</code> if the region is empty. */
        public boolean isEmpty ();
        /** Sets the bit depth value. */
        public void setBitDepth (int bitDepth);
        /** Sets the bitrate reduction information to null (no compression). */
        public void clearBitrateReduction ();
        /** Sets the bitrate reduction (aka compression type). */
        public void setBitrateReduction (String codecName,
                String codecNameVersion,
                String codecCreatorApplication,
                String codecCreatorApplicationVersion,
                String codecQuality,
                String dataRate,
                String dataRateMode);
        /** Sets the sample rate. */
        public void setSampleRate (double sampleRate);
        /** Sets the word size. */
        public void setWordSize (int wordSize);
    }

    /**
     *  Public interface to the nested TimeDesc object.  Instances
     *  of this should be created only by appropriate methods, but can be
     *  accessed through the public methods of this interface.
     */
    public static interface TimeDesc {
        /** Returns the hours component. */
        public int getHours ();
        /** Returns the minutes component. */
        public int getMinutes ();
        /** Returns the seconds component. */
        public int getSeconds ();
        /** Returns the frames component of the fraction of a second.
         *  We always consider frames to be thirtieths of a second. */
        public int getFrames ();
        /** Returns the samples remaining after the frames part of
         *  the fractional second. */
        public int getSamples ();
        /** Returns the sample rate on which the samples remainder
         *  is based. */
        public double getSampleRate ();
    }
    
    /** Public interface to the nested Face object. Instances
     *  of this should be created only by appropriate methods, but can be
     *  accessed through the public methods of this interface. */
    public static interface Face {
        /** Returns an indexed FaceRegion. */
        public FaceRegion getFaceRegion (int i);
        
        /** Adds a FaceRegion. This may be called repeatedly to
         *  add multiple FaceRegions. */
        public void addFaceRegion ();
        
        /** Returns the starting time. */
        public TimeDesc getStartTime ();
        
        /** Returns the duration. */
        public TimeDesc getDuration ();
        
        /** Returns the direction. */
        public String getDirection ();
        
        /** Sets the starting time.  This will be converted
         *  into a TimeDesc. */
        public void setStartTime (long samples);
        
        /** Sets the duration. This will be converted
         *  into a TimeDesc. */
        public void setDuration (long samples);
        
        /** Sets the direction.  This must be one of the
         *  directionTypes.  FORWARD is recommended for most
         *  or all cases. 
         */
        public void setDirection (String direction);

        /* End of interface Face */
    }
    
    /** Public interface to the nested FaceRegion object. Instances
     *  of this should be created only by appropriate methods, but can be
     *  accessed through the public methods of this interface. */
    public static interface FaceRegion {
        /** Returns the starting time. */
        public TimeDesc getStartTime ();
        
        /** Returns the duration. */
        public TimeDesc getDuration ();

        /** Returns the channel map locations.  The array length must
         *  equal the number of channels. */
        public String[] getMapLocations ();

        /** Sets the starting time. */
        public void setStartTime (long samples);
        
        /** Sets the duration. */
        public void setDuration (long samples);
        
        /** Sets the channel map locations.  The array length must
         *  equal the number of channels. */
        public void setMapLocations (String[] locations);

        /* End of interface FaceRegion */
    }

    /******************************************************************
     * STATIC MEMBER CLASSES.
     * 
     ******************************************************************/
    /** The implementation of the FormatRegion interface.  The combination
     *  of a public interface and a private implementation is suggested
     *  in _Java in a Nutshell_.
     */
    class FormatRegionImpl implements FormatRegion {
        
        private int _bitDepth;
        private double _sampleRate;
        private int _wordSize;
        private String[] _bitrateReduction;

        public FormatRegionImpl () {
            _bitDepth = NULL;
            _sampleRate = NILL;
            _wordSize = NULL;
            _bitrateReduction = null;
        }
        
        /** Returns bit depth. */
        public int getBitDepth ()
        {
            return _bitDepth;
        }
        
        /** Returns the bitrate reduction (compression information).
         *  This will be an array of seven strings (which may be
         *  empty but not null) interpreted respectively as follows:
         *  <ul>
         *  <li>0: codecName
         *  <li>1: codecNameVersion
         *  <li>2: codecCreatorApplication
         *  <li>3: codecCreatorApplicationVersion
         *  <li>4: codecQuality
         *  <li>5: dataRate
         *  <li>6: dataRateMode
         *  </ul> 
         */
        public String[] getBitrateReduction ()
        {
            return _bitrateReduction;
        }
        
        /** Returns sample rate. */
        public double getSampleRate ()
        {
            return _sampleRate;
        }
        
        /** Returns word size. */
        public int getWordSize ()
        {
            return _wordSize;
        }
        
        /** Returns true if the FormatRegion contains only
         *  default values. */
        public boolean isEmpty ()
        {
            return _bitDepth == NULL &&
                   _sampleRate == NILL &&
                   _wordSize == NULL;
        }

        /** Sets bit depth. */
        public void setBitDepth (int bitDepth)
        {
            _bitDepth = bitDepth;
        }

        /** Sets the bitrate reduction information to null (no compression). */
        public void clearBitrateReduction ()
        {
            _bitrateReduction = null;
        }

        /** Sets the bitrate reduction (compression type). */
        public void setBitrateReduction (String codecName,
                String codecNameVersion,
                String codecCreatorApplication,
                String codecCreatorApplicationVersion,
                String codecQuality,
                String dataRate,
                String dataRateMode)
        {
            _bitrateReduction = new String[7];
            _bitrateReduction[0] = codecName;
            _bitrateReduction[1] = codecNameVersion;  
            _bitrateReduction[2] = codecCreatorApplication;
            _bitrateReduction[3] = codecCreatorApplicationVersion;
            _bitrateReduction[4] = codecQuality;
            _bitrateReduction[5] = dataRate;
            _bitrateReduction[6] = dataRateMode;
        }

        /** Sets sample rate. */
        public void setSampleRate (double sampleRate)
        {
            _sampleRate = sampleRate;
        }
        
        
        /** Sets word size. */
        public void setWordSize (int wordSize)
        {
            _wordSize = wordSize;
        }
        
        /* End of FormatRegionImpl */
    }

    /** The implementation of the TimeDesc interface.  The combination
     *  of a public interface and a private implementation is suggested
     *  in _Java in a Nutshell_.
     */
    class TimeDescImpl implements TimeDesc
    {
        private int _hours;
        private int _minutes;
        private int _seconds;
        private int _frames;
        private int _samples;
        private double _sampleRate;
	private int _frameCount;
        
	/* Constructor rewritten to avoid rounding errors when converting to
	 * TCF. Now uses integer remainder math instead of floating point.
	 * Changed the base unit from a double representing seconds to a long
	 * representing samples. Changed all existing calls (that I could find)
	 * to this method to accomodate this change.
	 *
	 * @author David Ackerman
	 */
        public TimeDescImpl (long samples)
	{
	    long _sample_count = samples;
	    _frameCount = 30;
	    _sampleRate = _curFormatRegion.getSampleRate ();
			
	    /* It seems that this method is initially called before a valid
	     * sample rate has been established, causing a divide by zero
	     * error.
	     */
	    if (_sampleRate < 0) {
                _sampleRate = 44100.0; //reasonable default value 
            }

	    long sample_in_1_frame = (long)(_sampleRate/_frameCount);
	    long sample_in_1_second = sample_in_1_frame * _frameCount;
	    long sample_in_1_minute = sample_in_1_frame * _frameCount * 60;
	    long sample_in_1_hour = sample_in_1_frame * _frameCount * 60 * 60;
	    long sample_in_1_day = sample_in_1_frame * _frameCount * 60 * 60 * 24;
			
	    // BWF allows for a negative timestamp but tcf does not, so adjust
	    // time accordingly
	    // this might be a good place to report a warning during validation
	    if (_sample_count < 0) {
		_sample_count += sample_in_1_day;
		_sample_count = (_sample_count % sample_in_1_day);
	    }
		
	    _hours = (int)(_sample_count / sample_in_1_hour);
	    _sample_count -= (_hours * sample_in_1_hour);
	    _minutes = (int)(_sample_count / sample_in_1_minute);
	    _sample_count -= (_minutes * sample_in_1_minute);
	    _seconds = (int)(_sample_count / sample_in_1_second);
	    _sample_count -= (_seconds * sample_in_1_second);
	    _frames = (int)(_sample_count / sample_in_1_frame);
	    _sample_count -= (_frames * sample_in_1_frame);
	    _samples = (int)_sample_count;
			
	    /* At present TCF does not have the ability to handle time stamps
	     * > midnight. Industry practice is to roll the clock forward to
	     * zero or back to 23:59:59:29... when crossing this boundary
	     * condition.
	     */
	    _hours = _hours % 24;	
        }
        
        /** Returns the hours component. */
        public int getHours () {
            return _hours;
        }

        /** Returns the minutes component. */
        public int getMinutes () {
            return _minutes;
        }

        /** Returns the seconds component. */
        public int getSeconds () {
            return _seconds;
        }

        /** Returns the frames component of the fraction of a second.
         *  We always consider frames to be thirtieths of a second. */
        public int getFrames () {
            return _frames;
        }

        /** Returns the samples remaining after the frames part of
         *  the fractional second. */
        public int getSamples () {
            return _samples;
        }
        
        /** Returns the sample rate on which the samples remainder
         *  is based. */
        public double getSampleRate () {
            return _sampleRate;
        }
    } /* End of TimeDescImpl */

    /** The implementation of the Face interface.  The combination
     *  of a public interface and a private implementation is suggested
     *  in _Java in a Nutshell_.
     */
    class FaceImpl implements Face {
        List _regionList;
        TimeDesc _startTime;
        TimeDesc _duration;
        String _direction;
        
        
        /** Constructor.  Initially the duration is set
         *  to null, indicating unknown value. */
        public FaceImpl ()
        {
            _regionList = new ArrayList ();
            _startTime = new TimeDescImpl (0);
            _duration = null;
        }


        /** Returns an indexed FaceRegion. */
        public FaceRegion getFaceRegion (int i) {
            return (FaceRegion) _regionList.get (i);
        }
        
        /** Adds a FaceRegion. This may be called repeatedly to
         *  add multiple FaceRegions. */
        public void addFaceRegion () {
            _regionList.add (new FaceRegionImpl ());
        }
        
        /** Returns the starting time. Will be zero if not
         *  explicitly specified. */
        public TimeDesc getStartTime () {
            return _startTime;
        }
        
        /** Returns the duration. May be null if the duration
         *  is unspecified. */
        public TimeDesc getDuration () {
            return _duration;
        }

        /** Returns the direction. */
        public String getDirection ()
        {
            return _direction;
        }

        /** Sets the starting time.  This will be converted
         *  into a TimeDesc. */
        public void setStartTime (long samples)
        {
            _startTime = new TimeDescImpl (samples);
        }
        
        /** Sets the duration. This will be converted
         *  into a TimeDesc. */
        public void setDuration (long samples)
        {
            _duration = new TimeDescImpl (samples);
        }

        /** Sets the direction.  This must be one of the
         *  directionTypes.  FORWARD is recommended for most
         *  or all cases. 
         */
        public void setDirection (String direction)
        {
            _direction = direction;
        }

        /* End of FaceImpl */
    }


    /** The implementation of the Face interface.  The combination
     *  of a public interface and a private implementation is suggested
     *  in _Java in a Nutshell_.
     */
    class FaceRegionImpl implements FaceRegion {
        private TimeDesc _startTime;
        private TimeDesc _duration;
        private String[] _mapLocations;
        
        public FaceRegionImpl ()
        {
            _startTime = new TimeDescImpl (0);
            _duration = null;
        }
        
        /** Returns the starting time. */
        public TimeDesc getStartTime () {
            return _startTime;
        }
        
        /** Returns the duration. */
        public TimeDesc getDuration () {
            return _duration;
        }
        
        /** Returns the channel map locations.  The array length
         *  will equal the number of channels. */
        public String[] getMapLocations ()
        {
            return _mapLocations;
        }

        /** Sets the duration. This will be converted
         *  into a TimeDesc. */
        public void setStartTime (long samples) {
            _startTime = new TimeDescImpl (samples);
        }
        
        /** Sets the duration. This will be converted
         *  into a TimeDesc. */
        public void setDuration (long samples)
        {
            _duration = new TimeDescImpl (samples);
        }

        /** Sets the channel map locations.  The array length must
         *  equal the number of channels. */
        public void setMapLocations (String[] locations)
        {
            _mapLocations = locations;
        }        
        /* End of FaceRegionImpl */
    }
   
    /* End of inner classes */

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     * 
     * Accessor methods.
     ******************************************************************/

    /** Returns analog/digital flag.  Value will always be
     *  "FILE_DIGITAL" in practice. */
    public String getAnalogDigitalFlag ()
    {
        return _analogDigitalFlag;
    }
    
    /** Returns application-specific data.  We assume this is
     *  representable in String format. 
     */
    public String getAppSpecificData ()
    {
        return _appSpecificData;
    }
    
    /** Returns audio data encoding. */
    public String getAudioDataEncoding ()
    {
        return _audioDataEncoding;
    }

    /** Returns the bitrate reduction (compression information).
     *  This will be an array of seven strings (which may be
     *  empty, but should never be null) interpreted as follows:
     *  <ul>
     *  <li>0: codecName
     *  <li>1: codecNameVersion
     *  <li>2: codecCreatorApplication
     *  <li>3: codecCreatorApplicationVersion
     *  <li>4: codecQuality
     *  <li>5: dataRate
     *  <li>6: dataRateMode
     *  </ul> 
     */
    public String[] getBitrateReduction ()
    {
        return _curFormatRegion.getBitrateReduction();
    }

    /* Returns the sample rate. */
    public double getSampleRate ()
    {
	return _curFormatRegion.getSampleRate ();
    }

    /** Return the byte order: 0 = big-endian; 1 = little-endian. */
    public int getByteOrder ()
    {
        return _byteOrder;
    }
    
    /** Returns disposition. */
    public String getDisposition ()
    {
        return _disposition;
    }
    
    /** Gets the list of Faces. Normally there will be only one face
     *  in a digital file. */
    public List getFaceList ()
    {
        return _faceList;
    }
    
    /** Return the offset of the first byte of sample data. */
    public long getFirstSampleOffset ()
    {
        return _firstSampleOffset;
    }

    /** Returns format name. */
    public String getFormat ()
    {
        return _format;
    }
    
    /** Gets the list of Format Regions.  Since one is created
     *  automatically on initialization, it's possible that the
     *  list will contain a Format Region with only default values.
     *  This should be checked with isEmpty ().
     */
    public List getFormatList ()
    {
        return _formatList;
    }
    
    /** Returns the names of the map locations.
     *  The returned
     *  value is an array whose length equals the number of
     *  channels and whose elements correspond to channels 0, 1,
     *  etc. 
     */
    public String[] getMapLocations() {
        return _curFace.getFaceRegion(0).getMapLocations();
    }
    
    /** Returns number of channels. */
    public int getNumChannels ()
    {
        return _numChannels;
    }

    /** Returns primary identifier. */
    public String getPrimaryIdentifier ()
    {
        return _primaryIdentifier;
    }

    /** Returns primary identifier type. */
    public String getPrimaryIdentifierType ()
    {
        return _primaryIdentifierType;
    }

    /** Returns schema version. */
    public String getSchemaVersion ()
    {
        return _schemaVersion;
    }
    
    /** Returns specification version of the document format. */
    public String getSpecificationVersion ()
    {
        return _specificationVersion;
    }
    
    /** Returns the use (role of the document).
     *  The value returned is an array of two strings,
     *  the useType and the otherType. */
    public String[] getUse ()
    {
        return _use;
    }
    

    


    /******************************************************************
     * Mutator methods.
     ******************************************************************/
    
    /** Sets the analog/digital flag.  The value set should always
     *  be "FILE_DIGITAL". */
    public void  setAnalogDigitalFlag (String flagType)
    {
        _analogDigitalFlag = flagType;
    }

    /** Sets the bitrate reduction (compression type). */
    public void setBitrateReduction (String codecName,
            String codecNameVersion,
            String codecCreatorApplication,
            String codecCreatorApplicationVersion,
            String codecQuality,
            String dataRate,
            String dataRateMode)
    {
        _curFormatRegion.setBitrateReduction (codecName,
                codecNameVersion, codecCreatorApplication,
                codecCreatorApplicationVersion,
                codecQuality, dataRate, dataRateMode);
    }
    
    /** Set the bitrate reduction information to null (no compression). */
    public void clearBitrateReduction ()
    {
        _curFormatRegion.clearBitrateReduction ();
    }

    /** Sets the byte order.
     * @param order Byte order: 0 = big-endian, 1 = little-endian
     */
    public void setByteOrder (int order)
    {
	   _byteOrder = order;
    }

    /** Sets the byte order.
     */
    public void setByteOrder (String order)
    {
    	if (order.substring (0, 3).toLowerCase ().equals ("big")) {
    	    _byteOrder = BIG_ENDIAN;
    	}
    	else if (order.substring (0, 6).toLowerCase ().equals ("little")) {
    	    _byteOrder = LITTLE_ENDIAN;
    	}
    }

    /** Sets the audio data encoding. */
    public void setAudioDataEncoding (String audioDataEncoding)
    {
        _audioDataEncoding = audioDataEncoding;
    }
    
    /** Set the application-specific data.  For present purposes,
     *  we assume this is representable as a text string. */
    public void setAppSpecificData (String data)
    {
        _appSpecificData = data;
    }
    
    /** Sets the bit depth. */
    public void setBitDepth (int bitDepth)
    {
        _curFormatRegion.setBitDepth (bitDepth);
    }
    
    /** Sets the disposition. */
    public void setDisposition (String disposition)
    {
        _disposition = disposition;
    }

    /** Sets the direction.  
     *  This must be one of the values 
     *  FORWARD, REVERSE, A_WIND, B_WIND, C_WIND, D_WIND,
     *  FRONT, BACK.  FORWARD may be the only one that
     *  makes sense for digital formats.
     */
    public void setDirection (String direction)
    {
        _curFace.setDirection (direction);
    }
    
    /** Sets the duration in samples. 
     * This affects the current face and its first FaceRegion.
     */
    public void setDuration (long duration)
    {
	_curFace.setDuration (duration);
	_curFace.getFaceRegion(0).setDuration (duration);
    }

    /** Sets the offset of the first byte of sample data. */
    public void setFirstSampleOffset (long offset)
    {
        _firstSampleOffset = offset;
    }

    /** Sets the format name. */
    public void setFormat (String format)
    {
        _format = format;
    }
    
    /** Sets the array of channel map locations. The length
     *  of the array must equal the number of channels. */
    public void setMapLocations (String[] locations) {
        _curFace.getFaceRegion(0).setMapLocations (locations);
    }

    /** Sets the number of channels. */
    public void setNumChannels (int numChannels)
    {
        _numChannels = numChannels;
    }

    /** Sets the primary identifier. */
    public void setPrimaryIdentifier (String primaryIdentifier)
    {
        _primaryIdentifier = primaryIdentifier;
    }
    
    /** Sets the primary identifier type. If the primary identifier
     *  type is OTHER, use setOtherPrimaryIdentifierType instead.
     */
    public void setPrimaryIdentifierType (String primaryIdentifierType)
    {
        _primaryIdentifierType = primaryIdentifierType;
    }

    /** Sets the primary identifier type as "OTHER", and
     *  set the otherType.
     */
    public void setOtherPrimaryIdentifierType (String otherType)
    {
        _primaryIdentifierType = "OTHER";
        _primaryIdentifierOtherType = otherType;
    }
    
    /** Sets the sample rate. */
    public void setSampleRate (double sampleRate)
    {
        _curFormatRegion.setSampleRate (sampleRate);
    }
    
    /** Sets the specification version of the document format.*/
    public void setSpecificationVersion (String specificationVersion)
    {
        _specificationVersion = specificationVersion;
    }

    /** Sets the start time in samples. 
     * This affects the current face and its first FaceRegion.
     */
    public void setStartTime (long samples)
    {
	_curFace.setStartTime (samples);
	_curFace.getFaceRegion(0).setStartTime (samples);
    }
    
    /** Sets the role of the document. Permitted values are
     *  ORIGINAL_MASTER, PRESERVATION_MASTER, PRODUCTION_MASTER, 
     *  SERVICE, PREVIEW, or OTHER.
     *  If useType is "OTHER", then otherType
     *  is significant.  Since OTHER is the only meaningful
     *  value for a digital document, the code assumes this will always
     *  be the case and uses otherType. */
    public void setUse (String useType, String otherType)
    {
        _use = new String[] {useType, otherType};
    }
    
    /** Sets the word size. */
    public void setWordSize (int wordSize)
    {
        _curFormatRegion.setWordSize (wordSize);
    }
    
    /** Adds a FormatRegion object to a FormatSize list.
     *  The most recently added FormatRegion object will
     *  be filled in by setBitDepth, setSampleRate, and
     *  setWordSize.
     */
    public void addFormatRegion ()
    {
        _curFormatRegion = new FormatRegionImpl ();
        _formatList.add (_curFormatRegion);
    }
    
    /** Adds a Face.  
     */
    public void addFace ()
    {
        _curFace = new FaceImpl ();
        _faceList.add (_curFace);
        _curFace.addFaceRegion();
    }
    
}
