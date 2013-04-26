/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2007 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.module.wave.*;
import java.io.*;
import java.util.*;

/**
 * Module for identification and validation of WAVE sound files.
 * 
 * There is no published specification for WAVE files; this module
 * is based on several Internet sources.
 * 
 * WAVE format is a type of RIFF format.  RIFF, in turn, is a variant
 * on EA IFF 85.
 * 
 * @author Gary McGath
 */
public class WaveModule
    extends ModuleBase
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
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
    protected List<Property> _propList;
    
    /* List of Note properties */
    protected List<Property> _notes;
    
    /* List of Label properties */
    protected List<Property> _labels;
    
    /* List of Labeled Text properties */
    protected List<Property> _labeledText;
    
    /* List of Sample properties */
    protected List<Property> _samples;

    /* AES audio metadata to go into AIFF metadata */
    protected AESAudioMetadata _aesMetadata;

    /* Bytes remaining to be read. */
    protected long bytesRemaining;
    
    /* Bytes needed to store a file. */
    protected int _blockAlign;
    
    /* Exif data from file. */
    protected ExifInfo _exifInfo;
    
    /* Compression format, used for profile verification. */
    protected int compressionCode;

    /* Number of samples in the file.  Obtained from the
     * DATA chunk for uncompressed files, and the FACT
     * chunk for compressed ones. */
    protected long numSamples;
    
    /* Sample rate from file. */
    protected long sampleRate;

    /* Flag to check for exactly one format chunk */
    protected boolean formatChunkSeen;
    
    /* Flag to check for presence of fact chunk */
    protected boolean factChunkSeen;

    /* Flag to check for not more than one data chunk */
    protected boolean dataChunkSeen;

    /* Flag to check for not more than one instrument chunk */
    protected boolean instrumentChunkSeen;
    
    /* Flag to check for not more than one MPEG chunk */
    protected boolean mpegChunkSeen;
    
    /* Flag to check for not more than one Cart chunk */
    protected boolean cartChunkSeen;

    /* Flag to check for not more than one broadcast audio extension chunk */
    protected boolean broadcastExtChunkSeen;

    /* Flag to check for not more than one peak envelope chunk */
    protected boolean peakChunkSeen;

    /* Flag to check for not more than one link chunk */
    protected boolean linkChunkSeen;

    /* Flag to check for not more than one cue chunk */
    protected boolean cueChunkSeen;

    /* Profile flag for PCMWAVEFORMAT */
    protected boolean flagPCMWaveFormat;
    
    /* Profile flag for WAVEFORMATEX */
    protected boolean flagWaveFormatEx;
    
    /* Profile flag for WAVEFORMATEXTENSIBLE */
    protected boolean flagWaveFormatExtensible;
    
    /* Profile flag for Broadcast Wave format.  This indicates
     * only that the Format chunk is acceptable; it is also
     * necessary to verify that certain chunks were found. */
    protected boolean flagBroadcastWave;

    /* Version of Broadcast Wave, as determined from the Broadcast
     * Extension Chunk. */
    protected int broadcastVersion;
    
    /* Flag to note that first sample offset has been recorded */
    protected boolean firstSampleOffsetMarked;

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    
    /* Fixed value for first 4 bytes */
    private static final int[] sigByte =
       { 0X52, 0X49, 0X46, 0X46 };

    private static final String NAME = "WAVE-hul";
    private static final String RELEASE = "1.3";
    private static final int [] DATE = {2007, 12, 14};
    private static final String [] FORMAT = {
        "WAVE", 
        "Audio for Windows", 
        "EBU Technical Specification 3285", 
        "Broadcast Wave Format", 
        "BWF"
    };
    private static final String COVERAGE = 
    "WAVE (WAVEFORMAT, PCMWAVEFORMAT, WAVEFORMATEX, WAVEFORMATEXTENSIBLE), " +
	"Broadcast Wave Format (BWF) version 0 and 1";
    private static final String [] MIMETYPE = {"audio/x-wave", "audio/wave"};
    private static final String WELLFORMED = null;
    private static final String VALIDITY = null;
    private static final String REPINFO = null;
    private static final String NOTE = 
        "There is no published standard for WAVE files. This module regards " +
	"a file as valid if it conforms to common usage practices.";
    private static final String RIGHTS = "Copyright 2004-2007 by JSTOR and the " +
       "President and Fellows of Harvard College. " +
       "Released under the GNU Lesser General Public License.";

    /******************************************************************
    * CLASS CONSTRUCTOR.
    ******************************************************************/
   /**
     *  Instantiates an <tt>WaveModule</tt> object.
     */
   public WaveModule ()
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

       Agent msagent = new Agent ("Microsoft Corporation",
                    AgentType.COMMERCIAL);
       msagent.setAddress (" One Microsoft Way, " +
                "Redmond, WA 98052-6399");
       msagent.setTelephone ("+1 (800) 426-9400");
       msagent.setWeb ("http://www.microsoft.com");
       Document doc = new Document ("PCMWAVEFORMAT", DocumentType.WEB);
       doc.setIdentifier (new Identifier 
            ("http://msdn.microsoft.com/library/default.asp?url=/library/en-us/" +
                "multimed/htm/_win32_pcmwaveformat_str.asp", 
                IdentifierType.URL));
       doc.setPublisher (msagent);
       _specification.add (doc);
       
       doc = new Document ("WAVEFORMATEX", DocumentType.WEB);
       doc.setIdentifier (new Identifier 
            ("http://msdn.microsoft.com/library/default.asp?url=/library/en-us/" +
                "multimed/htm/_win32_waveformatex_str.asp", 
                IdentifierType.URL));
       doc.setPublisher (msagent);
       _specification.add (doc);
       
       doc = new Document ("WAVEFORMATEXTENSIBLE", DocumentType.WEB);
       doc.setIdentifier (new Identifier 
            ("http://msdn.microsoft.com/library/default.asp?url=/library/en-us/" +
                "multimed/htm/_win32_waveformatextensible_str.asp", 
                IdentifierType.URL));
       doc.setPublisher (msagent);
       _specification.add (doc);       
       
       agent = new Agent ("European Broadcasting Union", 
                    AgentType.COMMERCIAL);
       agent.setAddress ("Casa postale 45, Ancienne Route 17A, " +
                "CH-1218 Grand-Saconex, Geneva, Switzerland");
       agent.setTelephone ("+ 41 (0)22 717 2111");
       agent.setFax("+ 41 (0)22 747 4000");
       agent.setEmail("techreview@ebu.ch");
       agent.setWeb("http://www.ebu.ch");

       doc = new Document ("Broadcast Wave Format (EBU N22-1987)",
                                    DocumentType.REPORT);
       doc.setIdentifier (new Identifier 
            ("http://www.ebu.ch/CMSimages/en/tec_doc_t3285_tcm6-10544.pdf",
             IdentifierType.URL));
       doc.setPublisher(agent);
       _specification.add (doc);

       Signature sig = new ExternalSignature (".wav", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);

       sig = new ExternalSignature (".bwf", SignatureType.EXTENSION,
				    SignatureUseType.OPTIONAL,
				    "For BWF profile");
       _signature.add(sig);

       sig = new InternalSignature ("RIFF", SignatureType.MAGIC, 
                                   SignatureUseType.MANDATORY, 0);
       _signature.add (sig);
       sig = new InternalSignature ("WAVE", SignatureType.MAGIC, 
                                   SignatureUseType.MANDATORY, 8);
       _signature.add (sig);

       _bigEndian = false;
   }

   /**
    *   Parses the content of a purported WAVE digital object and stores the
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
                   info.setMessage(new ErrorMessage ("Document does not start with RIFF chunk", 0));
                   info.setWellFormed (false);
                   return 0;
               }
           }
           /* If we got this far, take note that the signature is OK. */
           info.setSigMatch(_name);
           
           // Get the length of the Form chunk.  This includes all
           // the subsequent chunks in the file, but excludes the
           // header ("FORM" and the length itself).
           bytesRemaining = readUnsignedInt (_dstream);
               
           // Read the file type.
           String typ = read4Chars (_dstream);
           bytesRemaining -= 4;
           if (!"WAVE".equals (typ)) {
               info.setMessage (new ErrorMessage 
                       ("File type in RIFF header is not WAVE", _nByte));
               info.setWellFormed (false);
               return 0;
           }
        
           while (bytesRemaining > 0) {
               if (!readChunk (info)) {
                   break;
               }
           }
       }
       catch (EOFException e) {
           info.setWellFormed (false);
           info.setMessage (new ErrorMessage 
                ("Unexpected end of file", _nByte));
           return 0;
       }
       catch (Exception e) {    // TODO make this more specific
           e.printStackTrace();
           info.setWellFormed (false);
           info.setMessage (new ErrorMessage 
                ("Exception reading file: " + e.getClass().getName() + 
                        ", " + e.getMessage(), _nByte));
           return 0;
       }
       
       // Set duration from number of samples and rate.
       if (numSamples > 0) {
           //_aesMetadata.setDuration((double) numSamples / sampleRate);
           _aesMetadata.setDuration (numSamples);
       }
       
       // Add note and label properties, if there's anything
       // to report.
       if (!_labels.isEmpty ()) {
           _propList.add (new Property ("Labels",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _labels));
       }
       if (!_labeledText.isEmpty ()) {
           _propList.add (new Property ("LabeledText",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _labeledText));
       }
       if (!_notes.isEmpty ()) {
           _propList.add (new Property ("Notes",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _notes));
       }
       if (!_samples.isEmpty ()) {
           _propList.add (new Property ("Samples",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _samples));
       }
       if (_exifInfo != null) {
           _propList.add (_exifInfo.buildProperty ());
       }
       if (!formatChunkSeen) {
           info.setMessage (new ErrorMessage
                ("No Format Chunk"));
           info.setWellFormed (false);
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

       info.setProperty (_metadata);
       
       // Indicate satisfied profiles.
       if (flagPCMWaveFormat) {
           info.setProfile ("PCMWAVEFORMAT");
       }
       if (flagWaveFormatEx) {
           info.setProfile ("WAVEFORMATEX");
       }
       if (flagWaveFormatExtensible) {
           info.setProfile ("WAVEFORMATEXTENSIBLE");
       }
       if (flagBroadcastWave) {
           // Need to do some additional checks.
           if (!broadcastExtChunkSeen) {
               flagBroadcastWave = false;
           }
           if (compressionCode == FormatChunk.WAVE_FORMAT_MPEG) {
               if (!broadcastExtChunkSeen || !factChunkSeen) {
                   flagBroadcastWave = false;
               }
           }
           if (flagBroadcastWave) {
               String prof = null;
               switch (broadcastVersion) {
                   case 0:
                   prof = "Broadcast Wave Version 0";
                   break;
                   
                   case 1:
                   prof = "Broadcast Wave Version 1";
                   break;
                   
                   // Other versions are unknown at this time
               }
               if (prof != null) {
                   info.setProfile (prof);
               }
           }
       }
       return 0;
   }

   /** Marks the first sample offset as the current byte position,
    *  if it hasn't already been marked. */
   public void markFirstSampleOffset ()
   {
       if (!firstSampleOffsetMarked) {
           firstSampleOffsetMarked = true;
           _aesMetadata.setFirstSampleOffset (_nByte);
       }
   }

   /** Sets an ExifInfo object for the module. */
   public void setExifInfo (ExifInfo exifInfo) 
   {
       _exifInfo = exifInfo;
   }
   
   /** Set the number of bytes that holds an aligned sample. */
   public void setBlockAlign (int align)
   {
       _blockAlign = align;
   }
   
   /** Returns the ExifInfo object.  If no ExifInfo object
    *  has been set, returns null. */
   public ExifInfo getExifInfo ()
   {
       return _exifInfo;
   }
   
   /** Returns the compression code. */
   public int getCompressionCode ()
   {
       return compressionCode;
   }
   
   /** Returns the number of bytes needed per aligned
    *  sample. */
   public int getBlockAlign ()
   {
       return _blockAlign;
   }

   /** Adds a Property to the WAVE metadata. */
   public void addWaveProperty (Property prop)
   {
       _propList.add (prop);
   }
    
   /** Adds a Label property */
   public void addLabel (Property p)
   {
       _labels.add (p);
   }

   /** Adds a LabeledText property */
   public void addLabeledText (Property p)
   {
       _labeledText.add (p);
   }
   
   /** Adds a Sample property */
   public void addSample (Property p)
   {
       _samples.add (p);
   }

   /** Adds a Note string */
   public void addNote (Property p)
   {
       _notes.add (p);
   }
   
   /** Adds the ListInfo property, which is a List of String Properties. */
   public void addListInfo (List l) {
       _propList.add (new Property ("ListInfo",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            l));
   }

   /** One-argument version of <code>readSignedLong</code>.
    *  WAVE is always little-endian, so readSignedInt can
    *  unambiguously drop its endian argument. */
    public long readSignedLong (DataInputStream stream)
           throws IOException
    {
       return readSignedLong (stream, false, this);
    }

   /** One-argument version of <code>readUnsignedInt</code>.
    *  WAVE is always little-endian, so readUnsignedInt can
    *  unambiguously drop its endian argument. */
    public long readUnsignedInt (DataInputStream stream)
           throws IOException
    {
       return readUnsignedInt (stream, false, this);
    }

   /** One-argument version of <code>readSignedInt</code>.
    *  WAVE is always little-endian, so readSignedInt can
    *  unambiguously drop its endian argument. */
    public int readSignedInt (DataInputStream stream)
           throws IOException
    {
       return readSignedInt (stream, false, this);
    }

   /** One-argument version of <code>readUnsignedShort</code>.
    *  WAVE is always little-endian, so readUnsignedShort can
    *  unambiguously drop its endian argument. */
    public int readUnsignedShort (DataInputStream stream)
           throws IOException
    {
       return readUnsignedShort (stream, false, this);
    }

   /** One-argument version of <code>readSignedShort</code>.
    *  WAVE is always little-endian, so readSignedShort can
    *  unambiguously drop its endian argument. */
    public int readSignedShort (DataInputStream stream)
           throws IOException
    {
       return readSignedShort (stream, false, this);
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
            if (ch != 0) {
                sbuf.append((char) ch);  // omit nulls
            }
        }
        return sbuf.toString();
    }

    /** Set the compression format.  Called from the Format
     *  chunk. */
    public void setCompressionCode (int cf)
    {
        compressionCode = cf;
    }
    
    /** Add to the number of data bytes. This may be called
     *  multiple times to give a cumulative total.
     */
    public void addSamples (long samples)
    {
        numSamples += samples;
    }
    
    /** Set the sample rate. */
    public void setSampleRate (long rate)
    {
        sampleRate = rate;
    }
    
    /** Set the profile flag for PCMWAVEFORMAT. */
    public void setPCMWaveFormat(boolean b)
    {
        flagPCMWaveFormat = b;
    }

    /** Set the profile flag for WAVEFORMATEX. */
    public void setWaveFormatEx(boolean b)
    {
        flagWaveFormatEx = b;
    }
    
    /** Set the profile flag for WAVEFORMATEXTENSIBLE. */
    public void setWaveFormatExtensible(boolean b)
    {
        flagWaveFormatExtensible = b;
    }
    
    /** Set the profile flag for Broadcast Wave. */
    public void setBroadcastWave (boolean b)
    {
        flagBroadcastWave = b;
    }
    
    /** Set the version from the Broadcast Extension chunk. */
    public void setBroadcastVersion (int version)
    {
        broadcastVersion = version;
    }
    
    /**
     *   Initializes the state of the module for parsing.
     */
    protected void initParse() 
    {
        super.initParse ();
       _propList = new LinkedList<Property> ();
       _notes = new LinkedList<Property> ();
       _labels = new LinkedList<Property> ();
       _labeledText = new LinkedList<Property> ();
       _samples = new LinkedList<Property> ();
       firstSampleOffsetMarked = false;
       numSamples = 0;
       
       _metadata = new Property ("WAVEMetadata",
               PropertyType.PROPERTY,
               PropertyArity.LIST,
               _propList);
        _aesMetadata = new AESAudioMetadata ();
        _aesMetadata.setByteOrder (AESAudioMetadata.LITTLE_ENDIAN);
        _aesMetadata.setAnalogDigitalFlag("FILE_DIGITAL");
        _aesMetadata.setFormat ("WAVE");
        _aesMetadata.setUse ("OTHER", "JHOVE_validation");
        _aesMetadata.setDirection ("NONE");

        _propList.add (new Property ("AESAudioMetadata",
                PropertyType.AESAUDIOMETADATA,
                _aesMetadata));

        // Most chunk types are allowed to occur only once,
        // and a few must occur exactly once.
        // Clear flags for whether they have been seen.
        formatChunkSeen = false;
        dataChunkSeen = false;
        instrumentChunkSeen = false;
        cartChunkSeen = false;
        mpegChunkSeen = false;
        broadcastExtChunkSeen = false;
        peakChunkSeen = false;
        linkChunkSeen = false;
	cueChunkSeen  = false;
        
        // Initialize profile flags
        flagPCMWaveFormat = false;
        flagWaveFormatEx = false;
        flagWaveFormatExtensible = false;
        flagBroadcastWave = false;
    }

   /** Reads a WAVE Chunk.
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
       
       if (bytesRemaining < 0) {
           info.setMessage (new ErrorMessage 
                ("Invalid chunk size", _nByte));
           return false;
       }
        
       String id = chunkh.getID ();
       if ("fmt ".equals (id)) {
           if (formatChunkSeen) {
               dupChunkError (info, "Format");
           }
           chunk = new FormatChunk (this, chunkh, _dstream);
           formatChunkSeen = true;
       }
       else if ("data".equals (id)) {
           if (dataChunkSeen) {
               dupChunkError (info, "Data");
           }
           chunk = new DataChunk (this, chunkh, _dstream);
           dataChunkSeen = true;
       }
       else if ("fact".equals (id)) {
           chunk = new FactChunk (this, chunkh, _dstream);
           factChunkSeen = true;
           // Are multiple 'fact' chunks allowed?
       }
       else if ("note".equals (id)) {
           chunk = new NoteChunk (this, chunkh, _dstream);
           // Multiple note chunks are allowed
       }
       else if ("labl".equals (id)) {
           chunk = new LabelChunk (this, chunkh, _dstream);
           // Multiple label chunks are allowed
       }
       else if ("list".equals (id)) {
           chunk = new AssocDataListChunk (this, chunkh, _dstream, info);
           // Are multiple chunks allowed?  Who knows?
       }
       else if ("LIST".equals (id)) {
           chunk = new ListInfoChunk (this, chunkh, _dstream, info);
           // Multiple list chunks must be OK, since there can
           // be different types, e.g., an INFO list and an exif list.
       }
       else if ("smpl".equals (id)) {
           chunk = new SampleChunk (this, chunkh, _dstream);
           // Multiple sample chunks are allowed -- I think
       }       
       else if ("inst".equals (id)) {
           if (instrumentChunkSeen) {
               dupChunkError (info, "Instrument");
           }
           chunk = new InstrumentChunk (this, chunkh, _dstream);
           // Only one instrument chunk is allowed
           instrumentChunkSeen = true;
       }
       else if ("mext".equals (id)) {
           if (mpegChunkSeen) {
               dupChunkError (info, "MPEG");
           }
           chunk = new MpegChunk (this, chunkh, _dstream);
           // I think only one MPEG chunk is allowed
           mpegChunkSeen = true;
       }
       else if ("cart".equals (id)) {
           if (cartChunkSeen) {
               dupChunkError (info, "Cart");
           }
           chunk = new CartChunk (this, chunkh, _dstream);
           cartChunkSeen = true;
       }
       else if ("bext".equals (id)) {
           if (broadcastExtChunkSeen) {
               dupChunkError (info, "Broadcast Audio Extension");
           }
           chunk = new BroadcastExtChunk (this, chunkh, _dstream);
           broadcastExtChunkSeen = true;
       }
       else if ("levl".equals (id)) {
           if (peakChunkSeen) {
               dupChunkError (info, "Peak Envelope");
           }
           chunk = new PeakEnvelopeChunk (this, chunkh, _dstream);
           peakChunkSeen = true;
       }
       else if ("link".equals (id)) {
           if (linkChunkSeen) {
               dupChunkError (info, "Link");
           }
           chunk = new LinkChunk (this, chunkh, _dstream);
           linkChunkSeen = true;
       }
       else if ("cue ".equals (id)) {
           if (cueChunkSeen) {
               dupChunkError (info, "Cue");
           }
           chunk = new CueChunk (this, chunkh, _dstream);
           cueChunkSeen = true;
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

    /** General function for adding a property with a 32-bit
     *  value, with two arrays of Strings to interpret
     *  0 and 1 values as a bitmask. 
     * 
     *  @param val            The bitmask
     *  @param name           The name for the Property
     *  @param oneValueNames  Array of names to use for '1' values
     *  @param zeroValueNames Array of names to use for '0' values
     */ 
    public Property buildBitmaskProperty (int val, String name,
                                       String [] oneValueNames,
                                       String [] zeroValueNames)
    {
        if (_je != null && _je.getShowRawFlag ()) {
            return new Property (name,
                        PropertyType.INTEGER,
                        new Integer (val));
        }
        else {
           List<String> slist = new LinkedList<String> ();
           try {
               for (int i = 0; i < oneValueNames.length; i++) {
                   String s = null;
                   if ((val & (1 << i)) != 0)  {
                       s = oneValueNames[i];
                   }
                   else {
                       s = zeroValueNames[i];
                   }
                   if (s != null && s.length() > 0) {
                       slist.add (s);
                   }
               }
           }
           catch (Exception e) {
               return null;
           }
           return new Property (name, PropertyType.STRING,
                                             PropertyArity.LIST, slist);
        }
    }
}
