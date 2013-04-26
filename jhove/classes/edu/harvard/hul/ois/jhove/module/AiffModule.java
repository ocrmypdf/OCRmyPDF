/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2007 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.aiff.*;
import edu.harvard.hul.ois.jhove.module.iff.*;

import java.io.*;
import java.util.*;

/**
 * Module for identification and validation of AIFF files.
 * Supports AIFF and AIFF-C.
 * 
 * @author Gary McGath
 */
public class AiffModule
    extends ModuleBase
{
    /******************************************************************
     * PRIVATE Instance FIELDS.
     ******************************************************************/

    /* Checksummer object */
    protected Checksummer _ckSummer;
        
    /* Input stream wrapper which handles checksums */
    protected ChecksumInputStream _cstream;
    
    /* Data input stream wrapped around _cstream */
    protected DataInputStream _dstream;

    /* Top-level metadata property */
    protected Property _metadata;

    /* Top-level property list */
    protected List _propList;
    
    /* AES audio metadata to go into AIFF metadata */
    protected AESAudioMetadata _aesMetadata;

    /* List of Annotation Chunk properties */
    protected List _annotationList;

    /* List of MIDI Chunk properties */
    protected List _midiList;
    
    /* List of Saxel properties */
    protected List _saxelList;
    
    /* Bytes remaining to be read. */
    protected long bytesRemaining;
    
    /* Flag to check for multiple sound chunks */
    protected boolean soundChunkSeen;
    
    /* Flag to check for exactly one format version chunk */
    protected boolean formatVersionChunkSeen;

    /* Flag to check for exactly one instrument chunk */
    protected boolean instrumentChunkSeen;

    /* Flag to check for exactly one common chunk */
    protected boolean commonChunkSeen;

    /* Flag to check for exactly one comments chunk */
    protected boolean commentsChunkSeen;

    /* Flag to check for exactly one name chunk */
    protected boolean nameChunkSeen;
    
    /* Flag to check for exactly one author chunk */
    protected boolean authorChunkSeen;
    
    /* Flag to check for exactly one copyright chunk */
    protected boolean copyrightChunkSeen;
    
    /* Flag to check for exactly one marker chunk */
    protected boolean markerChunkSeen;

    /* Flag to check for exactly one audio recording chunk */
    protected boolean audioRecChunkSeen;
    
    /* Flag to note that first sample offset has been recorded */
    protected boolean firstSampleOffsetMarked;
    
    /* File type */
    protected int fileType;
    
    /* Endianness for current file (not necessarily same as _bigEndian) */
    protected boolean thisFileBigEndian;

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /* Chunk data orientation is big-endian. */
    private static final boolean BIGENDIAN = true;

    /* Values for fileType */
    public final static int 
        AIFFTYPE = 1,
        AIFCTYPE = 2;
        
    /* Fixed value for first 4 bytes */
    private static final int[] sigByte =
       { 0X46, 0X4F, 0X52, 0X4D };

    private static final String NAME = "AIFF-hul";
    private static final String RELEASE = "1.3";
    private static final int [] DATE = {2006, 9, 5};
    private static final String [] FORMAT = {
	"AIFF", "Audio Interchange File Format"
    };
    private static final String COVERAGE = "AIFF 1.3, AIFF-C";
    private static final String [] MIMETYPE = {
	"audio/x-aiff", "application/aiff"
    };
    private static final String WELLFORMED =
	"Magic number: \"FORM\" at byte offset 0; \"AIFF\"" +
        "(for AIFF) or \"AIFC\" (for AIFF-C) at offset 8; one Form chunk " +
	"containing one Common chunk and at most one Sound Data chunk " +
	"(if numSampleFrames > 0); at most one instance of each of the " +
	"following optional chunks: Marker, Instrument, Audio Recording, " +
	"Comments, Name, Author, Copyright; all chunks required by a given " +
        "profile exist in the file; all chunk structures are well-formed: " +
	"a four ASCII character ID, followed by a 32 signed integer size, " +
	"followed by a size byte data block (if size is odd, then the data " +
	"block includes a final padding byte of value 0x00); and no data " +
	"exist before the first byte of the chunk or after the " +
        "last byte of the last chunk";
    private static final String VALIDITY = "The file is well-formed";
    private static final String REPINFO =
	"Properties capturing the technical attributes of the audio " +
	"from all chunks";
    private static final String NOTE = null;
    private static final String RIGHTS = "Copyright 2004-2007 by JSTOR and " +
	"the President and Fellows of Harvard College. " +
	"Released under the GNU Lesser General Public License.";

    /******************************************************************
    * CLASS CONSTRUCTOR.
    ******************************************************************/
   /**
     *  Instantiates an <tt>AiffModule</tt> object.
     */
   public AiffModule ()
   {
       super (NAME, RELEASE, DATE, FORMAT, COVERAGE, MIMETYPE, WELLFORMED,
              VALIDITY, REPINFO, NOTE, RIGHTS, false);
       Agent agent = new Agent ("Harvard University Library",
                                AgentType.EDUCATIONAL);
       agent.setAddress ("Office for Information Systems, " +
                         "90 Mt. Auburn St., " +
                         "Cambridge, MA 02138");
       agent.setTelephone ("+1 (617) 495-3724");
       agent.setEmail("jhove-support@hulmail.harvard.edu");
       _vendor = agent;


       Document doc = new Document ("Audio Interchange File Format: " +
				    "\"AIFF\", A Standard for Sampled Sound " +
				    "Files, Version 1.3", DocumentType.REPORT);
       agent = new Agent ("Apple Computer, Inc.", 
                    AgentType.COMMERCIAL);
       agent.setAddress ("1 Infinite Loop, Cupertino, CA 95014");
       agent.setTelephone("(408) 996-1010");
       agent.setWeb ("http://www.apple.com/");
       doc.setAuthor (agent);
       doc.setDate ("1989-01-04");
       doc.setIdentifier (new Identifier ("http://developer.apple.com/documentation/QuickTime/INMAC/SOUND/imsoundmgr.30.htm#pgfId=3190",
                                          IdentifierType.URL));
       _specification.add (doc);

       doc = new Document ("Audio Interchange File Format AIFF-C: " +
                    "A revision to include compressed audio data",
                                    DocumentType.REPORT);
       doc.setAuthor (agent);
       doc.setDate ("1991-08-26");
       doc.setNote ("*** DRAFT ***");   // Asterisks as in the printed document
       _specification.add (doc);
                                           
       Signature sig = new ExternalSignature ("AIFF", SignatureType.FILETYPE,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
       sig = new ExternalSignature ("AIFC", SignatureType.FILETYPE,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
       sig = new ExternalSignature (".aif", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
       sig = new ExternalSignature (".aifc", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL,
                                    "For AIFF-C profile");
       _signature.add (sig);
       
       sig = new InternalSignature ("FORM", SignatureType.MAGIC, 
                                   SignatureUseType.MANDATORY, 0);
       _signature.add (sig);

       sig = new InternalSignature ("AIFF", SignatureType.MAGIC,
                                   SignatureUseType.OPTIONAL, 8,
                                   "For AIFF profile");
       _signature.add (sig);

       sig = new InternalSignature ("AIFC", SignatureType.MAGIC,
                                   SignatureUseType.OPTIONAL, 0,
                                   "For AIFF-C profile");
       _signature.add (sig);

       _bigEndian = true;
   }

   /**
    *   Parses the content of a purported AIFF digital object and stores the
    *   results in RepInfo.
    * 
    *
    *   @param stream    An InputStream, positioned at its beginning,
    *                    which is generated from the object to be parsed
    *   @param info       A fresh RepInfo object which will be modified
    *                    to reflect the results of the parsing
    *   @param parseIndex  Must be 0 in first call to <code>parse</code>.  If
    *                    <code>parse</code> returns a nonzero value, it must be
    *                    called again with <code>parseIndex</code> 
    *                    equal to that return value.
    */
   public int parse (InputStream stream, RepInfo info, int parseIndex)
       throws IOException
   {
       initParse ();
       info.setFormat (_format[0]);
       info.setMimeType (_mimeType[0]);
       info.setModule (this);
       _aesMetadata.setPrimaryIdentifier(info.getUri());
       if (info.getURLFlag ()) {
           _aesMetadata.setOtherPrimaryIdentifierType("URI");
       }
       else {
           _aesMetadata.setPrimaryIdentifierType(AESAudioMetadata.FILE_NAME);
       }

       /* We may have already done the checksums while converting a
          temporary file. */
       _ckSummer = null;
       if (_je != null && _je.getChecksumFlag () &&
           info.getChecksum ().size () == 0) {
           _ckSummer = new Checksummer ();
           _cstream = new ChecksumInputStream (stream, _ckSummer);
           _dstream = getBufferedDataStream (_cstream, _je != null ?
                   _je.getBufferSize () : 0);
       }
       else {
           _dstream = getBufferedDataStream (stream, _je != null ?
                   _je.getBufferSize () : 0);
       }

       try {
           // Check the start of the file for the right opening bytes
           for (int i = 0; i < 4; i++) {
               int ch = readUnsignedByte(_dstream, this);
               if (ch != sigByte[i]) {
                   info.setMessage(new ErrorMessage ("Document does not start with AIFF FORM Chunk", 0));
                   info.setWellFormed (RepInfo.FALSE);
                   return 0;
               }
           }
           /* If we got this far, take note that the signature is OK. */
           info.setSigMatch(_name);
           
           // Get the length of the Form chunk.  This includes all
           // the subsequent chunks in the file, but excludes the
           // header ("FORM" and the length itself).
//         bytesRemaining = readUnsignedInt (_dstream, _bigEndian, this);
           bytesRemaining = readUnsignedInt (_dstream,  BIGENDIAN, this);
           
           // Read the file type.
           if (!readFileType (info)) {
               return 0;
           }
    
           while (bytesRemaining > 0) {
               if (!readChunk (info)) {
                   break;
               }
           }
       }
       catch (EOFException e) {
           info.setWellFormed (RepInfo.FALSE);
           info.setMessage (new ErrorMessage 
                ("Unexpected EOF", _nByte));
           return 0;
       }
       
       if (!commonChunkSeen) {
           info.setWellFormed (RepInfo.FALSE);
           info.setMessage (new ErrorMessage
                ("Document does not contain a Common Chunk"));
       }
       if (fileType == AIFCTYPE && !formatVersionChunkSeen) {
           info.setWellFormed (RepInfo.FALSE);
           info.setMessage (new ErrorMessage
                ("AIFF-C document must contain a Format Version Chunk"));
       }
       if (info.getWellFormed () != RepInfo.TRUE) {
           return 0;
       }
       
       /* This file looks OK. */
       if (_ckSummer != null){
            /* We may not have actually hit the end of file. If we're calculating
             * checksums on the fly, we have to read and discard whatever is
             * left, so it will get checksummed. */
            for (;;) {
                try {
                    int n = skipBytes (_dstream, 2048, this);
                    if (n == 0) {
                        break;
                    }
                }
                catch (Exception e) {
                    break;
                }
            }
            info.setSize (_cstream.getNBytes ());
            info.setChecksum (new Checksum (_ckSummer.getCRC32 (), 
                        ChecksumType.CRC32));
            String value = _ckSummer.getMD5 ();
            if (value != null) {
                info.setChecksum (new Checksum (value, ChecksumType.MD5));
            }
            if ((value = _ckSummer.getSHA1 ()) != null) {
            info.setChecksum (new Checksum (value, ChecksumType.SHA1));
            }
       }

       if (fileType == AIFFTYPE) {
            info.setProfile("AIFF");
       }
       else if (fileType == AIFCTYPE) {
            info.setProfile ("AIFF-C");
       }

       _aesMetadata.setByteOrder (thisFileBigEndian ? AESAudioMetadata.BIG_ENDIAN :
				               AESAudioMetadata.LITTLE_ENDIAN);

       // Most properties were added by the Chunks.  The Annotations, Saxel
       // and MIDIData properties could have come from multiple chunks,
       // and these were added to lists which we now make into Properties
       // if there's anything to report.
       if (!_annotationList.isEmpty ()) {
           _propList.add (new Property ("Annotations",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                _annotationList));
       }
       if (!_midiList.isEmpty ()) {
           _propList.add (new Property ("MIDIData",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                _midiList));
       }
       if (!_saxelList.isEmpty ()) {
           _propList.add (new Property ("Saxels",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                _saxelList));
       }
       info.setProperty (_metadata);

       return 0;
   }

    /** Sets the endian-ness.  <code>true</code> indicates
     *  big-endian, and <code>false</code> means little-endian.
     *  This is needed because chunk data can change the
     *  usual little-endian byte order to big-endian.
     */
    public void setEndian (boolean bigEndian)
    {
        thisFileBigEndian = bigEndian;
    }

    /** Adds a Property to the AIFF metadata. */
    public void addAiffProperty (Property prop)
    {
        _propList.add (prop);
    }
    
    /** Adds an Annotation Property to the annotation list.
     *  This will get put into an Annotations Property. */
    public void addAnnotation (Property prop)
    {
        _annotationList.add (prop);
    }
    
    /** Adds a Saxel Property to the saxel list.
     *  This will get put into a Saxels Property. */
    public void addSaxel (Property prop)
    {
        _saxelList.add (prop);
    }
    
    /** Adds a MIDI Property to the MIDI list.
     *  This will get put into a MIDIData Property. */
    public void addMidi (Property prop)
    {
        _midiList.add (prop);
    }

    /**
     *   Initializes the state of the module for parsing.
     */
    protected void initParse() 
    {
        super.initParse ();

        thisFileBigEndian = _bigEndian;
       _propList = new LinkedList ();
       _metadata = new Property ("AIFFMetadata",
               PropertyType.PROPERTY,
               PropertyArity.LIST,
               _propList);

        firstSampleOffsetMarked = false;
        _aesMetadata = new AESAudioMetadata ();
        _aesMetadata.setAnalogDigitalFlag("FILE_DIGITAL");
        _aesMetadata.setFormat ("AIFF");    // Further data may modify this value
        _aesMetadata.setSpecificationVersion("1.3 (1989-01-04)");  // Ditto
        _aesMetadata.setAudioDataEncoding ("PCM");
//        _aesMetadata.setBitrateReduction ("PCM", "", "", "",
//                "LOSSY", "UNKNOWN", "FIXED");
        // Per Bugzilla 772, default is to omit bitrateReduction info
        _aesMetadata.clearBitrateReduction();
        _aesMetadata.setUse ("OTHER", "JHOVE_validation");
        _aesMetadata.setDirection ("NONE");
        
        _propList.add (new Property ("AESAudioMetadata",
                PropertyType.AESAUDIOMETADATA,
                _aesMetadata));
     
        // Create a List for accumulating properties from Annotation Chunks
        _annotationList = new LinkedList ();

        // Create a List for accumulating properties from MIDI Chunks
        _midiList = new LinkedList ();
       
        // Create a List for accumulating properties from SAXL chunks
        _saxelList = new LinkedList ();
       
        // Most chunk types are allowed to occur only once,
        // and a few must occur exactly once.
        // Clear flags for whether they have been seen.
        soundChunkSeen = false;
        commonChunkSeen = false;
        markerChunkSeen = false;
        formatVersionChunkSeen = false;
        instrumentChunkSeen = false;
        commentsChunkSeen = false;
        nameChunkSeen = false;
        authorChunkSeen = false;
        audioRecChunkSeen = false;
        copyrightChunkSeen = false;
    }

    /** One-argument version of <code>readUnsignedInt</code>. */
    public long readUnsignedInt (DataInputStream stream)
	throws IOException
    {
        return readUnsignedInt (stream,  BIGENDIAN, this);
    }

    /** One-argument version of <code>readUnsignedShort</code>.
     */
    public int readUnsignedShort (DataInputStream stream)
	throws IOException
    {
        return readUnsignedShort (stream,  BIGENDIAN, this);
    }

    /** One-argument version of <code>readSignedShort</code>.
     */
    public int readSignedShort (DataInputStream stream)
	throws IOException
    {
        return readSignedShort (stream, true, this);
    }
    
    /** This reads an 80-bit SANE number, aka IEEE 754 
     *  extended double.
     */
    public double read80BitDouble (DataInputStream stream)
	throws IOException
    {
        byte[] buf = new byte[10];
        readByteBuf(_dstream, buf, this);
        ExtDouble xd = new ExtDouble (buf);
        return xd.toDouble();
    }

    /**
     *   Reads 4 bytes and concatenates them into a String.
     *   This pattern is used for ID's of various kinds.
     */
    public String read4Chars(DataInputStream stream) throws IOException 
    {
        StringBuffer sbuf = new StringBuffer(4);
        for (int i = 0; i < 4; i++) {
            int ch = readUnsignedByte(stream, this);
            sbuf.append((char) ch);
        }
        return sbuf.toString();
    }
    
    /** Reads a Pascal string.
     *  A Pascal string is one whose count is given in the first
     *  byte.  The count is exclusive of the count byte itself.
     *  A Pascal string can have a maximum of 255 characters. 
     *  If the count of a Pascal string is even (meaning the total
     *  number of bytes is odd), there will be a pad byte to skip,
     *  so that the next item can start on an even boundary.
     * 
     *  We assume the string will be in ASCII or Macintosh encoding.
     */
    public String readPascalString (DataInputStream stream) throws IOException
    {
        int byteCnt = readUnsignedByte (stream, this);
        byte[] byteBuf = new byte[byteCnt];
        readByteBuf (_dstream, byteBuf, this);
        if ((byteCnt & 1) == 0) {
            skipBytes (_dstream, 1, this);
        }
        return new String (byteBuf, "MacRoman");
    }

    /** Converts a Macintosh-style timestamp (seconds since
     *  January 1, 1904) into a Java date.  The timestamp is
     *  treated as a time in the default localization.
     *  Depending on that localization,
     *  there may be some variation in the exact hour of the date 
     *  returned, e.g., due to daylight savings time.
     * 
     */
    public Date timestampToDate (long timestamp)
    {
        Calendar cal = Calendar.getInstance ();
        cal.set (1904, 0, 1, 0, 0, 0);
        
        // If we add the seconds directly, we'll truncate the long
        // value when converting to int.  So convert to hours plus
        // residual seconds.
        int hours = (int) (timestamp / 3600);
        int seconds = (int) (timestamp - (long) hours * 3600L);
        cal.add (Calendar.HOUR_OF_DAY, hours);
        cal.add (Calendar.SECOND, seconds);
        return cal.getTime ();
    }

    /** Returns the filetype, which is AIFFTYPE or AIFCTYPE. */
    public int getFileType ()
    {
        return fileType;
    }
    
    /** Marks the first sample offset as the current byte position,
     * if it hasn't already been marked.
     * The SSND chunk offset value must be added to the current
     * byte offset for a correct value.
     */
    public void markFirstSampleOffset (long offset)
    {
        if (!firstSampleOffsetMarked) {
            firstSampleOffsetMarked = true;
            _aesMetadata.setFirstSampleOffset (_nByte + offset);
        }
    }

    /** Reads the file type.   
     *  Broken out from parse().
     *  If it is not a valid file type, returns false.
     */
    protected boolean readFileType (RepInfo info) throws IOException
    {
        String typ = read4Chars (_dstream);
        bytesRemaining -= 4;
        if ("AIFF".equals (typ)) {
            fileType = AIFFTYPE;
            return true;
        }
        else if ("AIFC".equals (typ)) {
            fileType = AIFCTYPE;
            _aesMetadata.setFormat ("AIFF-C");
            _aesMetadata.setSpecificationVersion ("Draft 1991-08-26");
            return true;
        }
        else {
            info.setMessage (new ErrorMessage 
                    ("File type in Form Chunk is not AIFF or AIFC", _nByte));
            info.setWellFormed (RepInfo.FALSE);
            return false;
        }
    }

    /** Reads an AIFF Chunk.
     * 
     */
     protected boolean readChunk (RepInfo info) throws IOException
     {
        Chunk chunk = null;
        ChunkHeader chunkh = new ChunkHeader (this, info);
        if (!chunkh.readHeader(_dstream)) {
            return false;
        }
        int chunkSize = (int) chunkh.getSize ();
        bytesRemaining -= chunkSize + 8;
        
        String id = chunkh.getID ();
        if ("FVER".equals (id)) {
            if (formatVersionChunkSeen) {
                dupChunkError (info, "Format Version");
            }
            chunk = new FormatVersionChunk (this, chunkh, _dstream);
            formatVersionChunkSeen = true;
        }
        else if ("APPL".equals (id)) {
            chunk = new ApplicationChunk (this, chunkh, _dstream);
            // Any number of application chunks is ok
        }
        else if ("COMM".equals (id)) {
            if (commonChunkSeen) {
                dupChunkError (info, "Common");
            }
            chunk = new CommonChunk (this, chunkh, _dstream);
            commonChunkSeen = true;
        }
        else if ("SSND".equals (id)) {
            // Watch for multiple sound chunks
            if (soundChunkSeen) {
                dupChunkError (info, "Sound");
            }
            else {
                chunk = new SoundDataChunk (this, chunkh, _dstream);
                soundChunkSeen = true;
            }
        }
        else if ("COMT".equals (id)) {
            if (commentsChunkSeen) {
                dupChunkError (info, "Comments");
            }
            chunk = new CommentsChunk (this, chunkh, _dstream);
            commentsChunkSeen = true;
        }
        else if ("INST".equals (id)) {
            if (instrumentChunkSeen) {
                dupChunkError (info, "Instrument");
            }
            chunk = new InstrumentChunk (this, chunkh, _dstream);
            instrumentChunkSeen = true;
        }
        else if ("MARK".equals (id)) {
            if (markerChunkSeen) {
                dupChunkError (info, "Marker");
            }
            else {
                chunk = new MarkerChunk (this, chunkh, _dstream);
                markerChunkSeen = true;
            }
        }
        else if ("MIDI".equals (id)) {
            chunk = new MidiChunk (this, chunkh, _dstream);
            // Any number of MIDI chunks are allowed
        }
        else if ("NAME".equals (id)) {
            if (nameChunkSeen) {
                dupChunkError (info, "Name");
            }
            else {
                chunk = new NameChunk (this, chunkh, _dstream);
                nameChunkSeen = true;
            }
        }
        else if ("AUTH".equals (id)) {
            if (authorChunkSeen) {
                dupChunkError (info, "Author");
            }
            else {
                chunk = new AuthorChunk (this, chunkh, _dstream);
                authorChunkSeen = true;
            }
        }
        else if ("(c) ".equals (id)) {
            if (copyrightChunkSeen) {
                dupChunkError (info, "Copyright");
            }
            else {
                chunk = new CopyrightChunk (this, chunkh, _dstream);
                copyrightChunkSeen = true;
            }
        }
        else if ("AESD".equals (id)) {
            if (audioRecChunkSeen) {
                dupChunkError (info, "Audio Recording");
            }
            else {
                chunk = new AudioRecChunk (this, chunkh, _dstream);
                audioRecChunkSeen = true;
            }
        }
        else if ("SAXL".equals (id)) {
            chunk = new SaxelChunk (this, chunkh, _dstream);
            // Multiple saxel chunks are ok 
        }
        else if ("ANNO".equals (id)) {
            chunk = new AnnotationChunk (this, chunkh, _dstream);
            // Multiple annotations are OK
        }
        else {
            info.setMessage (new InfoMessage
                ("Chunk type '" + id + "' ignored", _nByte));
        }
        if (chunk != null) {
            try {
                if (!chunk.readChunk (info)) {
                    return false;
                }
            }
            catch (JhoveException e) {
                info.setMessage(new ErrorMessage (e.getMessage()));
                info.setWellFormed (false);
                return false;
            }
        }
        else {
            // Other chunk types are legal, just skip over them
            skipBytes (_dstream, chunkSize, this);
        }
        if ((chunkSize & 1) != 0) {
            // Must come out to an even byte boundary
            skipBytes (_dstream, 1, this);
            --bytesRemaining;
        }
        return true;   
     }

    /** Returns the module's AES metadata. */
    public AESAudioMetadata getAESMetadata ()
    {
        return _aesMetadata;
    }

    /* Factor out the reporting of duplicate chunks. */
    protected void dupChunkError (RepInfo info, String chunkName)
    {
        info.setMessage (new ErrorMessage
                        ("Multiple " + chunkName + " Chunks not permitted",
                         _nByte));
        info.setValid (false);
    }
}
