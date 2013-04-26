/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-4 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;
import java.util.logging.*;

/**
 *  This class is an abstract implementation of the Module interface.
 *  It contains all the methods required for a Module, but doesn't
 *  do anything by itself.  A subclass should provide a functional
 *  implmentation of <code>parse (InputStream stream, RepInfo info, int parseIndex)</code>
 *  if it is not random access, or
 *  <code>parse (RandomAccessFile file, RepInfo info)</code>
 *  if it is random access.
 *  
 */
public abstract class ModuleBase
    implements Module
{
    /******************************************************************
     * PROTECTED INSTANCE FIELDS.
     ******************************************************************/
        
    /**  The application object */
    protected App _app;
    /**  Coverage information */
    protected String _coverage;
    /**  Module last modification date */
    protected Date _date;
    /**  Formats recognized by this Module */
    protected String [] _format;
    /** Initialization value. */
    protected String _init;
    /** List of default parameters. */
    protected List<String> _defaultParams;
    /** JHOVE engine. */
    protected JhoveBase _je;
    /**  MIME types supported by this Module */
    protected String [] _mimeType;
    /**  Module name */
    protected String _name;
    /**  Module note */
    protected String _note;
    /**  Module-specific parameter. */
    protected String _param;
    /**  Module release description */
    protected String _release;
    /**  RepInfo note */
    protected String _repInfoNote;
    /**  Copyright notice */
    protected String _rights;
    /**  Module Signature list  */
    protected List<Signature> _signature;
    /**  Module specification document list */
    protected List<Document> _specification;
    /**  Module vendor */
    protected Agent _vendor;
    /**  Well-formedness criteria */
    protected String _wellFormedNote;
    /**  Validity criteria */
    protected String _validityNote;
    /**  Random access flag */
    protected boolean _isRandomAccess;
        /**  Byte count of content object */
    protected long _nByte;
    /**  CRC32 calculated on content object */
    protected CRC32 _crc32;
    /**  MD5 digest calculated on content object */
    protected MessageDigest _md5;
    /**  SHA-1 digest calculated on content object */
    protected MessageDigest _sha1;
        /**  Flag indicating valid checksum information set */
    protected boolean _checksumFinished;
    /**  Indicator of how much data to report */
    protected int _verbosity;
    /**  Flag to indicate read routines should count the stream */
    protected boolean _countStream;
    /**  The dominant "endianness" of the Module. */
    protected boolean _bigEndian;
    /**  The list of supported features. */
    protected List<String> _features;
    /** Logger for a module class. */
    protected Logger _logger;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *   Constructors of all subclasses of ModuleBase should call
     *   this as a <code>super</code> constructor.
     *
     *   @param name            Name of the module
     *   @param release         Release identifier
     *   @param date            Last modification date of the module code,
     *                          in the form of an array of three numbers.
     *                          <code>date[0]</code> is the year, 
     *                          <code>date[1]</code> the month, and
     *                          <code>date[2]</code> the day.
     *   @param format          Array of format names supported by the module
     *   @param coverage        Details as to the specific format versions or 
     *                          variants that are supported by the module
     *   @param mimeType        Array of MIME type strings for formats 
     *                          supported by the module
     *   @param wellFormedNote  Brief explanation of what constitutes
     *                          well-formed content
     *   @param validityNote    Brief explanation of what constitutes
     *                          valid content
     *   @param repInfoNote     Note pertaining to RepInfo (may be null)
     *   @param note            Additional information about the module
     *                          (may be null)
     *   @param rights          Copyright notice for the module
     *   @param isRandomAccess  <code>true</code> if the module treats content as
     *                          random-access data, <false> if it treats content
     *                          as stream data
     */
    protected ModuleBase (String name, String release, int [] date,
                          String [] format, String coverage,
                          String [] mimeType, String wellFormedNote,
                          String validityNote, String repInfoNote, String note,
                          String rights, boolean isRandomAccess)
    {
        // Though we're actually in the jhove package, all the related
        // action logically belongs in the module package, so we name
        // this logger accordingly.
        _logger = Logger.getLogger ("edu.harvard.hul.ois.jhove.module");
        _logger.info ("Initializing " + name);
        _name = name;
        _release = release;

        Calendar calendar = new GregorianCalendar ();
        calendar.set (date[0], date[1]-1, date[2]);
        _date = calendar.getTime ();

        _format = format;
        _coverage = coverage;
        _mimeType = mimeType;
        _signature = new ArrayList<Signature> ();
        _specification = new ArrayList<Document> ();
        _wellFormedNote = wellFormedNote;
        _repInfoNote = repInfoNote;
        _validityNote = validityNote;
        _note = note;
        _rights = rights;
        _isRandomAccess = isRandomAccess;

	_verbosity = MINIMUM_VERBOSITY;
        initFeatures ();
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Initialization methods.
     ******************************************************************/

    /** Initializes the feature list.
     *  This method puts the following features in the list:
     *  <ul>
     *  <li>edu.harvard.hul.ois.canValidate
     *  <li>edu.harvard.hul.ois.canIdentify
     *  </ul>
     */
    public void initFeatures ()
    {
        _features = new ArrayList<String> (2);
        _features.add ("edu.harvard.hul.ois.jhove.canValidate");
        _features.add ("edu.harvard.hul.ois.jhove.canCharacterize");
    }


    /**
     * Per-instantiation initialization.
     * The default method does nothing but save its parameter.
     */
    public void init (String init)
        throws Exception
    {
	_init = init;
    }
    
    /**
     * Set a a List of default parameters for the module.
     * 
     * @param   params     A List whose elements are Strings.
     *                     May be empty.
     */
    public void setDefaultParams (List<String> params)
    {
        _defaultParams = params;
    }

    /**
     *  Applies the default parameters.
     *  Calling this clears any prior parameters.
     */
    public void applyDefaultParams ()
        throws Exception
    {
        resetParams ();
        Iterator<String> iter = _defaultParams.iterator ();
        while (iter.hasNext ()) {
            String parm =  iter.next ();
            param (parm);
        }
    }

    /** Reset parameter settings.
     *  Returns to a default state without any parameters.
     *  The default method clears the saved parameter.
     */
    public void resetParams ()
        throws Exception
    {
        _param = null;
    }

    /**
     * Per-action initialization.  May be called multiple times.
     * The default method does nothing but save its parameter.
     */
    public void param (String param)
        throws Exception
    {
	_param = param;
    }

    /******************************************************************
     * Accessor methods.
     ******************************************************************/

    /**
     *   Returns the App object.
     */
    public App getApp() {
        return _app;
    }

    /**
     *   Returns the JHOVE engine object.
     */
    public JhoveBase getBase() {
        return _je;
    }

    /**
     *   Returns the value of _nByte.
     *   Meaningful only for modules that use a counted InputStream.
     */
    public long getNByte ()
    {
        return _nByte;
    }
    
    /**
     *  Returns <code>true</code> if the dominant "endianness" of the
     *  module, or the current file being processed,
     *  is big-endian, otherwise false.  This does not guarantee
     *  that all numbers in the module follow the dominant endianness,
     *  particularly as formats sometimes incorporate data stored in
     *  a previously defined format.  For some formats, e.g., TIFF, the
     *  endianness depends on the file being processed.
     * 
     *  Every module must initialize the value of _bigEndian for this
     *  function, or else assign its value when parsing a file,
     *  to return a meaningful result.  For some modules (e.g.,
     *  ASCII, endianness has no meaning.
     */
    public boolean isBigEndian ()
    {
        return _bigEndian;
    }
    
    /**
     *  Return details as to the specific format versions or 
     *  variants that are supported by this module
     */
    public final String getCoverage ()
    {
        return _coverage;
    }

    /**
     *  Return the last modification date of this Module, as a
     *  Java Date object
     */
    public final Date getDate ()
    {
        return _date;
    }

    /**
     *   Return the array of format names supported by this Module
     */
    public final String [] getFormat ()
    {
        return _format;
    }

    /**
     *   Return the array of MIME type strings for formats supported
     *   by this Module
     */
    public final String [] getMimeType ()
    {
        return _mimeType;
    }

    /**
     *   Return the module name
     */
    public final String getName ()
    {
        return _name;
    }

    /**
     *   Return the module note
     */
    public final String getNote ()
    {
        return _note;
    }

    /**
     *   Return the release identifier
     */
    public final String getRelease ()
    {
        return _release;
    }

    /**
     *   Return the RepInfo note
     */
    public final String getRepInfoNote ()
    {
        return _repInfoNote;
    }

    /**
     *   Return the copyright information string
     */
    public final String getRights ()
    {
        return _rights;
    }

    /**
     *   Return the List of Signatures recognized by this Module
     */
    public final List<Signature> getSignature ()
    {
        return _signature;
    }

    /**
     *  Returns a list of <code>Document</code> objects (one for each 
     *  specification document of the format).  The specification
     *  list is generated by the Module, and specifications cannot
     *  be added by callers.
     *
     *  @see Document
     */
    public final List<Document> getSpecification ()
    {
        return _specification;
    }

    /**
     *  Return the vendor information
     */
    public final Agent getVendor ()
    {
        return _vendor;
    }

    /**
     *   Return the string describing well-formedness criteria
     */
    public final String getWellFormedNote ()
    {
        return _wellFormedNote;
    }

    /**
     *   Return the string describing validity criteria
     */
    public final String getValidityNote ()
    {
        return _validityNote;
    }

    /**
     *  Return the random access flag (true if the module operates
     *  on random access files, false if it operates on streams)
     */
    public final boolean isRandomAccess () 
    {
        return _isRandomAccess;
    }

    /**
     *  Returns <code>true</code> if the module supports a given
     *  named feature, and <code>false</code> if the feature is
     *  unsupported or unknown.  Feature names are case sensitive.
     * 
     *  It is recommended that features be named using package
     *  nomenclature.  The following features are, by default,
     *  supported by the modules developed by OIS:
     * 
     *  <ul>
     *    <li>edu.harvard.hul.ois.canValidate
     *    <li>edu.harvard.hul.ois.canIdentify
     *  </ul>
     */
    public boolean hasFeature (String feature)
    {
        if (_features == null) {
            // dubious, but check it
            return false;
        }
        Iterator<String> iter = _features.iterator ();
        while (iter.hasNext ()) {
            String f =  iter.next ();
            if (f.equals (feature)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     *  Returns the full list of features.
     */
    public List<String> getFeatures ()
    {
        return _features;
    }

    /**
     *  Returns the list of default parameters. 
     */
    public List<String> getDefaultParams ()
    {
        return _defaultParams;
    }


    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /**
     *  Pass the associated App object to this Module.
     *  The App makes various services available.
     */
    public final void setApp (App app)
    {
        _app = app;
    }

    /**
     *  Pass the JHOVE engine object to this Module.
     */
    public final void setBase (JhoveBase je)
    {
        _je = je;
    }

    /**
     *  Set the value of the validityNote property, which
     *  briefly explains the validity criteria of this Module.
     */
    public final void setValidityNote (String validityNote)
    {
        _validityNote = validityNote;
    }


    /**
     *  Set the value of the CRC32 calculated for the content object.
     *  The checksum-like functions can be set by the caller. 
     *  Setting any of these creates the assumption that the
     *  calculation is already done, and sets the checksumFinished
     *  flag to inhibit recalculation.
         */
    public final void setCRC32 (CRC32 crc32) 
    {
        _crc32 = crc32;
        _checksumFinished = true;
    }
    
    /**
     *  Set the degree of verbosity desired from the module.  The setting
     *  of <code>param</code> can override the verbosity setting.
     *  It does not affect whether raw data are reported or not, only
     *  which data are reported.
     *  
     *
     *  @param  verbosity  The requested verbosity value.  Recognized
     *          values are Module.MINIMUM_VERBOSITY and Module.MAXIMUM_VERBOSITY.
     *          The interpretation of the value depends on the module, and
     *          the module may choose not to use this setting.  However,
     *          modules should treat MAXIMUM_VERBOSITY as a request for
     *          all the data available from the module.
     */
    public void setVerbosity (int verbosity)
    {
        _verbosity = verbosity;
    }

    /**
     *  Sets the byte count for the content object, and sets
     *  the checksumFinished flag.
     */
    public final void setNByte (long nByte) 
    {
        _nByte = nByte;
        _checksumFinished = true;
    }

    /**
     *  Sets the MD5 calculated digest for the content object, and sets
     *  the checksumFinished flag.
     */
    public final void setMD5 (MessageDigest md5) 
    {
        _md5 = md5;
        _checksumFinished = true;
    }

    /**
     *  Sets the SHA-1 calculated digest for the content object, and sets
     *  the checksumFinished flag.
     */
    public final void setSHA1 (MessageDigest sha1) 
    {
        _sha1 = sha1;
        _checksumFinished = true;
    }

    /******************************************************************
     * Parsing methods.
     ******************************************************************/

    /**
     *   Parse the content of a stream digital object and store the
     *   results in RepInfo.
     *   A given Module will normally override only one of the two
     *   parse methods; the default method does nothing.
     *
     *   @param stream    An InputStream, positioned at its beginning,
     *                    which is generated from the object to be parsed.
     *                    If multiple calls to <code>parse</code> are made 
     *                    on the basis of a nonzero value being returned,
     *                    a new InputStream must be provided each time.
     * 
     *   @param info      A fresh (on the first call) RepInfo object 
     *                    which will be modified
     *                    to reflect the results of the parsing
     *                    If multiple calls to <code>parse</code> are made 
     *                    on the basis of a nonzero value being returned, 
     *                    the same RepInfo object should be passed with each
     *                    call.
     *
     *   @param parseIndex  Must be 0 in first call to <code>parse</code>.  If
     *                    <code>parse</code> returns a nonzero value, it must be
     *                    called again with <code>parseIndex</code> 
     *                    equal to that return value.
     */
    public int parse (InputStream stream, RepInfo info, int parseIndex)
        throws IOException
    {
        return 0;
    }

    /**
     *   Parse the content of a random access digital object and store the
     *   results in RepInfo.
     *   A given Module will normally override only one of the two
     *   parse methods; the default method does nothing.
     *
     *   @param file      A RandomAccessFile, positioned at its beginning,
     *                    which is generated from the object to be parsed
     *   @param info      A fresh RepInfo object which will be modified
     *                    to reflect the results of the parsing
     */
    public void parse (RandomAccessFile file, RepInfo info)
        throws IOException
    {
    }

    /**
     *  Check if the digital object conforms to this Module's
     *  internal signature information.
     *  This function checks the file against the list of predefined
     *  signatures for the module. If there are no predefined
     *  signatures, it calls parse with the arguments passed to it.
     *  Override this for modules that check digital signatures in
     *  some other way. Any module for which the signature may be located
     *  other than at the beginning of the file must override.
     *
     *   @param file      A File object for the object being parsed
     *   @param stream    An InputStream, positioned at its beginning,
     *                    which is generated from the object to be parsed
     *   @param info      A fresh RepInfo object which will be modified
     *                    to reflect the results of the test
     */
    public void checkSignatures (File file,
                InputStream stream, 
                RepInfo info) 
        throws IOException
    {
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        int sigsChecked = 0;
        if (_signature.size() > 0) {
            /* Get each of the internal sigs defined for the module 
             * and test it. All sigs must be present. If there are
             * no internal signatures, this test is meaningless. */
            byte[] sigBuf = new byte[1024];
            stream.read(sigBuf);
            stream.close();
            ListIterator<Signature> iter = _signature.listIterator();
            while (iter.hasNext ()) {
                Signature sig = ((Signature) iter.next ());
                if (sig instanceof InternalSignature) {
                    InternalSignature isig = (InternalSignature) sig;
                    int[] sigValue = isig.getValue ();
                    int offset = isig.getOffset();
                    boolean match = true;
                    for (int i = 0; i < sigValue.length; i++) {
                        if (sigBuf[offset + i] != sigValue[i]) {
                            match = false;
                            break;
                        }
                    }
                    if (!match && isig.getUse().equals (SignatureUseType.MANDATORY)) {
                        info.setWellFormed (false);
                        return;
                    }
                    if (match) {
                        // Only count optional signatures if they match.
                        ++sigsChecked;
                    }
                }
            }
        }
        if (sigsChecked == 0) {
            // No internal sigs defined, parse the file.
            int parseIndex = parse (stream, info, 0);
            while (parseIndex != 0) {
                stream.close ();
                stream = new FileInputStream (file);
                parseIndex = parse (stream, info, parseIndex);
            }
        }
        else if (info.getWellFormed() == RepInfo.TRUE) {
            info.setSigMatch(_name);
        }
    }

    /**
     *  Check if the digital object conforms to this Module's
     *  internal signature information.
     *
     *   @param file      A File object representing the object to be 
     *                    parsed
     * 
     *   @param raf       A RandomAccessFile, positioned at its beginning,
     *                    which is generated from the object to be parsed
     *   
     *   @param info      A fresh RepInfo object which will be modified
     *                    to reflect the results of the test
     */
    public void checkSignatures (File file,
            RandomAccessFile raf, 
            RepInfo info)
        throws IOException
    {
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        int sigsChecked = 0;
        /* Get each of the internal sigs defined for the module 
         * and test it. */
        ListIterator<Signature> iter = _signature.listIterator();
        try {
            while (iter.hasNext ()) {
                Signature sig = ((Signature) iter.next ());
                if (sig instanceof InternalSignature) {
                    InternalSignature isig = (InternalSignature) sig;
                    /* What about non-fixed offset? */
                    raf.seek (isig.getOffset ());
                    int[] sigValue = isig.getValue ();
                    boolean match = true;
                    for (int i = 0; i < sigValue.length; i++) {
                        if (readUnsignedByte (raf) != sigValue[i]) {
                            match = false;
                            break;
                        }
                    }
                    if (!match && isig.getUse().equals (SignatureUseType.MANDATORY)) {
                        info.setWellFormed (false);
                        break;
                    }
                    if (match) {
                        // Only count optional signatures if they match.
                        ++sigsChecked;
                    }
                }
            }
        }
        catch (Exception e) {
            // We may get here on a short file.
            info.setWellFormed (false);
            return;
        }
        // Must match at least one signature.
        if (sigsChecked == 0) {
            info.setWellFormed (false);
        }
        else if (info.getWellFormed() == RepInfo.TRUE) {
            info.setSigMatch(_name);
        }
    }

    /**
     *   Initializes the state of the module for parsing.  This should be
     *   called early in each module's parse() method.  If a module
     *   overrides it to provide additional functionality, the module's
     *   initParse() should call super.initParse().
     */
    protected void initParse ()
    {
        _logger.info (_name + " called initParse");
        _checksumFinished = false;
        _nByte = 0;
        _crc32 = new CRC32 ();
        try {
            _md5  = MessageDigest.getInstance ("MD5");
            _sha1 = MessageDigest.getInstance ("SHA-1");
        }
        catch (NoSuchAlgorithmException e) {
        }    
    }
    
    /**
     *  Calculates the checksums for a module that uses a
     *  random access file.
     */
    protected void calcRAChecksum (Checksummer ckSummer, RandomAccessFile raf)
        throws IOException
    {
	if (ckSummer == null) {
	    return;
	}

        raf.seek (0);
	byte [] buffer = new byte[_je.getBufferSize ()];
	int n = -1;
	try {
	    while ((n = raf.read (buffer)) != -1) {
		if (n > 0) {
		    ckSummer.update (buffer, 0, n);
		}
	    }
	}
	catch (Exception e) {}
    }

    /**
     * Set the checksum values.
     * @param ckSummer Checksummer object
     * @param info     RepInfo object
     */
    protected void setChecksums (Checksummer ckSummer, RepInfo info)
    {
        if (ckSummer != null){
            info.setChecksum (new Checksum (ckSummer.getCRC32 (), 
                                            ChecksumType.CRC32));
            String value = ckSummer.getMD5 ();
            if (value != null) {
                info.setChecksum (new Checksum (value, ChecksumType.MD5));
            }
            if ((value = ckSummer.getSHA1 ()) != null) {
                info.setChecksum (new Checksum (value, ChecksumType.SHA1));
            }
        }
    }

    /**
     *  Generates information about this Module.
     *  The format of the output depends on the OutputHandler.
     */
    public void show (OutputHandler handler)
    {
        handler.show (this);
    }

    /******************************************************************
     * PRIVATE INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Returns the hex string representation of the CRC32 result.
     */
    protected String getCRC32 ()
    {
        return Long.toHexString (_crc32.getValue ());
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/


    /** 
     *  Returns an Property representing an integer value.
     *  If raw output is specified for the module, returns
     *  an INTEGER property, and <code>labels</code> and
     *  <code>index</code> are unused.  Otherwise,
     *  returns a STRING property, with the
     *  string being the element of <code>labels</code>
     *  whose index is the index of
     *  <code>value</code> in <code>index</code>.
     */
    public Property addIntegerProperty(
        String name,
        int value,
        String[] labels,
        int[] index) 
    {
        boolean rawOutput = _je.getShowRawFlag ();
        Property prop = null;
        if (!rawOutput) {
            int n = -1;
            for (int i = 0; i < index.length; i++) {
                if (value == index[i]) {
                    n = i;
                    break;
                }
            }
            if (n > -1) {
                prop = new Property(name, PropertyType.STRING, labels[n]);
            }
        }
        if (prop == null) {
            prop = new Property(name, PropertyType.INTEGER, new Integer(value));
        }

        return prop;
    }


    /** 
     *  Returns an Property representing an integer value.
     *  If raw output is specified for the module, returns
     *  an INTEGER property, and <code>labels</code> and
     *  <code>index</code> are unused.  Otherwise,
     *  returns a STRING property, with the
     *  string being the element of <code>labels</code>
     *  whose index is <code>value</code>.
     */
    public Property addIntegerProperty (String name, int value,
                       String [] labels)
    {
        if (!_je.getShowRawFlag ()) {
            try {
                return new Property (name, PropertyType.STRING, labels[value]);
            }
            catch (Exception e) {
                // fall through
            }
        }
        return new Property (name, PropertyType.INTEGER,
                 new Integer (value));
    }

    /**
     *  Reads an unsigned byte from a DataInputStream.
     *  @param stream     Stream to read
     */
    public static int readUnsignedByte (DataInputStream stream)
        throws IOException
    {
	return readUnsignedByte (stream, null);
    }

    /**
     *  Reads an unsigned byte from a DataInputStream.
     *  @param stream     Stream to read
     *  @param counted    If non-null, module for which value of _nByte 
     *                    shall be incremented appropriately
     */
    public static int readUnsignedByte (DataInputStream stream,
					ModuleBase counted)
        throws IOException
    {
        int val = stream.readUnsignedByte();
        if (counted != null) {
            counted._nByte++;
        }
        return val;
    }

    /**
     *  Reads an unsigned byte from a RandomAccessFile.
     */
    public static int readUnsignedByte (RandomAccessFile file)
        throws IOException
    {
        return file.readUnsignedByte ();
    }
    
    /**
     *  Reads into a byte buffer from a DataInputStream.
     * 
     *  @param stream   Stream to read from
     *  @param buf      Byte buffer to fill up
     *  @param counted  If non-null, module for which value of _nByte 
     *                  shall be incremented appropriately
     */
    public static int readByteBuf (DataInputStream stream, byte[] buf,
				   ModuleBase counted)
        throws IOException
    {
        int bytesRead = stream.read (buf);
        if (counted != null && bytesRead > 0) {
            counted._nByte += bytesRead;
        }
        return bytesRead;
    }

    /**
     *  Reads two bytes as an unsigned short value from a DataInputStream.
     *  @param stream     The stream to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static int readUnsignedShort (DataInputStream stream,
                                         boolean bigEndian)
        throws IOException
    {
	return readUnsignedShort (stream, bigEndian, null);
    }

    /**
     *  Reads two bytes as an unsigned short value from a DataInputStream.
     *  @param stream     The stream to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static int readUnsignedShort (DataInputStream stream,
                                         boolean bigEndian,
                                         ModuleBase counted)
        throws IOException
    {
        int n = 0;
        if (bigEndian) {
            n = stream.readUnsignedShort ();
        }
        else {
            int b1 = stream.readUnsignedByte ();
            int b0 = stream.readUnsignedByte ();
            n = (b0 << 8) | b1;
        }
        if (counted != null) {
            counted._nByte += 2;
        }
        return n;
    }

    /**
     *  Reads two bytes as an unsigned short value from a
     *  RandomAccessFile.
     *
     *  @param file       The file to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static int readUnsignedShort (RandomAccessFile file,
                                         boolean bigEndian)
        throws IOException
    {
        int n = 0;
        if (bigEndian) {
            n = file.readUnsignedShort ();
        }
        else {
            int b1 = file.readUnsignedByte ();
            int b0 = file.readUnsignedByte ();
            n = (b0 << 8) | b1;
        }
        return n;
    }

    /**
     *  Reads four bytes as an unsigned 32-bit value from a
     *  DataInputStream.
     *
     *  @param stream     The stream to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static long readUnsignedInt (DataInputStream stream,
                                        boolean bigEndian)
        throws IOException 
    {
	return readUnsignedInt (stream, bigEndian, null);
    }

    /**
     *  Reads four bytes as an unsigned 32-bit value from a
     *  DataInputStream.
     *
     *  @param stream     The stream to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static long readUnsignedInt (DataInputStream stream,
                                        boolean bigEndian,
                                        ModuleBase counted)
        throws IOException 
    {
        long n = 0;
        if (bigEndian) {
            n = stream.readInt();         /* This is a signed value. */
            if (n < 0) {
                //n = 2147483648L + n;
                n = (long) n & 0XFFFFFFFFL;
            }
        }
        else {
            long b3 = stream.readUnsignedByte ();
            long b2 = stream.readUnsignedByte ();
            long b1 = stream.readUnsignedByte ();
            long b0 = stream.readUnsignedByte ();
            n = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
        }
        if (counted != null) {
            counted._nByte += 4;
        }
        return n;
    }

    /**
     *  Reads four bytes as an unsigned 32-bit value from a
     *  RandomAccessFile.
     *
     *  @param file       The file to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static long readUnsignedInt (RandomAccessFile file,
                                        boolean bigEndian)
        throws IOException 
    {
        long n = 0;
        if (bigEndian) {
            n = file.readInt();         /* This is a signed value. */
            if (n < 0) {
                //n = 2147483648L + n;
                n = (long) n & 0XFFFFFFFFL;
            }
        }
        else {
            // For efficiency, do one read rather than four
            byte buf[] = new byte[4];
            file.read (buf);
            long b3 = buf[0] & 0XFFL;
            long b2 = buf[1] & 0XFFL;
            long b1 = buf[2] & 0XFFL;
            long b0 = buf[3] & 0XFFL;
            n = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3;
        }
        return n;
    }



    /**
     *  Reads eight bytes as a signed 64-bit value from a
     *  DataInputStream.  (There is no way in Java to have
     *  an unsigned long.)
     *
     *  @param stream     The stream to read from.
     *  @param bigEndian  If true, interpret the first byte as the high
     *                    byte, otherwise interpret the first byte as
     *                    the low byte.
     */
    public static long readSignedLong (DataInputStream stream,
                                        boolean bigEndian,
                                        ModuleBase counted)
        throws IOException 
    {
        long n = 0;
        if (bigEndian) {
            n = stream.readLong();         /* This is a signed value. */
        }
        else {
            long b7 = stream.readUnsignedByte ();
            long b6 = stream.readUnsignedByte ();
            long b5 = stream.readUnsignedByte ();
            long b4 = stream.readUnsignedByte ();
            long b3 = stream.readUnsignedByte ();
            long b2 = stream.readUnsignedByte ();
            long b1 = stream.readUnsignedByte ();
            long b0 = stream.readUnsignedByte ();
            n = (b0 << 56) | (b1 << 48) | (b2 << 40) | (b3 << 32) |
                (b4 << 24) | (b5 << 16) | (b6 << 8) | b7;
        }
        if (counted != null) {
            counted._nByte += 8;
        }
        return n;
    }

    public static Rational readUnsignedRational (DataInputStream stream,
                                                 boolean endian)
        throws IOException
    {
	return readUnsignedRational (stream, endian, null);
    }

    public static Rational readUnsignedRational (DataInputStream stream,
                                                 boolean endian,
                                                 ModuleBase counted)
        throws IOException
    {
        long n = readUnsignedInt (stream, endian, counted);
        long d = readUnsignedInt (stream, endian, counted);
        return new Rational (n, d);
    }

    public static  Rational readUnsignedRational (RandomAccessFile file,
                                                  boolean endian)
        throws IOException
    {
        long n = readUnsignedInt (file, endian);
        long d = readUnsignedInt (file, endian);
        return new Rational (n, d);
    }

    public static Rational readSignedRational (DataInputStream stream,
                                                 boolean endian,
                                                 ModuleBase counted)
        throws IOException
    {
        long n = readSignedInt (stream, endian, counted);
        long d = readSignedInt (stream, endian, counted);
        return new Rational (n, d);
    }

    public static Rational readSignedRational (RandomAccessFile file,
                                               boolean endian)
        throws IOException
    {
        long n = readSignedInt (file, endian);
        long d = readSignedInt (file, endian);
        return new Rational (n, d);
    }

    public static int readSignedByte (RandomAccessFile file)
        throws IOException
    {
        return file.readByte ();
    }

    public static int readSignedShort (RandomAccessFile file, boolean endian)
        throws IOException
    {
        int b = readUnsignedShort (file, endian);
        if ((b & 0X8000) != 0) {
            b |= ~0XFFFF;
        }
        return b;
    }
    
    public static int readSignedInt (RandomAccessFile file, boolean endian)
        throws IOException
    {
        long b = readUnsignedInt (file, endian);
        if ((b & 0X80000000L) != 0) {
            b |= ~0XFFFFFFFFL;
        }
        return (int) b;
    }

    public static int readSignedByte (DataInputStream stream)
	throws IOException
    {
	return readSignedByte (stream, null);
    }

    public static int readSignedByte (DataInputStream stream,
				      ModuleBase counted)
        throws IOException
    {
        int val = stream.readByte ();
        if (counted != null) {
            counted._nByte++;
        }
        return val;
    }

    public static int readSignedShort (DataInputStream stream, boolean endian)
        throws IOException
    {
	return readSignedShort (stream, endian, null);
    }

    public static int readSignedShort (DataInputStream stream, boolean endian,
				       ModuleBase counted)
        throws IOException
    {
        int b = readUnsignedShort (stream, endian, counted);
        if ((b & 0X8000) != 0) {
            b |= ~0XFFFF;
        }
        return b;
    }
    
    public static int readSignedInt (DataInputStream stream, boolean endian)
        throws IOException
    {
	return readSignedInt (stream, endian, null);
    }

    public static int readSignedInt (DataInputStream stream, boolean endian,
				     ModuleBase counted)
        throws IOException
    {
        long b = readUnsignedInt (stream, endian, counted);
        if ((b & 0X80000000L) != 0) {
            b |= ~0XFFFFFFFFL;
        }
        return (int) b;
    }

    public static float readFloat (RandomAccessFile file, boolean endian)
        throws IOException 
    {
        float f = 0.0F;
        if (endian) {
            f = file.readFloat ();
        }
        else {
            // For efficiency, do one read rather than four
            byte buf[] = new byte[4];
            file.read (buf);
            int b3 = buf[0] & 0XFF;
            int b2 = buf[1] & 0XFF;
            int b1 = buf[2] & 0XFF;
            int b0 = buf[3] & 0XFF;
            f = Float.intBitsToFloat (b0<<24 | b1<<16 | b2<<8 | b3);
        }
        return f;
    }

    public static float readFloat (DataInputStream stream, boolean endian,
                        ModuleBase counted)
        throws IOException 
    {
        float f = 0.0F;
        if (endian) {
            f = stream.readFloat ();
        }
        else {
            int b3 = stream.readUnsignedByte ();
            int b2 = stream.readUnsignedByte ();
            int b1 = stream.readUnsignedByte ();
            int b0 = stream.readUnsignedByte ();
            f = Float.intBitsToFloat (b0<<24 | b1<<16 | b2<<8 | b3);
        }
        if (counted != null) {
            counted._nByte += 4;
        }
        return f;
    }

    public static double readDouble (RandomAccessFile file, boolean endian)
        throws IOException 
    {
        double f = 0.0F;
        if (endian) {
            f = file.readDouble ();
        }
        else {
            // For efficiency, do one read rather than eight
            byte buf[] = new byte[8];
            file.read (buf);
            long b7 = buf[0] & 0XFFL;
            long b6 = buf[1] & 0XFFL;
            long b5 = buf[2] & 0XFFL;
            long b4 = buf[3] & 0XFFL;
            long b3 = buf[4] & 0XFFL;
            long b2 = buf[5] & 0XFFL;
            long b1 = buf[6] & 0XFFL;
            long b0 = buf[7] & 0XFFL;

            f = Double.longBitsToDouble (b0<<56 | b1<<48 | b2<<40 | 
                                         b3<<32 | b4<<24 | b5<<16 |
                                         b6<< 8 | b7);
        }
        return f;
    }

    public static double readDouble (DataInputStream stream, boolean endian)
        throws IOException 
    {
	return readDouble (stream, endian, null);
    }

    public static double readDouble (DataInputStream stream, boolean endian,
				     ModuleBase counted)
        throws IOException 
    {
        double f = 0.0F;
        if (endian) {
            f = stream.readDouble ();
        }
        else {
            long b7 = (long) stream.readUnsignedByte ();
            long b6 = (long) stream.readUnsignedByte ();
            long b5 = (long) stream.readUnsignedByte ();
            long b4 = (long) stream.readUnsignedByte ();
            long b3 = (long) stream.readUnsignedByte ();
            long b2 = (long) stream.readUnsignedByte ();
            long b1 = (long) stream.readUnsignedByte ();
            long b0 = (long) stream.readUnsignedByte ();
            f = Double.longBitsToDouble (b0<<56 | b1<<48 | b2<<40 | 
                                         b3<<32 | b4<<24 | b5<<16 |
                                         b6<< 8 | b7);
        }
        if (counted != null) {
            counted._nByte += 8;
        }
        return f;
    }

    /* Skip over some bytes.  */
    public int skipBytes (DataInputStream stream, int bytesToSkip)
            throws IOException
    {
	return skipBytes (stream, bytesToSkip, null);
    }

    /* Skip over some bytes.  */
    public int skipBytes (DataInputStream stream, int bytesToSkip,
			  ModuleBase counted) 
            throws IOException
    {
        int n = stream.skipBytes (bytesToSkip);
        if (counted != null) {
            counted._nByte += n;
        }
        return n;
    }

    /**
     *  A convenience method for getting a buffered DataInputStream
     *  from a module's InputStream.  If the size specified is 0 or
     *  less, the default buffer size is used.
     */
    public static DataInputStream getBufferedDataStream (InputStream stream,
                                                         int size)
    {
        BufferedInputStream bis;
        if (size <= 0) {
            bis = new BufferedInputStream (stream);
        }
        else {
            bis = new BufferedInputStream (stream, size);
        }
        return new DataInputStream (bis);
    }
    
    /**
     *   A utility for converting a Vector of Properties to an
     *   Array.  It can be simpler to build a Vector and then
     *   call VectorToPropArray than to allocate an array and
     *   drop all the Properites into the correct indices.
     *   All the members of the Vector must be of type Property,
     *   or a ClassCastException will be thrown.
     */
    protected Property[] vectorToPropArray (Vector vec)
    {
        Property[] prop = new Property[vec.size ()];
        for (int i = 0; i < vec.size (); i++) {
            prop[i] = (Property) vec.elementAt (i);
        }
        return prop;
    }
}
