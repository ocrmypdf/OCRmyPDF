/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2007 by JSTOR and the President and Fellows of Harvard College
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.pdf.*;
import java.io.*;
import java.util.*;
//Importing org.xml.sax.* would make Parser ambiguous
import org.xml.sax.XMLReader;
import org.xml.sax.SAXException;
//import org.xml.sax.InputSource;
import javax.xml.parsers.SAXParserFactory;

/** 
 *  Module for identification and validation of PDF files.
 */
public class PdfModule
    extends ModuleBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "PDF-hul";
    private static final String RELEASE = "1.7";
    private static final int [] DATE = {2012, 8, 12};
    private static final String [] FORMAT = {
        "PDF", "Portable Document Format"
    };
    private static final String COVERAGE = 
        "PDF 1.0-1.6; PDF/X-1 (ISO 15930-1:2001), X-1a (ISO 15930-4:2003), " +
	"X-2 (ISO 15930-5:2003), and X-3 (ISO 15930-6:2003); Tagged PDF; " +
	"Linearized PDF; PDF/A (ISO/CD 19005-1)";
    private static final String [] MIMETYPE = {"application/pdf"};
    private static final String WELLFORMED = "A PDF file is " +
        "well-formed if it meets the criteria defined in Chapter " +
        "3 of the PDF Reference 1.6 (5th edition, 2004)";
    private static final String VALIDITY = null;
    private static final String REPINFO = null;
    private static final String NOTE = "This module does *not* validate " +
	"data within content streams (including operators) or encrypted data";
    private static final String RIGHTS = "Copyright 2003-2007 by JSTOR and " +
	"the President and Fellows of Harvard College. " +
	"Released under the GNU Lesser General Public License.";
    private static final String ENCRYPTED = "<May be encrypted>";
    
    /** Font type selectors. */
    public final static int F_TYPE0 = 1,
            F_TYPE1 = 2,
            F_TT = 3,
            F_TYPE3 = 4,
            F_MM1 = 5,
            F_CID0 = 6,
            F_CID2 = 7;

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/
    
    /* The maximum number of fonts that will be reported before we just
     * give up and report a stub to avoid running out of memory. */
    protected int DEFAULT_MAX_FONTS = 1000;
    
    /* Constants for trailer parsing */
    private static final int EOFSCANSIZE = 1024;
    private static final int XREFSCANSIZE = 128; // generous...

    protected RandomAccessFile _raf;
    protected Parser _parser;
    protected String _version;
    protected Property _metadata;
    protected Property _xmpProp;
    protected long _eof;
    protected long _startxref;
    protected long _prevxref;
    protected int _numFreeObjects;
    protected Property _idProperty;
    protected int _objCount;     // Count of objects in the cross-reference table
    protected int _numObjects;   // Value of the "Size" entry in the trailer dictionary
    protected int _numTrailers;  // Count of the number of trailers (updates)
    protected Map _objects;      // Map of the objects in the file
    protected long[] _xref;      // array of object offsets from xref table
    protected int[] [] _xref2;   // array of int[2], giving object stream and offset when _xref[i] < 0
    protected boolean _xrefIsStream; // true if xref streams rather than tables are used
    protected boolean _encrypted;    // equivalent to _encryptDictRef != null
    protected List<Property> _docCatalogList;  // Info extracted from doc cat dict
    protected List<Property> _encryptList;     // Info from encryption dict
    protected List<Property> _docInfoList;     // info from doc info dict
    protected List<Property> _extStreamsList;  // List of external streams
    protected List<Property> _imagesList;      // List of image streams
    protected List<Property> _filtersList;     // List of filters
    protected List<Property> _pagesList;       // List of PageObjects

    protected Map<Integer, PdfObject> _type0FontsMap;    // Map of type 0 font dictionaries
    protected Map<Integer, PdfObject> _type1FontsMap;    // Map of type 1 font dictionaries
    protected Map<Integer, PdfObject> _mmFontsMap;       // Map of multi master font dictionaries
    protected Map<Integer, PdfObject> _type3FontsMap;    // Map of type 3 font dictionaries
    protected Map<Integer, PdfObject> _trueTypeFontsMap;   // Map of TrueType font dictionaries
    protected Map<Integer, PdfObject> _cid0FontsMap;   // Map of CIDFont/Type1 dictionaries
    protected Map<Integer, PdfObject> _cid2FontsMap;   // Map of CIDFont/TrueType dictionaries

    protected Map<Integer, Integer> _pageSeqMap;     // Map associating page object dicts with sequence numbers

    protected PdfIndirectObj _docCatDictRef;
    protected PdfIndirectObj _encryptDictRef;
    protected PdfIndirectObj _docInfoDictRef;
    protected PdfIndirectObj _pagesDictRef;
    
    protected PdfDictionary _docCatDict;
    protected PdfDictionary _docInfoDict;
    protected PageTreeNode _docTreeRoot;
    protected PdfDictionary _pageLabelDict;
    protected PageLabelNode _pageLabelRoot;
    protected NameTreeNode _embeddedFiles;
    protected NameTreeNode _destNames;
    protected PdfDictionary _encryptDict;
    protected PdfDictionary _trailerDict;
    protected PdfDictionary _viewPrefDict;
    protected PdfDictionary _outlineDict;
    protected PdfDictionary _destsDict;
    
    protected boolean _showFonts;
    protected boolean _showOutlines;
    protected boolean _showAnnotations;
    protected boolean _showPages;

    protected boolean _actionsExist;
    protected boolean _pdfACompliant;  // flag checking PDF/A compliance
    
    protected boolean _recursionWarned;  // Check if warning has been issued on recursive outlines.

    /* These three variables track whether a message has been posted
       notifying the user of omitted information. */
    protected boolean _skippedFontsReported;
    protected boolean _skippedOutlinesReported;
    protected boolean _skippedAnnotationsReported;
    protected boolean _skippedPagesReported;

    /** List of profile checkers */
    protected List<PdfProfile> _profile;
    
    /** Cached object stream. */
    protected ObjectStream _cachedObjectStream;
    
    /** Object number of cached object stream. */
    protected int _cachedStreamIndex;
    
    /** Map of visited nodes when walking through an outline. */
    protected Set<Integer> _visitedOutlineNodes;
    
    /** maximum number of fonts to report full information on. */
    protected int maxFonts;
    
    /** Number of fonts reported so far. */
    protected int _nFonts;
    
    /* These are the message texts to post in case of omitted
       information. */
    private final static String fontsSkippedString = 
        "Fonts exist, but are not displayed; to display " +
        "remove param value of f from the config file";
    private final static String outlinesSkippedString = 
        "Outlines exist, but are not displayed; to display " +
        "remove param value of o from the config file";
    private final static String annotationsSkippedString = 
        "Annotations exist, but are not displayed; to display " +
        "remove param value of a from the config file";
    private final static String pagesSkippedString = 
        "Page information is not displayed; to display " +
        "remove param value of p from the config file";

    /* Warning messages. */
    protected final static String outlinesRecursiveString =
        "Outlines contain recursive references.";
    
    /* Name-to-value array pairs for NISO metadata */
    private final static String[] compressionStrings = 
        { "LZWDecode", /* "FlateDecode", */ "RunLengthDecode", "DCTDecode", "CCITTFaxDecode"};
    private final static int[] compressionValues  =
        { 5, /* 8, */ 32773, 6, 2};
    /* The value of 2 (CCITTFaxDecode) is a placeholder; additional 
     * checking of the K parameter is needed to determine the real
     * value if that's returned. */
     
     private final static String [] colorSpaceStrings =
        { "Lab", "DeviceRGB", "DeviceCMYK", "DeviceGray", "Indexed" };
     private final static int[] colorSpaceValues =
        { 8, 2, 5, 1, 3 };
     
    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

        /**
         *  Creates an instance of the module and initializes identifying
         *  information.
         */
    public PdfModule ()
    {
        super (NAME, RELEASE, DATE, FORMAT, COVERAGE, MIMETYPE, WELLFORMED,
               VALIDITY, REPINFO, NOTE, RIGHTS, true);

        Agent agent = new Agent ("Harvard University Library",
                                 AgentType.EDUCATIONAL);
        agent.setAddress ("Office for Information Systems, " +
                          "90 Mt. Auburn St., " +
                          "Cambridge, MA 02138");
        agent.setTelephone ("+1 (617) 495-3724");
        agent.setEmail("jhove-support@hulmail.harvard.edu");
        _vendor = agent;

        Document doc = new Document ("PDF Reference: Adobe Portable " +
                                     "Document Format, Version 1.4",
                                     DocumentType.BOOK);
        agent = new Agent ("Adobe Systems, Inc.", AgentType.COMMERCIAL);
        agent.setAddress ("345 Park Avenue, San Jose, California 95110-2704");
        agent.setTelephone ("+1 (408) 536-6000");
        agent.setFax ("+1 (408) 537-6000");
        agent.setWeb ("http://www.adobe.com/");
        doc.setPublisher (agent);
        doc.setDate ("2001-12");
        doc.setEdition ("3rd edition");
        doc.setIdentifier (new Identifier ("0-201-75839-3",
                                           IdentifierType.ISBN));
        doc.setIdentifier (new Identifier ("http://partners.adobe.com/asn/" +
                                           "acrobat/docs/File_Format_" +
                                           "Specifications/PDFReference.pdf",
                                           IdentifierType.URL));
        _specification.add (doc);
        
        doc = new Document ("PDF Reference: Adobe Portable " +
                                     "Document Format, Version 1.5",
                                     DocumentType.BOOK);
        doc.setPublisher (agent);
        doc.setDate ("2003");
        doc.setEdition ("4th edition");
        doc.setIdentifier (new Identifier (
	"http://partners.adobe.com/public/developer/en/pdf/PDFReference15_v6.pdf",
                                           IdentifierType.URL));
        _specification.add (doc);

        doc = new Document ("PDF Reference: Adobe Portable " +
                                     "Document Format, Version 1.6",
                                     DocumentType.BOOK);
        doc.setPublisher (agent);
        doc.setDate ("2004-11");
        doc.setEdition ("5th edition");
        doc.setIdentifier (new Identifier (
        "http://partners.adobe.com/public/developer/en/pdf/PDFReference16.pdf",
                                           IdentifierType.URL));
        _specification.add (doc);


        doc = new Document ("Graphic technology -- Prepress " +
                "digital data exchange -- Use of PDF -- " +
                "Part 1: Complete exchange using CMYK data " +
                "(PDF/X-1 and PDF/X-1a)",
              DocumentType.STANDARD);
       Agent isoAgent = new Agent ("ISO", AgentType.STANDARD);
       isoAgent.setAddress ("1, rue de Varembe, Casa postale 56, " +
                            "CH-1211, Geneva 20, Switzerland");
       isoAgent.setTelephone ("+41 22 749 01 11");
       isoAgent.setFax ("+41 22 733 34 30");
       isoAgent.setEmail ("iso@iso.ch");
       isoAgent.setWeb ("http://www.iso.org");
       doc.setPublisher (isoAgent);
       doc.setDate ("2001-12-06");
       doc.setIdentifier (new Identifier ("ISO 15930-1:2001",
            IdentifierType.ISO));
       _specification.add (doc);


        doc = new Document ("Graphic technology -- Prepress " +
                "digital data exchange -- Use of PDF -- " +
                "Part 4: Complete exchange using CMYK and " +
                "spot colour printing data using " +
                "PDF 1.4 (PDF/X-1a)",
              DocumentType.STANDARD);
        doc.setPublisher (isoAgent);
        doc.setDate ("2003-08-04");
        doc.setIdentifier (new Identifier ("ISO 15930-4:2003",
            IdentifierType.ISO));
        _specification.add (doc);
        
        
        doc = new Document ("Graphic technology -- Prepress " +
                "digital data exchange -- Use of PDF -- " +
                "Part 5: Partial exchange of printing data " +
                "using PDF 1.4 (PDF/X-2)",
              DocumentType.STANDARD);
        doc.setPublisher (isoAgent);
        doc.setDate ("2003-08-05");
        doc.setIdentifier (new Identifier ("ISO 15930-5:2003",
            IdentifierType.ISO));
        _specification.add (doc);


        doc = new Document ("Graphic technology -- Prepress " +
                "digital data exchange -- Use of PDF -- " +
                "Part 6: Complete exchange suitable for " +
                "colour-managed workflows using " +
                "PDF 1.4 (PDF/X-3)",
              DocumentType.STANDARD);
        doc.setPublisher (isoAgent);
        doc.setDate ("2003-08-06");
        doc.setIdentifier (new Identifier ("ISO 15930-6:2003",
            IdentifierType.ISO));
        _specification.add (doc);
                
        _signature.add (new ExternalSignature (".pdf",
                                        SignatureType.EXTENSION,
                                        SignatureUseType.OPTIONAL));
        _signature.add (new InternalSignature ("%PDF-1.", 
                                        SignatureType.MAGIC,
                                        SignatureUseType.MANDATORY, 
                                        0));
        
        
        doc = new Document ("Document management -- Electronic " +
                "document file format for long-term " +
                "preservation -- Part 1: Use of PDF (PDF/A)",
              DocumentType.RFC);
        doc.setPublisher (isoAgent);
        doc.setDate ("2003-11-30");
        doc.setIdentifier (new Identifier ("ISO/CD 19005-1",
            IdentifierType.ISO));
        doc.setIdentifier (new Identifier 
            ("http://www.aiim.org/documents/standards/ISO_19005-1_(E).doc",
            IdentifierType.URL));
        _specification.add (doc);


        _profile = new ArrayList<PdfProfile> (6);
        _profile.add (new LinearizedProfile (this));
        TaggedProfile tpr = new TaggedProfile (this);
        _profile.add (tpr);
        AProfile apr = new AProfile (this);
        _profile.add (apr);
        // Link AProfile to TaggedProfile to save checking
        // the former twice.
        apr.setTaggedProfile (tpr);
        
        AProfileLevelA apra = new AProfileLevelA (this);
        _profile.add (apra);
        // AProfileLevelA depends on AProfile
        apra.setAProfile(apr);
        
        X1Profile x1 = new X1Profile (this); 
        _profile.add (x1);
        X1aProfile x1a = new X1aProfile (this); 
        _profile.add (x1a);
        // Linking the X1 profile to the X1a profile saves checking the former twice.
        x1a.setX1Profile (x1);
        _profile.add (new X2Profile (this));
        _profile.add (new X3Profile (this));
        _showAnnotations = false;
        _showFonts = false;
        _showOutlines = false;
        _showPages = false;
        maxFonts = DEFAULT_MAX_FONTS;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Parsing methods.
     ******************************************************************/

    /** Reset parameter settings.
     *  Returns to a default state without any parameters.
     */
    public void resetParams ()
        throws Exception
    {
        _showAnnotations = true;
        _showFonts = true;
        _showOutlines = true;
        _showPages = true;
        maxFonts = DEFAULT_MAX_FONTS;
    }

    /**
     * Per-action initialization.  May be called multiple times.
     *
     * @param param   The module parameter; under command-line Jhove, the -p parameter.
     *        If the parameter contains the indicated characters, then the
     *        specified information is omitted; otherwise, it is included.
     *        (This is the reverse of the behavior prior to beta 3.)
     *        These characters may be provided as separate parameters,
     *        or all in a single parameter.
     *        <ul>
     *          <li>a: annotations</li>
     *          <li>f: fonts</li>
     *          <li>o: outlines</li>
     *          <li>p: pages</li>
     *        </ul><br>
     *        The parameter is case-independent.  A null parameter is
     *        equivalent to the empty string.
     */
    public void param (String param)
    {
        if (param != null) {
            param = param.toLowerCase ();
            if (param.indexOf ('a') >= 0) {
                _showAnnotations = false;
            }
            if (param.indexOf ('f') >= 0) {
                _showFonts = false;
            }
            if (param.indexOf ('o') >= 0) {
                _showOutlines = false;
            }
            if (param.indexOf ('p') >= 0) {
                _showPages = false;
            }
            if (param.indexOf ('n') >= 0) {
                // Parse out the number after the n, and use that to set
                // the maximum number of fonts reported. Default is DEFAULT_MAX_FONTS.
                int n = param.indexOf ('n');
                StringBuffer b = new StringBuffer ();
                for (int i = n + 1; i < param.length(); i++) {
                    char ch =  param.charAt(i);
                    if (Character.isDigit (ch)) {
                        b.append(ch);
                    }
                    else {
                        break;
                    }
                }
                try {
                    int mx = Integer.parseInt (b.toString ());
                    if (mx > 0) {
                        maxFonts = mx;
                    }
                }
                catch (Exception e) {}
            }
        }
    }
    
    /**
     *  Parse a file and stores descriptive information.  A RandomAccessFile
     *  must be used to represent the object.
     *
     *  @param  raf   A PDF file
     *  @param  info  A clean RepInfo object, which will be modified to hold
     *                the descriptive information
     */
    public final void parse (RandomAccessFile raf, RepInfo info) 
        throws IOException
    {
        initParse ();
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        _objects = new HashMap ();
        _raf = raf;

        Tokenizer tok = new FileTokenizer (_raf);
        _parser = new Parser (tok);
        _parser.setObjectMap (_objects);

        List<Property> metadataList = new ArrayList<Property> (11);
        /* We construct a big whopping property,
           which contains up to 11 subproperties */
        _metadata = new Property ("PDFMetadata",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                metadataList);

        if (_raf.length () > 10000000000L) {    // that's 10^10
            _pdfACompliant = false;    // doesn't meet size limit in Appendix C of PDF spec
        }
        if (!parseHeader (info)) {
            return;
        }
        if (!findLastTrailer (info)) {
            return;
        }

        /* Walk through the linked trailer and cross reference
           sections. */
        _prevxref = -1;
        boolean lastTrailer = true;
        while (_startxref > 0) {
            // After the first (last) trailer, parse only for next "Prev" link
            if (!parseTrailer (info, !lastTrailer)) {
                return;
            }
            if (!readXRefInfo (info)) {
                return;
            }
            ++_numTrailers;
            if (_xrefIsStream) {
                /* If we have an xref stream, readXRefInfo dealt with all
                 * the streams in a single call. */
                break;
            }
            // Beware infinite loop on badly broken file
            if (_startxref == _prevxref) {
                info.setMessage (new ErrorMessage 
                        ("Cross reference tables are broken",
                         _parser.getOffset ()));
                info.setWellFormed (false);
                return;
            }
            _startxref = _prevxref;
            lastTrailer = false;
        }
        if (!readDocCatalogDict (info)) {
            return;
        }
        if (!readEncryptDict (info)) {
            return;
        }
        if (!readDocInfoDict (info)) {
            return;
        }
        if (!readDocumentTree (info)) {
            return;
        }
        if (!readPageLabelTree (info)) {
            return;
        }
        if (!readXMPData (info)) {
            return;   
        }
        findExternalStreams (info);
        if (!findFilters (info)) {
            return;
        }
        findImages (info);
        findFonts (info);

        /* Object is well-formed PDF. */

        /* We may have already done the checksums while converting a
           temporary file. */
        Checksummer ckSummer = null;
        if (_je != null && _je.getChecksumFlag () &&
            info.getChecksum ().size () == 0) {
            ckSummer = new Checksummer ();
            calcRAChecksum (ckSummer, raf);
            setChecksums (ckSummer, info);
        }

        info.setVersion (_version);
        metadataList.add(new Property ("Objects",
                                        PropertyType.INTEGER,
                                        new Integer (_numObjects)));
        metadataList.add (new Property ("FreeObjects",
                                        PropertyType.INTEGER,
                                        new Integer (_numFreeObjects)));
        metadataList.add (new Property ("IncrementalUpdates",
                                        PropertyType.INTEGER,
                                        new Integer (_numTrailers)));
        if (_docCatalogList != null) {
            metadataList.add (new Property("DocumentCatalog",
                                        PropertyType.PROPERTY,
                                        PropertyArity.LIST,
                                        _docCatalogList));
        }
        if (_encryptList != null) {
            metadataList.add (new Property ("Encryption",
                                        PropertyType.PROPERTY,
                                        PropertyArity.LIST,
                                        _encryptList));
        }
        if (_docInfoList != null) {
            metadataList.add (new Property ("Info",
                                        PropertyType.PROPERTY,
                                        PropertyArity.LIST,
                                        _docInfoList));
        }
        if (_idProperty != null) {
            metadataList.add (_idProperty);
        }
        if (_extStreamsList != null && !_extStreamsList.isEmpty ()) {
            metadataList.add (new Property ("ExternalStreams",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            _extStreamsList));
        }
        if (_filtersList != null && !_filtersList.isEmpty ()) {
            metadataList.add (new Property ("Filters",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            _filtersList));
        }
        if (_imagesList != null && !_imagesList.isEmpty ()) {
            metadataList.add (new Property ("Images",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            _imagesList));
        }
        if (_showFonts || _verbosity == Module.MAXIMUM_VERBOSITY) {
			try { addFontsProperty (metadataList); }
            catch (NullPointerException e) {
				info.setMessage(new ErrorMessage ("unexpected error in parsing font property", e.toString()));
			}
        }
        if (_nFonts > maxFonts) {
            info.setMessage(new InfoMessage ("Too many fonts to report; some fonts omitted.", 
                          "Total fonts = " + _nFonts));
        }
        if (_xmpProp != null) {
            metadataList.add (_xmpProp);
        }
        addPagesProperty (metadataList, info);

        if (!doOutlineStuff (info)) {
            return;
        }

        info.setProperty (_metadata);

        /* Check for profile conformance. */
        
        if (!_parser.getPDFACompliant ()) {
            _pdfACompliant = false;
        }
        ListIterator<PdfProfile> pter = _profile.listIterator ();
        if (info.getWellFormed() == RepInfo.TRUE) {
            // Well-formedness is necessary to satisfy any profile.
            while (pter.hasNext ()) {
                PdfProfile prof = (PdfProfile) pter.next ();
                if (prof.satisfiesProfile (_raf, _parser)) {
                    info.setProfile (prof.getText ());
                }
            }
        }
    }

    /**
     *  Returns true if the module hasn't detected any violations
     *  of PDF/A compliance.  This must return true, but is not
     *  sufficient by itself, to establish compliance.  The
     *  <code>AProfile</code> profiler makes the final determination.
     */
    public boolean mayBePDFACompliant ()
    {
        return _pdfACompliant;
    }

    /**
     *  Returns the document tree root.
     */
    public PageTreeNode getDocumentTree ()
    {
        return _docTreeRoot;
    }

    /**
     *  Returns the document information dictionary.
     */
    public PdfDictionary getDocInfo ()
    {
        return _docInfoDict;
    }

    /**
     *  Returns the encryption dictionary.
     */
    public PdfDictionary getEncryptionDict ()
    {
        return _encryptDict;
    }
    
    /**
     *  Return true if Actions have been detected in the file.
     */
    public boolean getActionsExist ()
    {
        return _actionsExist;
    }

    /**
     *   Initialize the module.  This is called at the start
     *   of parse restore the module to its initial state.
     */
    protected final void initParse ()
    {
        super.initParse ();
        _xref = null;
        _xref2 = null;
        _version = "";
        _objects = null;
        _numFreeObjects = 0;
        _objCount = 0;
        _docInfoList = null;
        _extStreamsList = null;
        _docCatalogList = null;
        _encryptList = null;
        _imagesList = null;
        _filtersList = null;
        _pagesList = null;
        _type0FontsMap = null;
        _type1FontsMap = null;
        _mmFontsMap = null;
        _type3FontsMap = null;
        _trueTypeFontsMap = null;
        _cid0FontsMap = null;
        _cid2FontsMap = null;
        _docCatDictRef = null;
        _encryptDictRef = null;
        _docInfoDictRef = null;
        _pagesDictRef = null;
        _docCatDict = null;
        _docInfoDict = null;
        _docTreeRoot = null;
        _pageLabelDict = null;
        _encryptDict = null;
        _trailerDict = null;
        _viewPrefDict = null;
        _outlineDict = null;
        _destsDict = null;
        _pageSeqMap = null;
        _pageLabelRoot = null;
        _embeddedFiles = null;
        _destNames = null;
        _skippedFontsReported = false;
        _skippedOutlinesReported = false;
        _skippedAnnotationsReported = false;
        _skippedPagesReported = false;
        _idProperty = null;
        _actionsExist = false;
        _numObjects = 0;
        _numTrailers = -1;
        _pdfACompliant = true;  // assume compliance till disproven
        _xmpProp = null;
        _cachedStreamIndex = -1;
        _nFonts = 0;
    }

    protected boolean parseHeader (RepInfo info) throws IOException
    {
        Token  token = null;
        String value = null;
        final String nohdr = "No PDF header";

        /* Parse file header. */

        boolean foundSig = false;
        for (;;) {
            if (_parser.getOffset() > 1024) {
                break;
            }
            try {
                token = null;
                token = _parser.getNext (1024L);
            }
            catch (IOException ee) {
                break;
            }
            catch (Exception e) {}   // fall through
            if (token == null) {
                break;
            }
            if (token instanceof Comment) {
                value = ((Comment) token).getValue ();
                if (value.indexOf ("PDF-1.") == 0) {
                    foundSig = true;
                    _version = value.substring (4, 7);
                    /* If we got this far, take note that the signature is OK. */
                    info.setSigMatch(_name);
                    break;
                }
                // The implementation notes (though not the spec)
                // allow an alternative signature of %!PS-Adobe-N.n PDF-M.m
                if (value.indexOf ("!PS-Adobe-") == 0) {
                    // But be careful: that much by itself is the standard
                    // PostScript signature.
                    int n = value.indexOf ("PDF-1.");
                    if (n >= 11) {
                        foundSig = true;
                        _version = value.substring (n + 4);
                        // However, this is not PDF-A compliant.
                        _pdfACompliant = false;
                        info.setSigMatch (_name);
                        break;
                    }
                }
            }

            // If we don't find it right at the beginning, we aren't
            // PDF/A compliant.
            _pdfACompliant = false;
        }
        if (!foundSig) {
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage (nohdr, 0L));
            return false;
        }
        // Check for PDF/A conformance.  The next item must be
        // a comment with four characters, each greater than 127
        try {
            token = _parser.getNext ();
            String cmt = ((Comment) token).getValue ();
            char[] cmtArray = cmt.toCharArray ();
            int ctlcnt = 0;
            for (int i = 0; i < 4; i++) {
                if ((int) cmtArray[i] > 127) {
                    ctlcnt++;
                }
            }
            if (ctlcnt < 4) {
                _pdfACompliant = false;
            }
        }
        catch (Exception e) { 
            // Most likely a ClassCastException on a non-comment
            _pdfACompliant = false;
        }
        return true;
    }

    
    private long lastEOFOffset(RandomAccessFile raf) throws IOException {

        long offset = 0;
        long flen = 0;
        byte[] buf = null;

        // overkill to restore fileposition, but make this
        // as side-effect free as possible
        long savepos = raf.getFilePointer();
        flen = raf.length();
        buf = new byte[(int) Math.min(EOFSCANSIZE, flen)];
        offset = flen - buf.length;
        raf.seek(offset);
        raf.read(buf);
        raf.seek(savepos);

        //OK:
        // flen is the total length of the file
        // offset is 1024 bytes from the end of file or 0 if file is shorter than 1024
        // buf contains all bytes from offset to end of file

        long eofpos = -1;
        // Note the limits, selected so the index never is out of bounds
        for (int i = buf.length-4; i >= 1; i--) {
            if (buf[i] == '%') {
              if ((buf[i-1] == '%') &&
                  (buf[i+1] == 'E') &&
                  (buf[i+2] == 'O') &&
                  (buf[i+3] == 'F')) {
                   eofpos = offset+i-1;
                   break;
              }
            }
        }

//        if (Tracing.T_MODULE) System.out.println(flen - eofpos);
        return eofpos;

    }

    
    private long lastStartXrefOffset(RandomAccessFile raf, long eofOffset) throws IOException {

        long offset = 0;
        long flen = 0;
        byte[] buf = null;

        // overkill to restore fileposition, but make this
        // as side-effect free as possible
        long savepos = raf.getFilePointer();
        flen = raf.length();
        if (eofOffset <= 0) {
            eofOffset = flen;
        }
        if (eofOffset >= flen) {
            eofOffset = flen;
        }
        buf = new byte[(int) Math.min(XREFSCANSIZE, eofOffset)];
        offset = eofOffset - buf.length;
        raf.seek(offset);
        raf.read(buf);
        raf.seek(savepos);

        //OK:
        // flen is the total length of the file
        // offset is 128 bytes from the end of file or 0 if file is shorter than 128
        // buf contains all bytes from offset to end of file

        long xrefpos = -1;
        // Note the limits, selected so the index never is out of bounds
        for (int i = buf.length-9; i >= 0; i--) {
            if (buf[i] == 's') {
              if ((buf[i+1] == 't') &&
                  (buf[i+2] == 'a') &&
                  (buf[i+3] == 'r') &&
                  (buf[i+4] == 't') &&
                  (buf[i+5] == 'x') &&
                  (buf[i+6] == 'r') &&
                  (buf[i+7] == 'e') &&
                  (buf[i+8] == 'f')) {
                   xrefpos = offset+i;
                   break;
              }
            }
        }

//        if (Tracing.T_MODULE) System.out.println(flen - xrefpos);
        return xrefpos;

    }
    

    /** Locate the last trailer of the file */
    protected boolean findLastTrailer (RepInfo info) throws IOException
    {
        /* Parse file trailer. Technically, this should be the last thing in
         * the file, but we follow the Acrobat convention of looking in the
         * last 1024 bytes. Since incremental updates may add multiple
         * EOF comments, make sure that we use the last one in the file. */

        Token  token = null;
        String value = null;

        _eof = lastEOFOffset(_raf);

        if (_eof < 0L) {
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage ("No PDF trailer",
                                               _raf.length ()));
            return false;
        }

        // For PDF-A compliance, this must be at the very end.
    /* Fix contributed by FCLA, 2007-05-30, to test for trailing data
     * properly.
     *
     * if (_raf.length () - _eof > 6) {
     */
        if (_raf.length () - _eof > 7) {
            _pdfACompliant = false;
        }

        /* Retrieve the "startxref" keyword. */

        long startxrefoffset = lastStartXrefOffset(_raf, _eof);
        _startxref = -1L;

        if (startxrefoffset >= 0) {
            try {
                _parser.seek (startxrefoffset); // points to the 'startxref' kw
                //_parser.seek (_eof - 23);   // should we allow more slop?
            }
            catch (PdfException e) {}
            while (true) {
                try {
                    token = _parser.getNext ();
                }
                catch (Exception e) {
                    // we're starting at an arbitrary point, so there
                    // can be parsing errors.  Ignore them till we get
                    // back in sync.
                    continue;
                }
                if (token == null) {
                    break;
                }
                if (token instanceof Keyword) {
                    value = ((Keyword) token).getValue ();
                    if (value.equals ("startxref")) {
                        try {
                            token = _parser.getNext ();
                        }
                        catch (Exception e) {
                            break;  // no excuses here
                        }
                        if (token != null && token instanceof Numeric) {
                            _startxref = ((Numeric) token).getLongValue ();
                        }
                    }
                }
            }
        }
        if (_startxref < 0L) {
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage ("Missing startxref keyword " +
                                   "or value", _parser.getOffset ()));
            return false;
        }
        return true;
    }
    /*  Parse a "trailer" (which is not necessarily the last
        thing in the file, as trailers can be linked.) */
    protected boolean parseTrailer (RepInfo info,
                                boolean prevOnly) 
                                throws IOException
    {
        Token  token = null;
        String value = null;
        String invalidMsg = "Invalid cross-reference table";
        /* Parse the trailer dictionary.  */

       try {
        _parser.seek (_startxref);
        /* The next object may be either the keyword "xref", signifying
         * a classic cross-reference table, or a stream object,
         * signifying the new-style cross-reference stream.
         */
        Token xref = _parser.getNext ();
        if (xref instanceof Keyword) {
            _xrefIsStream = false;
            _parser.getNext (Numeric.class, invalidMsg);  // first object number
            _objCount = ((Numeric) _parser.getNext 
                    (Numeric.class, invalidMsg)).getIntegerValue ();
            _parser.seek (_parser.getOffset () + _objCount*20);
        }
        else if (xref instanceof Numeric) {
            /* No cross-ref tables to backtrack. */
            _xrefIsStream = true;
            _prevxref = -1;
            /* But I do need to read the dictionary at this point, to get
             * essential stuff out of it. */
            PdfStream str = (PdfStream) _parser.readObjectDef((Numeric) xref);
            PdfDictionary dict = str.getDict();
            _docCatDictRef = (PdfIndirectObj) dict.get ("Root");
            if (_docCatDictRef == null) {
                throw new PdfInvalidException 
                    ("Root entry missing in cross-ref stream dictionary",
                     _parser.getOffset ());
            }
            /* We don't need to see a trailer dictionary.
             * Move along, move along.  */
            return true;
        }

        /* Now find the "trailer" keyword. */
        long trailer = -1L;
        while ((token = _parser.getNext ()) != null) {
            if (token instanceof Keyword) {
                value = ((Keyword) token).getValue ();
                if (value.equals ("trailer")) {
                    token = _parser.getNext ();
                    if (token instanceof DictionaryStart) {
                        trailer = _parser.getOffset () - 7L;
                        break;
                    }
                }
            }
        }
        if (trailer < 0L) {
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage ("No file trailer",
                                               _parser.getOffset ()));
            return false;
        }

        _trailerDict = _parser.readDictionary ();
        PdfObject obj;
        
        // Extract contents of the trailer dictionary

        _prevxref = -1;
        obj = _trailerDict.get ("Prev");
        if (obj != null) {
            if (obj != null && obj instanceof PdfSimpleObject) {
                token = ((PdfSimpleObject) obj ).getToken ();
                if (token instanceof Numeric)
                    _prevxref = ((Numeric) token).getLongValue ();
            }
            if (_prevxref < 0) {
                throw new PdfInvalidException 
                        ("Invalid Prev offset in trailer dictionary",
                          _parser.getOffset ());
            }
        }
        // If this isn't the last (first read) trailer, then we
        // ignore all the other dictionary entries.
        if (prevOnly) {
            return true;
        }

        obj = _trailerDict.get ("Size");
        if (obj != null) {
            _numObjects = -1;
            if (obj != null && obj instanceof PdfSimpleObject) {
                token = ((PdfSimpleObject) obj ).getToken ();
                if (token instanceof Numeric)
                    _numObjects = ((Numeric) token).getIntegerValue ();
                    _xref = new long[_numObjects];
            }
            if (_numObjects < 0) {
                throw new PdfInvalidException 
                        ("Invalid Size entry in trailer dictionary",
                         _parser.getOffset ());
            }
            if (_numObjects > 8388607) {
                // Appendix C implementation limit is enforced by PDF/A
                _pdfACompliant = false;
            }
        }
        else throw new PdfInvalidException 
                ("Size entry missing in trailer dictionary",
                 _parser.getOffset ());
        _docCatDictRef = (PdfIndirectObj) _trailerDict.get ("Root");
        if (_docCatDictRef == null) {
            throw new PdfInvalidException 
                ("Root entry missing in trailer dictionary",
                 _parser.getOffset ());
        }
        _encryptDictRef =(PdfIndirectObj) _trailerDict.get ("Encrypt");  // This is at least v. 1.1
        _encrypted = (_encryptDictRef != null);
        _parser.setEncrypted (_encrypted);

        PdfObject infoObj = _trailerDict.get("Info");
        if (infoObj != null && !(infoObj instanceof PdfIndirectObj)) {
            throw new PdfInvalidException ("Trailer dictionary Info key is " +
					   "not an indirect reference",
					   _parser.getOffset ());
        }
        _docInfoDictRef = (PdfIndirectObj) infoObj;

        obj = _trailerDict.get ("ID");      // This is at least v. 1.1
        if (obj != null) {
            String badID = "Invalid ID in trailer";
            if (obj instanceof PdfArray) {
                String [] id = new String[2];
                try { 
                    PdfArray idArray = (PdfArray) obj;
                    Vector<PdfObject> idVec = idArray.getContent ();
                    if (idVec.size () != 2) {
                        throw new PdfInvalidException (badID);
                    }
                    PdfSimpleObject idobj = (PdfSimpleObject) idVec.get(0);
                    id[0] = toHex
                            (((StringValuedToken) idobj.getToken () ).getRawBytes ());
                    idobj = (PdfSimpleObject) idVec.get(1);
                    id[1] = toHex
                            (((StringValuedToken) idobj.getToken () ).getRawBytes ());
                    _idProperty = new Property ("ID", PropertyType.STRING,
                                                PropertyArity.ARRAY, id);
                }
                catch (Exception e) {
                    throw new PdfInvalidException (badID);
                }
            }
            else {
                throw new PdfInvalidException (badID, _parser.getOffset ());
            }
        }
        obj = _trailerDict.get ("XRefStm");
        if (obj != null) {
            /* We have a "hybrid" cross-reference scheme.  This means we have
             * to go through the cross-reference stream and have its entries
             * supplement the cross-reference section. */
            _logger.warning("Hybrid cross-reference not yet implemented");
        }
       }
       catch (PdfException e) {

            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // If it's merely invalid rather than ill-formed, keep going
            return (e instanceof PdfInvalidException);
       }
       return true;
    }

    /* Parses the cross-reference table or stream. */
    protected boolean readXRefInfo (RepInfo info) throws IOException
    {
        if (_xrefIsStream) {
            return readXRefStreams (info);
        }
        else {
            return readXRefTables (info);
        }
    }
    
    /* Parses the cross-reference streams.  This is called from
     * readXRefInfo if there is no cross-reference table.
     * I still need to deal with hybrid cases.  All linked cross-reference
     * streams are handled here.
     */
    protected boolean readXRefStreams (RepInfo info) throws IOException
    {
        _pdfACompliant = false;   // current version of PDF/A doesn't recognize XREF streams
        while (_startxref > 0) {
            try {
                _parser.seek (_startxref);
                PdfStream pstream = 
                    (PdfStream) _parser.readObjectDef ();
                int sObjNum = pstream.getObjNumber();
                CrossRefStream xstream = new CrossRefStream (pstream);
                if (!xstream.isValid ()) {
                    return false;
                }
                xstream.initRead (_raf);
                int no = xstream.getNumObjects (); 
                if (_xref == null) {
                    _xref = new long [no];
                    _xref2 = new int[no] [];
                }
                if (sObjNum < 0 || sObjNum >= no) {
                    throw new PdfMalformedException 
                          ("Invalid object number in cross-reference stream", 
                          _parser.getOffset ());
                }
                _xref[sObjNum] = _startxref;  // insert the index of the xref stream itself
                _startxref = xstream.getPrevXref();
                try {
                    while (xstream.readNextObject()) {
                        int objNum = xstream.getObjNum();
                        if (xstream.isObjCompressed ()) {
                            // Hold off on this branch
                            _xref[objNum] = -1;  // defers to _xref2
                            _xref2[objNum] = new int[] {
                                xstream.getContentStreamObjNum(), 
                                xstream.getContentStreamIndex()
                            };
                        }
                        else {
                            if (_xref[objNum] == 0) {
                                _xref[objNum] = xstream.getOffset ();
                            }
                        }
                    }
                   _numFreeObjects += xstream.getFreeCount ();
                }
                catch (IOException e) {
                    info.setWellFormed (false);
                    info.setMessage (new ErrorMessage
                            ("Malformed cross reference stream",
                             _parser.getOffset ()));
                    return false;
                }
            }
            catch (PdfException e) {
    
                e.disparage (info);
                info.setMessage (new ErrorMessage 
                            (e.getMessage (), _parser.getOffset ()));
                // If it's merely invalid rather than ill-formed, keep going
                return (e instanceof PdfInvalidException);
            }
        }
        return true;  // incomplete, but let it through
    }

    /* Parses the cross-reference table.  This is called from
     * readXRefInfo if there is a cross-reference table. */
    protected boolean readXRefTables (RepInfo info) throws IOException
    {
        Token  token = null;
        String badXref = "Malformed cross-reference table";

        try {
            _parser.seek (_startxref);
            token = _parser.getNext ();  // "xref" keyword or numeric
            if (token instanceof Keyword) {
                while ((token = _parser.getNext ()) != null) {
                    int firstObj = 0;
                    // Look for the start of a cross-ref subsection, which
                    // begins with a base object number and a count.
                    if (token instanceof Numeric) {
                        firstObj = ((Numeric) token).getIntegerValue ();
                    }
                    else {
                        // On anything else, assume we're done with this section.
                        // (Most likely we've hit the keyword "trailer".
                        break;
                    }
                    _objCount = ((Numeric) _parser.getNext ()).getIntegerValue ();
                    for (int i=0; i<_objCount; i++) {
                        // In reading the cross-reference table, also check
                        // the extra syntactic requirements of PDF/A.
                        long offset = ((Numeric) _parser.getNext 
                            (Numeric.class, badXref)).getLongValue ();
                        _parser.getNext ();  // Generation number
                        if (_parser.getWSString ().length () > 1) {
                                _pdfACompliant = false;
                        }
                        token = _parser.getNext (Keyword.class, badXref);
                        if (_parser.getWSString ().length () > 1) {
                                _pdfACompliant = false;
                        }
                        // A keyword of "n" signifies an object in use,
                        // "f" signifies a free object.  If we already
                        // have an entry for this object, don't replace it.
                        String keyval = ((Keyword) token).getValue ();
                        if (keyval.equals ("n")) {
                            if (_xref[firstObj + i] == 0) {
                                _xref[firstObj + i] = offset;
                            }
                        }
                        else if (keyval.equals ("f")) {
                            _numFreeObjects++;
                        }
                        else {
                            throw new PdfMalformedException 
                                   ("Illegal operator in xref table", 
                                    _parser.getOffset ());
                        }
                    }
                }
            }
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage (e.getMessage (),
					       _parser.getOffset ()));
            return false;
        }
        catch (Exception e) {
            info.setValid (false);
            info.setMessage (new ErrorMessage (e.getMessage (),
					       _parser.getOffset ()));
        }
        return true;
    }

    protected boolean readDocCatalogDict (RepInfo info) 
                        throws IOException
    {
        final String nocat = "No document catalog dictionary";
        Property p = null;
        _docCatDict = null;
        _docCatalogList = new ArrayList<Property> (2);
        // Get the Root reference which we had before, and
        // resolve it to the dictionary object.
        if (_docCatDictRef == null) {
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage
                        (nocat, 0));
            return false;
        }
        try {
            _docCatDict = (PdfDictionary) resolveIndirectObject 
                            (_docCatDictRef);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        if (_docCatDict == null) {
            // If it fails here, it's ill-formed, not
            // just invalid
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage
                        (nocat, 0));
            return false;            
        }        
        try {

            PdfObject viewPref = _docCatDict.get("ViewerPreferences");
            viewPref = resolveIndirectObject (viewPref);
            if (viewPref instanceof PdfDictionary) {
                _viewPrefDict = (PdfDictionary) viewPref;
                p = buildViewPrefProperty (_viewPrefDict);
                _docCatalogList.add (p);
            }
            String pLayoutText = "SinglePage";   // default
            PdfObject pLayout = resolveIndirectObject (_docCatDict.get ("PageLayout"));
            if (pLayout instanceof PdfSimpleObject) {
                pLayoutText = ((PdfSimpleObject) pLayout).getStringValue ();
            }
            p = new Property ("PageLayout",
                                PropertyType.STRING,
                                pLayoutText);
            _docCatalogList.add (p);

            String pModeText = "UseNone";   // default
            PdfObject pMode = resolveIndirectObject (_docCatDict.get ("PageMode"));
            if (pMode instanceof PdfSimpleObject) {
                pModeText = ((PdfSimpleObject) pMode).getStringValue ();
            }
            p = new Property ("PageMode",
                                PropertyType.STRING,
                                pModeText);
            _docCatalogList.add (p);
            
            PdfObject outlines = resolveIndirectObject (_docCatDict.get ("Outlines"));
            if (outlines instanceof PdfDictionary) {
                _outlineDict = (PdfDictionary) outlines;
            }
            
            PdfObject lang = resolveIndirectObject (_docCatDict.get ("Lang"));
            if (lang != null && lang instanceof PdfSimpleObject) {
                String langText = ((PdfSimpleObject) lang).getStringValue ();
                p = new Property ("Language", PropertyType.STRING,
				  _encrypted ? ENCRYPTED : langText);
                _docCatalogList.add (p);
            }

            // The Pages dictionary doesn't go into the property,
            // but this is a convenient time to grab it and the page label dictionary.
            _pagesDictRef = (PdfIndirectObj) _docCatDict.get ("Pages");
            _pageLabelDict = (PdfDictionary) 
                        resolveIndirectObject (_docCatDict.get ("PageLabels"));
            
            // Grab the Version entry, and use it to override the
            // file header IF it's later.
            PdfObject vers = resolveIndirectObject (_docCatDict.get ("Version"));
            if (vers instanceof PdfSimpleObject) {
                String versString = ((PdfSimpleObject) vers).getStringValue ();
                String infoVersString = _version;
                try {
                    double ver = Double.parseDouble (versString);
                    double infoVer = Double.parseDouble (infoVersString);
                    /* Set a message if this doesn't agree with RepInfo */
                    if (ver != infoVer) {
                        info.setMessage (new InfoMessage
                            ("File header gives version as " +
                             versString +
                             ", but catalog dictionary gives version as " +
                             infoVersString));
                    }
                    /* Replace the version in RepInfo if this is larger */
                    if (ver > infoVer) {
                        _version = versString;
                    }
                }
                catch (NumberFormatException e) {
                    throw new PdfInvalidException 
                        ("Invalid Version in document catalog");
                }
            }
            
            // Get the Names dictionary in order to grab the 
            // EmbeddedFiles and Dests entries.
            final String badname = "Invalid Names dictionary";
            try {
                PdfDictionary namesDict = 
                    (PdfDictionary) resolveIndirectObject (_docCatDict.get ("Names"));
                if (namesDict != null) {
                    PdfDictionary embeddedDict = (PdfDictionary) resolveIndirectObject 
                            (namesDict.get ("EmbeddedFiles"));
                    if (embeddedDict != null) {
                        _embeddedFiles = new NameTreeNode (this, null, embeddedDict);
                    }

                    PdfDictionary dDict = (PdfDictionary) resolveIndirectObject
                            (namesDict.get ("Dests"));
                    if (dDict != null) {
                        _destNames = new NameTreeNode (this, null, dDict);
                    }
                }
            }
            catch (ClassCastException ce) {
                throw new PdfInvalidException (badname);
            }
            catch (Exception e) {
                throw new PdfMalformedException (badname);
            }

            // Get the optional Dests dictionary. Note that destinations
            // may be specified in either of two completely different
            // ways: a dictionary here, or a name tree from the Names 
            // dictionary. 

            try {
                _destsDict = (PdfDictionary) resolveIndirectObject
                        (_docCatDict.get ("Dests"));
            }
            catch (ClassCastException ce) {
                throw new PdfInvalidException ("Invalid Dests dictionary");
            }
            catch (Exception e) {
                throw new PdfMalformedException ("Invalid Dests dictionary");
            }
        }

        catch (PdfException e) {
            e.disparage (info);  // clears Valid or WellFormed as appropriate
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Keep going if it's only invalid
            return (e instanceof PdfInvalidException);
        }
        catch (Exception e) {
            // Unexpected exception -- declare not well-formed
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage
                        (e.toString (), _parser.getOffset ()));
            return false;
        }
        return true;
    }

    protected boolean readEncryptDict (RepInfo info) 
                        throws IOException
    {
        String filterText = "";
        String effText = null;
        // Get the reference which we had before, and
        // resolve it to the dictionary object.
        if (_encryptDictRef == null) {
            return true;        // encryption entry is optional
        }
        try {
            _encryptList = new ArrayList<Property> (6);
            PdfDictionary dict = (PdfDictionary) resolveIndirectObject 
                            (_encryptDictRef);
            _encryptDict = dict;

            PdfObject filter = dict.get ("Filter");
            if (filter instanceof PdfSimpleObject) {
                Token tok = ((PdfSimpleObject)filter).getToken ();
                if (tok instanceof Name) {
                    filterText = ((Name) tok).getValue ();
                }
            }
            Property p = new Property ("SecurityHandler",
                                PropertyType.STRING,
                                filterText);
            _encryptList.add (p);
            //PdfObject eff = dict.get ("EFF");
            if (filter instanceof PdfSimpleObject) {
                Token tok = ((PdfSimpleObject)filter).getToken ();
                if (tok instanceof Name) {
                    effText = ((Name) tok).getValue ();
                }
            }
            if (effText != null) {
                p = new Property ("EFF", PropertyType.STRING, effText);
                _encryptList.add (p);
            }

            int algValue = 0;
            PdfObject algorithm = dict.get ("V");
            if (algorithm instanceof PdfSimpleObject) {
                Token tok = ((PdfSimpleObject) algorithm).getToken ();
                if (tok instanceof Numeric) {
                    algValue = ((Numeric) tok).getIntegerValue ();
                    if (_je != null && _je.getShowRawFlag ()) {
                        p = new Property ("Algorithm",
                                PropertyType.INTEGER,
                                new Integer (algValue));
                    }
                    else {
                        try {
                            p = new Property ("Algorithm",
                                PropertyType.STRING,
                                PdfStrings.ALGORITHM[algValue]);
                        }
                        catch (Exception e) {
                            throw new PdfInvalidException 
                                ("Invalid algorithm value in encryption dictionary",
                                    _parser.getOffset ());
                        }
                    }
                    if (p != null) {
                        _encryptList.add (p);
                    }
                }
            }

            int keyLen = 40;
            PdfObject length = dict.get ("Length");
            if (length instanceof PdfSimpleObject) {
                Token tok = ((PdfSimpleObject) length).getToken ();
                if (tok instanceof Numeric) {
                    keyLen = ((Numeric) tok).getIntegerValue ();
                }
                if (_je != null) {
                        p = new Property ("KeyLength",
                                PropertyType.INTEGER,
                                new Integer (keyLen));
                        _encryptList.add (p);
                    }
            }

            if ("Standard".equals (filterText)) {
                List stdList = new ArrayList (4);
                // Flags have a known meaning only if Standard
                // security handler was specified
                PdfObject flagObj = dict.get ("P");
                PdfObject revObj = dict.get ("R");
                int rev = 2;    // assume old rev if not present
                if (revObj instanceof PdfSimpleObject) {
                    rev = ((PdfSimpleObject) revObj).getIntValue ();
                }
                if (flagObj instanceof PdfSimpleObject) {
                    int flags = 
                        ((PdfSimpleObject) flagObj).getIntValue ();
                    String[] flagStrs;
                    if (rev == 2) {
                        flagStrs = PdfStrings.USERPERMFLAGS2;
                    }
                    else {
                        flagStrs = PdfStrings.USERPERMFLAGS3;
                    }
                    p = buildUserPermProperty (flags, flagStrs);
                    stdList.add (p);
                    
                    stdList.add (new Property ("Revision",
                        PropertyType.INTEGER,
                        new Integer (rev)));
                }
                PdfObject oObj = dict.get ("O");
                if (oObj != null) {
                    if (oObj instanceof PdfSimpleObject) {
                        stdList.add (new Property ("OwnerString",
                            PropertyType.STRING,
                            toHex (((PdfSimpleObject) oObj).getRawBytes ())));
                    }
                }
                PdfObject uObj = dict.get ("U");
                if (uObj != null) {
                    if (uObj instanceof PdfSimpleObject) {
                        stdList.add (new Property ("UserString",
                            PropertyType.STRING,
                            toHex (((PdfSimpleObject) uObj).getRawBytes ())));
                    }
                }
                _encryptList.add (new Property ("StandardSecurityHandler",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    stdList));
            }
            
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            return (e instanceof PdfInvalidException);
        }
        return true;
    }

    protected boolean readDocInfoDict (RepInfo info) 
                        throws IOException
    {
        // Get the Info reference which we had before, and
        // resolve it to the dictionary object.
        if (_docInfoDictRef == null) {
            return true;        // Info is optional
        }
        _docInfoList = new ArrayList<Property> (9);
        try {
            _docInfoDict = (PdfDictionary) resolveIndirectObject 
                            (_docInfoDictRef);

            addStringProperty (_docInfoDict, _docInfoList, "Title", "Title");
            addStringProperty (_docInfoDict, _docInfoList, "Author", "Author");
            addStringProperty (_docInfoDict, _docInfoList, "Subject", "Subject");
            addStringProperty (_docInfoDict, _docInfoList, "Keywords", "Keywords");
            addStringProperty (_docInfoDict, _docInfoList, "Creator", "Creator");
            addStringProperty (_docInfoDict, _docInfoList, "Producer", "Producer");
            // CreationDate requires string-to-date conversion
            // ModDate does too
            addDateProperty (_docInfoDict, _docInfoList, "CreationDate", "CreationDate");
            addDateProperty (_docInfoDict, _docInfoList, "ModDate", "ModDate");
            addStringProperty (_docInfoDict, _docInfoList, "Trapped", "Trapped");
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Keep parsing if it's only invalid
            return (e instanceof PdfInvalidException);
        }
        catch (Exception e) {
            info.setWellFormed(false);
            info.setMessage (new ErrorMessage ("Unexpected exception " +
                    e.getClass().getName()));
        }
        return true;
    }

    protected boolean readDocumentTree (RepInfo info) 
                        throws IOException
    {
        try {
            if (_pagesDictRef == null) {
                throw new PdfInvalidException ("Document page tree not found");
            }
            
            PdfObject pagesObj = resolveIndirectObject (_pagesDictRef);
            if (!(pagesObj instanceof PdfDictionary)) 
                throw new PdfMalformedException ("Invalid page dictionary object");
            PdfDictionary pagesDict = (PdfDictionary) pagesObj;
            
            _docTreeRoot = new PageTreeNode (this, null, pagesDict);
            _docTreeRoot.buildSubtree (true, 100);
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Continue parsing if it's only invalid
            return (e instanceof PdfInvalidException);
        }
        catch (Exception e) {
            // Catch any odd exceptions
            info.setMessage (new ErrorMessage (e.getClass().getName(), _parser.getOffset ()));
            info.setWellFormed(false);
            return false;
        }
        return true;
    }
    
    protected boolean readPageLabelTree (RepInfo info) 
    {
        // the page labels number tree is optional.
        try {
            if (_pageLabelDict != null) {
                _pageLabelRoot = new PageLabelNode (this, null, _pageLabelDict);
                _pageLabelRoot.buildSubtree ();
            }
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Continue parsing if it's only invalid
            return (e instanceof PdfInvalidException);
        }
        catch (Exception e) {
            info.setWellFormed(false);
            info.setMessage (new ErrorMessage ("Unexpected exception " +
                    e.getClass().getName()));
            return false;
        }
        return true;        // always succeeds
    }
    
    protected boolean readXMPData (RepInfo info) 
    {
        final String badMetadata = "Invalid or ill-formed XMP metadata"; 
        try {
            PdfStream metadata = (PdfStream) resolveIndirectObject (_docCatDict.get ("Metadata"));
            if (metadata == null) {
                return true;    // Not required
            }
            //PdfDictionary metaDict = metadata.getDict ();
        
            // Create an InputSource to feed the parser.
            SAXParserFactory factory = 
                            SAXParserFactory.newInstance();
            factory.setNamespaceAware (true);
            XMLReader parser = factory.newSAXParser ().getXMLReader ();
            PdfXMPSource src = new PdfXMPSource (metadata, getFile ());
            XMPHandler handler = new XMPHandler ();
            parser.setContentHandler (handler);
            parser.setErrorHandler (handler);
            
            // We have to parse twice.  The first time, we may get
            // an encoding change as part of an exception thrown.  If this
            // happens, we create a new InputSource with the encoding, and
            // continue.
            try {
                parser.parse (src);
                _xmpProp = src.makeProperty ();
            }
            catch (SAXException se) {
                String msg = se.getMessage ();
                if (msg != null && msg.startsWith ("ENC=")) {
                    String encoding = msg.substring (5);
                    try {
                        src = new PdfXMPSource (metadata, getFile (), encoding);
                        parser.parse (src);
                        _xmpProp = src.makeProperty ();
                    }
                    catch (UnsupportedEncodingException uee) {
                        throw new PdfInvalidException (badMetadata);
                    }
                }
            }

        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Continue parsing if it's only invalid
            return (e instanceof PdfInvalidException);            
        }
        catch (Exception e) {
            info.setMessage (new ErrorMessage (badMetadata,
                        _parser.getOffset ()));
            info.setValid (false);
            return false;
        }
        return true;
    }
    
    protected void findExternalStreams (RepInfo info) throws IOException 
    {
        _extStreamsList = new LinkedList<Property> ();
		// stop processing if there is no root for the document tree
		if (_docTreeRoot == null)
	 		return;
        _docTreeRoot.startWalk ();
        try {
            for (;;) {
                // Get all the page objects in the document sequentially
                PageObject page = _docTreeRoot.nextPageObject ();
                if (page == null) {
                    break;
                }
                // Get the streams for the page and walk through them
                List<PdfObject> streams = page.getContentStreams ();
                if (streams != null) {
                    ListIterator<PdfObject> streamIter = streams.listIterator ();
                    while (streamIter.hasNext ()) {
                        PdfStream stream = (PdfStream) streamIter.next ();
                        String specStr = stream.getFileSpecification ();
                        if (specStr != null) {
                            Property prop = new Property ("File",
                                    PropertyType.STRING,
                                    specStr);
                            _extStreamsList.add (prop);
                        }
                    }
                }
            }
        }
        catch (Exception e) {
            info.setWellFormed(false);
            info.setMessage (new ErrorMessage ("Unexpected exception " +
                    e.getClass().getName()));
        }
    }

    /** Locates the filters in the content stream dictionaries
     *  and generate a list of unique pipelines.
     * 
     *  @return  <code>false</code> if the filter structure is
     *           defective.
     */
    protected boolean findFilters (RepInfo info) 
                throws IOException
    {
        _filtersList = new LinkedList<Property> ();
		// stop processing if there is no root for the document tree
		if (_docTreeRoot == null)
	 		return false;
        _docTreeRoot.startWalk ();
        try {
            for (;;) {
                // Get all the page objects in the document sequentially
                PageObject page = _docTreeRoot.nextPageObject ();
                if (page == null) {
                    break;
                }
                // Get the streams for the page and walk through them
                List<PdfObject> streams = page.getContentStreams ();
                if (streams != null) {
                    ListIterator<PdfObject> streamIter = streams.listIterator ();
                    while (streamIter.hasNext ()) {
                        PdfStream stream = (PdfStream) streamIter.next ();
                        Filter[] filters = stream.getFilters ();
                        extractFilters (filters, stream);
                    }
                }
            }
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (), _parser.getOffset ()));
            // Continue parsing if it's only invalid
            return (e instanceof PdfInvalidException);            
        }
        return true;
    }

    /** Finds the filters in a stream or array object which is the value
     * of a stream's Filter key, and put them in _filtersList
     * if a duplicate isn't there already.  If the name is
     * "Crypt", appends a colon and the name if available.
     * Returns the filter string whether it's added or not,
     * or null if there are no filters.
     */
    protected String extractFilters (Filter[] filters, PdfStream stream) 
    {
        /* Concatenate the names into a string of names separated
         * by spaces. */
        int len = filters.length;
        if (len == 0) {
            return null;
        }
        StringBuffer buf = new StringBuffer ();
        for (int i = 0; i < len; i++) {
            Filter filt = filters[i];
            String fname = filt.getFilterName ();
            buf.append(fname);
            /* If it's a Crypt filter, add the crypt name. */
            if ("Crypt".equals (fname)) {
                String cname = filt.getNameParam();
                if (cname != null) {
                    buf.append (":" + cname);
                }
            }
            if (i < len - 1) {
                buf.append (' ');
            }
        }
        String filterStr = buf.toString ();
        boolean unique = true;
        // Check for uniqueness.
        Iterator<Property> iter = _filtersList.iterator ();
        while (iter.hasNext ()) {
            Property p = (Property) iter.next ();
            String s = (String) p.getValue ();
            if (s.equals (filterStr)) {
                unique = false;
                break;
            }
        }
        if (filterStr != null && unique) {
            Property prop = new Property ("FilterPipeline",
                    PropertyType.STRING,
                    filterStr);
            _filtersList.add (prop);
        }
        return filterStr;
    }

    protected void findImages (RepInfo info) throws IOException
    {
        _imagesList = new LinkedList<Property> ();
        _docTreeRoot.startWalk ();
        try {
            for (;;) {
                // Get all the page objects in the document sequentially
                PageObject page = _docTreeRoot.nextPageObject ();
                if (page == null) {
                    break;
                }
                // Get the resources for the page and look for image XObjects
                PdfDictionary rsrc = page.getResources ();
                if (rsrc != null) {
                    PdfDictionary xo = (PdfDictionary)
                        resolveIndirectObject (rsrc.get ("XObject"));
                    if (xo != null) {
                        Iterator<PdfObject> iter = xo.iterator ();
                        while (iter.hasNext ()) {
                            // Get an XObject and check if it's an image.
                            PdfDictionary xobdict = null;
                            PdfObject xob = resolveIndirectObject 
                                    ((PdfObject) iter.next ());
                            if (xob instanceof PdfStream) {
                                xobdict = ((PdfStream) xob).getDict ();
                            }
                            if (xobdict != null) {
                                PdfSimpleObject subtype = (PdfSimpleObject) xobdict.get ("Subtype");
                                if ("Image".equals (subtype.getStringValue ())) {
                                    // It's an image XObject.  Report stuff.
                                    List<Property> imgList = new ArrayList<Property> (10);
                                    Property prop = new Property ("Image",
                                        PropertyType.PROPERTY,
                                        PropertyArity.LIST,
                                        imgList);
                                    NisoImageMetadata niso = new NisoImageMetadata ();
                                    imgList.add (new Property ("NisoImageMetadata",
                                               PropertyType.NISOIMAGEMETADATA, niso));
                                    niso.setMimeType("application/pdf");
                                    PdfSimpleObject widObj = (PdfSimpleObject)
                                        xobdict.get ("Width");
                                    niso.setImageWidth(widObj.getIntValue ());
                                    PdfSimpleObject htObj = (PdfSimpleObject)
                                        xobdict.get ("Height");
                                    niso.setImageLength(htObj.getIntValue ());
                                    
                                    // Check for filters to add to the filter list
                                    Filter[] filters = ((PdfStream) xob).getFilters ();
                                    String filt = extractFilters (filters, (PdfStream) xob);
                                    if (filt != null) {
                                        // If the filter is one which the NISO schema
                                        // knows about, put it in the NISO metadata,
                                        // otherwise put it in a Filter property.
                                        int nisoFilt = nameToNiso (filt,
                                            compressionStrings, compressionValues);
                                        if (nisoFilt >= 0) {
                                            /* If it's 2, it's a CCITTFaxDecode
					     * filter. There may be an optional
					     * K entry that can change the
					     * value.
					     */
                                            PdfObject parms =
						xobdict.get ("DecodeParms");
                                            if (parms != null) {
						PdfSimpleObject kobj = null;
						if (parms instanceof
						    PdfDictionary) {
						    kobj = (PdfSimpleObject)
							((PdfDictionary) parms).get ("K");
						}
						/* Note that the DecodeParms
						 * value may also be an array
						 * of dictionaries.  We are not
						 * handling that contingency.
						 */
						if (kobj != null) {
						    int k = kobj.getIntValue();
						    if (k < 0) {
							nisoFilt = 4;
						    }
						    else if (k > 0) {
							nisoFilt = 3;
						    } 
						}
					    }
					    niso.setCompressionScheme(nisoFilt);
					}
                                        else {
                                            imgList.add (new Property("Filter",
						      PropertyType.STRING, 
						      filt));
                                        }
                                    }
                                    else {
                                        niso.setCompressionScheme(1);  // no filter
                                    }

                                    // Check for color space info
                                    PdfObject colorSpc = xobdict.get ("ColorSpace");
                                    if (colorSpc != null) {
                                        String colorName = null;
                                        if (colorSpc instanceof PdfSimpleObject) {
                                            colorName = ((PdfSimpleObject) colorSpc).getStringValue ();
                                        }
                                        else if (colorSpc instanceof PdfArray) {
                                            Vector<PdfObject> vec = ((PdfArray) colorSpc).getContent ();
                                            // Use the first element, which is the color space family
                                            PdfSimpleObject fam = (PdfSimpleObject) vec.elementAt (0);
                                            colorName = fam.getStringValue ();
                                        }
                                        if (colorName != null) {
                                            int nisoSpace = nameToNiso (colorName,
                                                colorSpaceStrings, colorSpaceValues);
                                            if (nisoSpace >= 0) {
                                                niso.setColorSpace(nisoSpace);
                                            }
                                            else {
                                                imgList.add (new Property ("ColorSpace",
                                                    PropertyType.STRING,
                                                    colorName));
                                            }
                                        }
                                    }

                                    PdfSimpleObject bpc = (PdfSimpleObject)
                                        xobdict.get ("BitsPerComponent");
                                    if (bpc != null) {
                                        //imgList.add (new Property ("BitsPerComponent",
                                        //        PropertyType.INTEGER,
                                        //        new Integer (bpc.getIntValue ())));
                                        niso.setBitsPerSample(new int[] { bpc.getIntValue() });
                                    }

                                    PdfSimpleObject intent = (PdfSimpleObject)
                                        xobdict.get ("Intent");
                                    if (intent != null) {
                                        imgList.add (new Property ("Intent",
                                                PropertyType.STRING,
                                                intent.getStringValue ()));
                                    }

                                    PdfSimpleObject imgmsk = (PdfSimpleObject)
                                        xobdict.get ("ImageMask");
                                    if (imgmsk != null) {
                                        boolean b = imgmsk.isTrue ();
                                        imgList.add (new Property ("ImageMask",
                                                PropertyType.BOOLEAN,
                                                new Boolean (b)));
                                    }

                                    PdfArray dcd = (PdfArray) xobdict.get ("Decode");
                                    if (dcd != null) {
                                        Vector<PdfObject> dcdvec = dcd.getContent ();
                                        List<Integer> dcdlst = new ArrayList<Integer> (dcdvec.size ());
                                        Iterator<PdfObject> diter = dcdvec.iterator ();
                                        while (diter.hasNext ()) {
                                            PdfSimpleObject d = (PdfSimpleObject) diter.next ();
                                            dcdlst.add (new Integer (d.getIntValue ()));
                                        }
                                        imgList.add (new Property ("Decode",
                                            PropertyType.INTEGER,
                                            PropertyArity.LIST,
                                            dcdlst));
                                    }

                                    PdfSimpleObject intrp = (PdfSimpleObject)
                                        xobdict.get ("Interpolate");
                                    if (intrp != null) {
                                        boolean b = intrp.isTrue ();
                                        imgList.add (new Property ("Interpolate",
                                                PropertyType.BOOLEAN,
                                                new Boolean (b)));
                                    }

                                    PdfSimpleObject nam = (PdfSimpleObject)
                                        xobdict.get ("Name");
                                    if (nam != null) {
                                        imgList.add (new Property ("Name",
                                                PropertyType.STRING,
                                                nam.getStringValue ()));
                                    }

                                    PdfSimpleObject id = (PdfSimpleObject)
                                        resolveIndirectObject 
                                            (xobdict.get ("ID"));
                                    if (id != null) {
                                        String idstr = toHex (id.getStringValue ());
                                        imgList.add (new Property ("ID",
                                                PropertyType.STRING,
                                                idstr));
                                    }

                                    _imagesList.add (prop);
                                }

                            }
                        }
                    }
                }
            }
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                (e.getMessage (), _parser.getOffset ()));
        }
        catch (Exception e) {
            info.setWellFormed(false);
            info.setMessage (new ErrorMessage ("Unexpected exception " +
                    e.getClass().getName()));
        }
    }            

    /* Convert a Filter name to a NISO compression scheme value.
     * If the name is unknown to NISO, return -1. */
    protected int nameToNiso (String name, 
            String[] nameArray,
            int[] valArray)
    {
        for (int i = 0; i < nameArray.length; i++) {
            if (nameArray[i].equals (name)) {
                return valArray[i];
            }
        }
        return -1;   // no match
    }
    
    protected void findFonts (RepInfo info) throws IOException 
    {
        _type0FontsMap = new HashMap<Integer, PdfObject> ();
        _type1FontsMap = new HashMap<Integer, PdfObject> ();
        _trueTypeFontsMap = new HashMap<Integer, PdfObject> ();
        _mmFontsMap = new HashMap<Integer, PdfObject> ();
        _type3FontsMap = new HashMap<Integer, PdfObject> ();
        _cid0FontsMap = new HashMap<Integer, PdfObject> ();
        _cid2FontsMap = new HashMap<Integer, PdfObject> ();
            try {
        _docTreeRoot.startWalk ();
            for (;;) {
             // This time we need all the page objects and page tree
             // nodes, because resources can be inherited from
             // page tree nodes.
                DocNode node = _docTreeRoot.nextDocNode ();
                if (node == null) {
                    break;
                }
                // Get the fonts for the node 
                PdfDictionary fonts = null; 
                fonts = node.getFontResources ();
                if (fonts != null) {
                    // In order to make sure we have a collection of
                    // unique fonts, we store them in a map keyed by
                    // object number.
                    Iterator<PdfObject> fontIter = fonts.iterator ();
                    while (fontIter.hasNext ()) {
                        PdfObject fontRef = (PdfObject) fontIter.next ();
                        PdfDictionary font = (PdfDictionary)
                                resolveIndirectObject (fontRef);
                        addFontToMap (font);
                        // If we've been directed appropriately,
                        // we accumulate the information, but don't
                        // report it.  In that case, we post a message
                        // just once to that effect.
                        if (!_skippedFontsReported && 
                            !_showFonts && 
                            _verbosity != Module.MAXIMUM_VERBOSITY) {
                            info.setMessage (new InfoMessage
                                (fontsSkippedString));
                            _skippedFontsReported = true;
                        }
                    }
                }
            }
        }
        catch (PdfException e) {
            e.disparage (info);
            info.setMessage (new ErrorMessage 
                (e.getMessage (), _parser.getOffset ()));
            return;
        }
        catch (Exception e) {
            // Unexpected exception.
            _logger.warning( "PdfModule.findFonts: " + e.toString ());
            info.setWellFormed (false);
            info.setMessage (new ErrorMessage
                ("Unexpected error in findFonts", e.toString (), 
                    _parser.getOffset ()));
            return;
        }
    }

    /** Add the font to the appropriate map, and return its subtype.
     *  If we've exceeded the maximum number of fonts, then ignore it. */
    protected String addFontToMap (PdfDictionary font) 
    {
        if (++_nFonts > maxFonts) {
            return null;
        }
        String subtypeStr = null;
        try {
            PdfSimpleObject subtype =
                (PdfSimpleObject) font.get ("Subtype");
            subtypeStr = subtype.getStringValue ();
            if ("Type0".equals (subtypeStr)) {
                _type0FontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
                // If the font is Type 0, we must go
                // through its descendant fonts
                PdfObject desc0 = font.get ("DescendantFonts");
                PdfArray descendants = 
                    (PdfArray) resolveIndirectObject (desc0);
                Vector<PdfObject> subfonts = descendants.getContent ();
                Iterator<PdfObject> subfontIter = subfonts.iterator ();
                while (subfontIter.hasNext ()) {
                    PdfObject subfont = (PdfObject) subfontIter.next ();
                    subfont = resolveIndirectObject (subfont);
                    addFontToMap ((PdfDictionary) subfont);
                }
            }
            else if ("Type1".equals (subtypeStr)) {
                _type1FontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            else if ("MMType1".equals (subtypeStr)) {
                _mmFontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            else if ("Type3".equals (subtypeStr)) {
                _type3FontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            else if ("TrueType".equals (subtypeStr)) {
                _trueTypeFontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            else if ("CIDFontType0".equals (subtypeStr)) {
                _cid0FontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            else if ("CIDFontType2".equals (subtypeStr)) {
                _cid2FontsMap.put(
                    new Integer (font.getObjNumber ()),
                    font);
            }
            return subtypeStr;
        }
        catch (Exception e) {
            return null;
        }
    }


    /******************************************************************
     * PRIVATE CLASS METHODS.
     ******************************************************************/

    protected static String toHex (String s)
    {
        StringBuffer buffer = new StringBuffer ("0x");

        int len = s.length ();
        for (int i=0; i<len; i++) {
            String h = Integer.toHexString (s.charAt (i));
            if (h.length () < 2) {
                buffer.append ("0");
            }
            buffer.append (h);
        }

        return buffer.toString ();
    }

    protected static String toHex (Vector<Integer> v)
    {
        StringBuffer buffer = new StringBuffer ("0x");

        int len = v.size ();
        for (int i=0; i<len; i++) {
            int hdigit = ((Integer) v.elementAt (i)).intValue ();
            String h = Integer.toHexString (hdigit);
            if (h.length () < 2) {
                buffer.append ("0");
            }
            buffer.append (h);
        }

        return buffer.toString ();
    }

    // Store a PDF object in the object map.  The key is a Long
    // consisting of the concatenation of the object and generation
    // numbers.  Do I really need this?  Is the xref table
    // sufficient?
    /* protected void addObject (int objectNum, int genNum, Object obj)
    {
        long key = ((long) objectNum << 32) + 
                   ((long) genNum & 0XFFFFFFFF);
        _objects.put (new Long (key), obj);
    } */

    /**
     *  If the argument is an indirect object reference,
     *  returns the object it resolves to, otherwise returns
     *  the object itself.  In particular, calling with null will
     *  return null.
     */
    public PdfObject resolveIndirectObject(PdfObject indObj)
                        throws PdfException, IOException
    {
        if (indObj instanceof PdfIndirectObj) {
            int objIndex = ((PdfIndirectObj) indObj).getObjNumber ();
            /* Here we need to allow for the possibility that the
             *  object is compressed in an object stream.  That means
             *  creating a new structure (call it _xref2) that contains
             *  the stream object number and offset whenever _xref[objIndex]
             *  is negative.  _xref2 will have to contain the content
             *  stream object number (which will itself have to be
             *  resolved) and the offset into the object stream.
             */
            return getObject (objIndex, 30);
        }
        else {
            return indObj;
        }
    }
    
    /** Returns an object of a given number.  This may involve 
     *  recursion into object streams, in which case it calls itself.
     * 
     *  @param objIndex   The object number to look up
     *  @param recGuard   The maximum permitted number of recursion levels;
     *                    no particular value is required, but 30 or more
     *                    should avoid false exceptions.
     */
    protected PdfObject getObject (int objIndex, int recGuard)
            throws PdfException, IOException
    {
        /* Guard against infinite recursion */
        if (recGuard <= 0) {
            throw new PdfMalformedException ("Improper nesting of object streams");
        }
        final String nogood = "Invalid object number or object stream";
        long offset = _xref [objIndex];
        if (offset == 0) {
            return null;   // This is considered legitimate by the spec
        }
        if (offset < 0) {
            /* The object is located in an object stream. Need to get the
             * object stream first. 
             * Be cautious dealing with _cachedStreamIndex and _cachedObjectStream;
             * these can be modified by a recursive call to getObject. */
            try {
                int streamObjIndex = _xref2[objIndex][0];
                PdfObject streamObj;
                ObjectStream ostrm = null;
                if (streamObjIndex ==_cachedStreamIndex) {
                    ostrm = _cachedObjectStream;
                    // Reset it
                    if (ostrm.isValid ()) {
                        ostrm.readIndex ();
                    }
                }
                else {
                    streamObj = 
                        resolveIndirectObject (getObject (streamObjIndex, recGuard - 1));
                    if (streamObj instanceof PdfStream) {
                        ostrm = new ObjectStream ((PdfStream) streamObj, _raf);
                        if (ostrm.isValid ()) {
                            ostrm.readIndex ();
                            _cachedObjectStream = ostrm;
                            _cachedStreamIndex = streamObjIndex;
                        }
                        else {
                            throw new PdfMalformedException (nogood);
                        }
                    }
                }
                /* And finally extract the object from the object stream. */
                return ostrm.getObject (objIndex);
            }
            catch (Exception e) {
                /* Fall through with error */
            }
            throw new PdfMalformedException (nogood);
        }
        else {
            _parser.seek (offset);
            PdfObject obj = _parser.readObjectDef ();
            obj.setObjNumber (objIndex);
            return obj;
        }
    }

    /**
     *  Return the RandomAccessFile being read.
     */
    public RandomAccessFile getFile ()
    {
        return _raf;
    }
    
    /**
     *  Returns the catalog dictionary object.
     */
    public PdfDictionary getCatalogDict ()
    {
        return _docCatDict;
    }
    
    /**
     *  Returns the trailer dictionary object.
     */
    public PdfDictionary getTrailerDict ()
    {
        return _trailerDict;
    }
    
    /**
     *  Returns the viewer preferences dictionary object.
     */
    public PdfDictionary getViewPrefDict ()
    {
        return _viewPrefDict;
    }

    /**
     *  Returns the outlines dictionary object.
     */
    public PdfDictionary getOutlineDict ()
    {
        return _outlineDict;
    }
    
    /**
     *   Get a font map.  The map returned is determined by the selector.
     *   Any other value returns null.
     */
    public Map<Integer, PdfObject> getFontMap (int selector) 
    {
        switch (selector) {
            case F_TYPE0:
                return _type0FontsMap;
            case F_TYPE1:
                return _type1FontsMap;
            case F_TT:
                return _mmFontsMap;
            case F_TYPE3:
                return _type3FontsMap;
            case F_MM1:
                return _mmFontsMap;
            case F_CID0:
                return _cid0FontsMap;
            case F_CID2:
                return _cid2FontsMap;
            default:
                return null;
        }
    }

    /**
      * Return a List of all the font maps.  Together, these contain
      * all the fonts and subfonts in the document.  Some of the maps
      * may be null.
      */
    public List<Map<Integer, PdfObject>> getFontMaps ()
    {
        List<Map<Integer, PdfObject>> lst = new ArrayList<Map<Integer, PdfObject>> (7);
        lst.add (_type0FontsMap);
        lst.add (_type1FontsMap);
        lst.add (_mmFontsMap);
        lst.add (_type3FontsMap);
        lst.add (_trueTypeFontsMap);
        lst.add (_cid0FontsMap);
        lst.add (_cid2FontsMap);
        return lst;
    }

    /**
     *   Returns a NameTreeNode for the EmbeddedFiles entry of the
     *   Names dictionary.  Returns null if there isn't one.
     */
    public NameTreeNode getEmbeddedFiles ()
    {
        return _embeddedFiles;
    }

    /**
     * Add the various font lists as a fonts property. Note: only add
     * the "Fonts" property if there are, in fact, fonts defined.
     */
    protected void addFontsProperty (List<Property> metadataList)
    {
        List<Property> fontTypesList = new LinkedList<Property> ();
        Property fontp = null;
        if (_type0FontsMap != null && !_type0FontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("Type0", _type0FontsMap, F_TYPE0);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
                // Report an error here?
            }
        }
        if (_type1FontsMap != null && !_type1FontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("Type1", _type1FontsMap, F_TYPE1);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
                // Report an error here?
            }
        }
        if (_trueTypeFontsMap != null && !_trueTypeFontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("TrueType", _trueTypeFontsMap,
					   F_TT);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
                // Report an error here?
            }
        }
        if (_type3FontsMap != null && !_type3FontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("Type3", _type3FontsMap, F_TYPE3);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
            }
        }
        if (_mmFontsMap != null && !_mmFontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("MMType1", _mmFontsMap, F_MM1);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
            }
        }
        if (_cid0FontsMap != null && !_cid0FontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("CIDFontType0", _cid0FontsMap,
					   F_CID0);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
            }
        }
        if (_cid2FontsMap != null && !_cid2FontsMap.isEmpty ()) {
            try {
                fontp = buildFontProperty ("CIDFontType2", _cid2FontsMap,
					   F_CID2);
                fontTypesList.add (fontp);
            }
            catch (ClassCastException e) {
            }
        }
	if (fontTypesList.size () > 0) {
	    metadataList.add (new Property ("Fonts", PropertyType.PROPERTY,
					    PropertyArity.LIST,
					    fontTypesList));
	}
    }

    /* Build Pages property, with associated subproperties. */
    protected void addPagesProperty (List<Property> metadataList, RepInfo info) 
    {
        _pagesList = new LinkedList<Property> ();
        _pageSeqMap = new HashMap<Integer, Integer> (500);
        try {
            _docTreeRoot.startWalk ();
            int pageIndex = 0;
            // Start the pipe with two entries.
            // We always need to have the current and the next
            // entry from the page label tree in order to determine
            // the lower and upper bounds of the applicable range.
            // If the first entry has a bound greater than zero,
            // that appears to be an undefined situation, so we
            // always treat the first entry as starting at zero.
            if (_pageLabelRoot != null) {
                if (!_pageLabelRoot.findNextKeyValue ()) {
                    throw new PdfMalformedException ("Bad page labels");
                }

                _pageLabelRoot.findNextKeyValue ();
            }
            for (;;) {
                // Get all the page objects in the document sequentially
                // Have to do this in two passes so that link
                // destinations can be properly reported.
                PageObject page = _docTreeRoot.nextPageObject ();
                if (page == null) {
                    break;
                }
                _pageSeqMap.put (
                        new Integer (page.getDict ().getObjNumber ()),
                        new Integer (pageIndex + 1));
            }
            _docTreeRoot.startWalk ();
            for (;;) {
                PageObject page = _docTreeRoot.nextPageObject ();
                if (page == null) {
                    break;
                }
                Property p = buildPageProperty (page, pageIndex++, info);
                _pagesList.add (p);
            }
            if (_showPages || _verbosity == Module.MAXIMUM_VERBOSITY) {
                Property prop = new Property ("Pages",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            _pagesList);
                metadataList.add (prop);
            }
            else {
                if (!_skippedPagesReported) {
                    info.setMessage (new InfoMessage
                        (pagesSkippedString));
                }
                _skippedPagesReported = true;
            }
        }
        catch (PdfException e) {

            e.disparage (info);
            info.setMessage (new ErrorMessage 
                        (e.getMessage (),
                           _parser.getOffset ()));
            return ;
        }
    }

    /* Build a subproperty for one PageObject. */
    protected Property buildPageProperty (PageObject page, 
                        int idx,
                        RepInfo info)
                throws PdfException
    {
        List<Property> pagePropList = new ArrayList<Property> (4);
        try {
            // Foo on Java's inability to return values through
            // parameters.  Passing an array is a crock to achieve
            // that effect.
            int nominalNum[] = new int[1];
            Property plProp = buildPageLabelProperty (page, idx, nominalNum);
            if (plProp != null) {
                pagePropList.add (plProp);
            }
            if (plProp == null || nominalNum[0] != idx + 1) {
                // Page sequence is different from label, or
                // there is no label.  Make it 1-based.
                pagePropList.add (new Property ("Sequence",
                                PropertyType.INTEGER,
                                new Integer (idx + 1)));
               
            }
        }
        catch (PdfException e) {
            throw e;
        }
        catch (Exception f) {
            throw new PdfMalformedException ("Invalid page label info");
        }

        try {
            List<Property> annotsList = new LinkedList<Property> ();
            PdfArray annots = page.getAnnotations ();
            if (annots != null) {
                Vector<PdfObject> contents = annots.getContent ();
                for (int i = 0; i < contents.size (); i++) {
                    PdfDictionary annot = 
                        (PdfDictionary) resolveIndirectObject 
                                ((PdfObject) contents.elementAt (i));
                    annotsList.add (buildAnnotProperty (annot, info));
                }
                if (!annotsList.isEmpty ()) {
                    if (_showAnnotations || 
                      _verbosity == Module.MAXIMUM_VERBOSITY) {
                        Property annotProp = new Property ("Annotations",
                                PropertyType.PROPERTY,
                                PropertyArity.LIST,
                                annotsList);
                        pagePropList.add (annotProp);
                    }
                    else {
                        // We don't report annotations if we got here,
                        // but we do report that we don't report them.
                        if (!_skippedAnnotationsReported) {
                            info.setMessage (new InfoMessage
                                (annotationsSkippedString));
                            _skippedAnnotationsReported = true;
                        }
                    }
                }
            }
        }
        catch (PdfException e) {
            throw e;
        }
        catch (Exception f) {
            throw new PdfMalformedException ("Invalid Annotation list");
        }

        try {
            // Rotation property is inheritable
            PdfSimpleObject rot = (PdfSimpleObject) page.get ("Rotate", true);
            if (rot != null && rot.getIntValue () != 0) {
                pagePropList.add (new Property ("Rotate", 
                        PropertyType.INTEGER,
                        new Integer (rot.getIntValue ())));
            }

            // UserUnit property (1.6), not inheritable
            PdfSimpleObject uu = (PdfSimpleObject) page.get ("UserUnit", false);
            if (uu != null) {
                pagePropList.add (new Property ("UserUnit",
                        PropertyType.DOUBLE,
                        new Double (rot.getDoubleValue())));
            } 
            // Viewport dictionaries (1.6), not inheritable
            PdfArray vp = (PdfArray) page.get ("VP", false);
            if (vp != null) {
                Vector<PdfObject> vpv = vp.getContent();
                Iterator<PdfObject> iter = vpv.iterator();
                List<Property> vplist = new ArrayList<Property> (vpv.size());
                while (iter.hasNext ()) {
                    PdfDictionary vpd = (PdfDictionary) 
                        resolveIndirectObject((PdfObject) iter.next ());
                    PdfObject vpdbb = vpd.get ("BBox");
                    List<Property> vpPropList = new ArrayList<Property> ();
                    vpPropList.add (makeRectProperty 
                        ((PdfArray) resolveIndirectObject (vpdbb),
                         "BBox"));
                    PdfObject meas = vpd.get ("Measure");
                    if (meas instanceof PdfDictionary) {
                        vpPropList.add (buildMeasureProperty ((PdfDictionary) meas));
                        // No, that's wrong -- the Viewport property itself
                        // needs to be a list with a bounding box.
                    }
                    vplist.add (new Property ("Viewport",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            vpPropList));
                }
                pagePropList.add (new Property ("Viewports",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        vplist));
            }
            // Thumbnail -- we just report if it's there. It's a 
            // non-inheritable property
            PdfObject thumb = page.get ("Thumb", false);
            if (thumb != null) {
                pagePropList.add (new Property ("Thumb",
                        PropertyType.BOOLEAN,
                        Boolean.TRUE));
            }
            return new Property ("Page",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    pagePropList);
        }
//        catch (PdfException e) {
//            throw e;
//        }
        catch (Exception f) {
            throw new PdfMalformedException ("Invalid page dictionary");
        }
    }

    /* Build a subproperty of a subproperty for page labels.
     * The nomNumRef argument is a crock for returning the
     * nominal number; element 0 of the array is replaced
     * by the nominal number of the page. */
    protected Property buildPageLabelProperty (PageObject page,
                        int pageIndex,
                        int[] nomNumRef)
                        throws PdfException
    {
        if (_pageLabelRoot == null) {
            return null;        // no page label info
        }

        // Note that our "current" page is the page label tree's
        // "previous" key.  Sorry about that...
        int curFirstPage = _pageLabelRoot.getPrevKey ();
        int nextFirstPage = _pageLabelRoot.getCurrentKey ();
        try {
            // If we're onto the next page range, advance our pointers.
            if (pageIndex >= nextFirstPage) {
                _pageLabelRoot.findNextKeyValue ();
                curFirstPage = nextFirstPage;
            }
            PdfDictionary pageLabelDict = 
                (PdfDictionary) resolveIndirectObject 
                        (_pageLabelRoot.getPrevValue ());
            StringBuffer labelText = new StringBuffer ();
            PdfSimpleObject prefixObj = 
                (PdfSimpleObject) pageLabelDict.get ("P");
            if (prefixObj != null) {
                labelText.append (prefixObj.getStringValue ());
            }
            PdfSimpleObject firstPageObj =
                (PdfSimpleObject) pageLabelDict.get ("St");
            int nominalPage;
            if (firstPageObj != null) {
                nominalPage = pageIndex - curFirstPage + 
                                firstPageObj.getIntValue ();
            }
            else {
                nominalPage = pageIndex - curFirstPage + 1;
            }
            if (nominalPage <= 0) {
                throw new PdfInvalidException ("Invalid page label sequence");
            }
            nomNumRef[0] = nominalPage;
            
            // Get the numbering style.  If there is no numbering
            // style entry, the label consists only of the prefix.
            PdfSimpleObject numStyleObj = 
                        (PdfSimpleObject) pageLabelDict.get ("S");
            String numStyle;
            if (numStyleObj == null) {
                numStyle = null;
            }
            else {
                numStyle = numStyleObj.getStringValue ();
            }
            if ("D".equals (numStyle)) {
                // Nice, simple decimal numbers
                labelText.append (nominalPage);
            }
            else if ("R".equals (numStyle)) {
                // Upper case roman numerals
                labelText.append 
                        (PageLabelNode.intToRoman (nominalPage, true));
            }
            else if ("r".equals (numStyle)) {
                // Lower case roman numerals
                labelText.append 
                        (PageLabelNode.intToRoman (nominalPage, false));
            }
            else if ("A".equals (numStyle)) {
                // Uppercase letters (A-Z, AA-ZZ, ...)
                labelText.append
                        (PageLabelNode.intToBase26 (nominalPage, true));
            }
            else if ("a".equals (numStyle)) {
                // Lowercase letters (a-z, aa-zz, ...)
                labelText.append
                        (PageLabelNode.intToBase26 (nominalPage, false));
            }
            // It screws up the PDF output if we have a blank Label property.
            if (labelText.length() == 0) {
                labelText.append("[empty]");
            }
            return new Property ("Label",
                        PropertyType.STRING,
                        labelText.toString ());
        }
        catch (Exception e) {
            throw new PdfMalformedException ("Problem with page label structure");
        }
    }


    /* Build a subproperty for a measure dictionary. */
    protected Property buildMeasureProperty (PdfDictionary meas)
    {
        List<Property> plist = new ArrayList<Property> ();
        PdfObject itemObj = meas.get ("Subtype");
        if (itemObj instanceof PdfSimpleObject) {
            plist.add (new Property ("Subtype",
                        PropertyType.STRING,
                        ((PdfSimpleObject)itemObj).getStringValue ()));
        }
        itemObj = meas.get ("R");
        if (itemObj instanceof PdfSimpleObject) {
            plist.add (new Property ("Ratio",
                        PropertyType.STRING,
                        ((PdfSimpleObject) itemObj).getStringValue ()));
        }
        // All kinds of stuff I could add -- limit it to the required
        // X, Y, D and A arrays.
        itemObj = meas.get ("X");
        if (itemObj instanceof PdfArray) {
            Vector<PdfObject> v = ((PdfArray) itemObj).getContent ();
            double[] x = new double[v.size()];
            for (int i = 0; i < v.size (); i++) {
                PdfSimpleObject xobj = (PdfSimpleObject) v.elementAt (i);
                x[i] = xobj.getDoubleValue();
            }
            plist.add (new Property ("X", PropertyType.DOUBLE,
                    PropertyArity.ARRAY, x));
        }
        itemObj = meas.get ("Y");
        if (itemObj instanceof PdfArray) {
            Vector<PdfObject> v = ((PdfArray) itemObj).getContent ();
            double[] x = new double[v.size()];
            for (int i = 0; i < v.size (); i++) {
                PdfSimpleObject xobj = (PdfSimpleObject) v.elementAt (i);
                x[i] = xobj.getDoubleValue();
            }
            plist.add (new Property ("Y", PropertyType.DOUBLE,
                    PropertyArity.ARRAY, x));
        }
        itemObj = meas.get ("D");
        if (itemObj instanceof PdfArray) {
            Vector<PdfObject> v = ((PdfArray) itemObj).getContent ();
            double[] x = new double[v.size()];
            for (int i = 0; i < v.size (); i++) {
                PdfSimpleObject xobj = (PdfSimpleObject) v.elementAt (i);
                x[i] = xobj.getDoubleValue();
            }
            plist.add (new Property ("Distance", PropertyType.DOUBLE,
                    PropertyArity.ARRAY, x));
        }
        itemObj = meas.get ("A");
        if (itemObj instanceof PdfArray) {
            Vector<PdfObject> v = ((PdfArray) itemObj).getContent ();
            double[] x = new double[v.size()];
            for (int i = 0; i < v.size (); i++) {
                PdfSimpleObject xobj = (PdfSimpleObject) v.elementAt (i);
                x[i] = xobj.getDoubleValue();
            }
            plist.add (new Property ("Area", PropertyType.DOUBLE,
                    PropertyArity.ARRAY, x));
        }
        return new Property ("Measure",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            plist);
    }

    /* Build a subproperty of a subproperty for an annotation. */
    protected Property buildAnnotProperty (PdfDictionary annot, RepInfo info)
	throws PdfException
    {
        List<Property> propList = new ArrayList<Property> (7);
        PdfObject itemObj;
        try {
            // Subtype is required
            itemObj = (PdfSimpleObject) annot.get ("Subtype");
            propList.add (new Property ("Subtype",
                        PropertyType.STRING,
                        ((PdfSimpleObject)itemObj).getStringValue ()));

            // Contents is optional for some subtypes, required for
            // others.  We consider it optional here.
            itemObj = (PdfSimpleObject) annot.get ("Contents");
            if (itemObj != null) {
                propList.add (new Property ("Contents", PropertyType.STRING,
					    _encrypted ? ENCRYPTED :
			    ((PdfSimpleObject)itemObj).getStringValue ()));
            }
            
            // Rectangle is required, and must be in the rectangle format
            itemObj = annot.get ("Rect");
            propList.add (makeRectProperty 
                    ((PdfArray) resolveIndirectObject (itemObj),
                    "Rect"));
                    
            // Name comes from the NM entry and is optional
            itemObj = annot.get ("NM");
            if (itemObj != null) {
                propList.add (new Property ("Name",
                        PropertyType.STRING,
                        ((PdfSimpleObject)itemObj).getStringValue ()));
            }

            // LastModified is optional.  The documentation says that
            // a PDF date is preferred but not guaranteed.  We just
            // put it out as a string.
            itemObj = annot.get ("M");
            if (itemObj != null) {
                Literal lastModLit = 
                    (Literal) ((PdfSimpleObject) itemObj).getToken ();
                Property dateProp;
                dateProp = new Property ("LastModified",
                            PropertyType.STRING,
                            lastModLit.getValue ());

                propList.add (dateProp);
            }
            
            // Flags.
            itemObj = annot.get ("F");
            if (itemObj != null) {
                int flagValue = ((PdfSimpleObject) itemObj).getIntValue ();
                Property flagProp = (buildBitmaskProperty (flagValue,
                            "Flags",
                            PdfStrings.ANNOTATIONFLAGS,
                            "No flags set"));
                if (flagProp != null) {
                    propList.add (flagProp);
                }
            }
            
            // Appearance dictionary -- just check if it's there.
            itemObj = annot.get ("AP");
            if (itemObj != null) {
                propList.add (new Property ("AppearanceDictionary",
                        PropertyType.BOOLEAN,
                        Boolean.TRUE));
            }
            
            // Action dictionary -- if it's there, set actionsExist
            itemObj = annot.get ("A");
            if (itemObj != null) {
                _actionsExist = true;
                itemObj = resolveIndirectObject (itemObj);
                // Actions are as common as Destinations for
                // connecting to destination pages.  If the Action
                // is of type GoTo, note its destination.
                PdfSimpleObject annType = (PdfSimpleObject)
                         ((PdfDictionary) itemObj).get ("S");
                if (annType == null) {
                    throw new PdfMalformedException ("Annotation dictionary " +
				     "missing required type (S) entry");
                }
                if ("GoTo".equals (annType.getStringValue ())) {
                    PdfObject destObj = 
                        ((PdfDictionary) itemObj).get ("D");
                    if (destObj != null) {
                        addDestination (destObj, "ActionDest", propList,
					info);
                    }
                }
            }

            // Destination object.
            itemObj = annot.get ("Dest");
            if (itemObj != null) {
                addDestination (itemObj, "Destination", propList, info);
            }
            
            // Reply Type (RT) (1.6)
            itemObj = annot.get ("RT");
            if (itemObj instanceof PdfSimpleObject) {
                String type = ((PdfSimpleObject) itemObj).getStringValue();
                propList.add (new Property ("ReplyType",
                        PropertyType.STRING,
                        type));
            }

            // Intent (IT) (1.6)
            itemObj = annot.get ("IT");
            if (itemObj instanceof PdfSimpleObject) {
                String type = ((PdfSimpleObject) itemObj).getStringValue();
                propList.add (new Property ("Intent",
                        PropertyType.STRING,
                        type));
            }

            // Callout Line (CL) (1.6)
            itemObj = annot.get ("CL");
            if (itemObj instanceof PdfArray) {
                Vector<PdfObject> clData = ((PdfArray) itemObj).getContent();
                // This should be an array of numbers.
                Iterator<PdfObject> iter = clData.iterator ();
                List<Double> clList = new ArrayList<Double> (6);
                while (iter.hasNext ()) {
                    PdfSimpleObject clItem = (PdfSimpleObject) iter.next ();
                    clList.add (new Double (clItem.getDoubleValue()));
                }
                propList.add (new Property ("CalloutLine",
                        PropertyType.DOUBLE,
                        PropertyArity.LIST,
                        clList));
            }

	    return new Property ("Annotation", PropertyType.PROPERTY,
				 PropertyArity.LIST, propList);
        }
        catch (PdfMalformedException ee) {
            // Just rethrow these
	    throw ee;
        }
        catch (Exception e) {
            throw new PdfMalformedException ("Invalid Annotation property");
        }
    }

    /* Given a PdfObject that stands for a Destination, add
     * a representative property to the property list.
     */
    protected void addDestination (PdfObject itemObj, String propName,
				 List<Property> propList, RepInfo info)
	throws PdfException
    {
	try {
	    Destination dest = new Destination (itemObj, this, false);
	    if (dest.isIndirect()) {
		// Encryption messes up name trees
		if (!_encrypted) {
		    int pageObjNum = resolveIndirectDest
			(dest.getIndirectDest ());
		    if (pageObjNum == -1) {
			// The scope of the reference is outside this
			// file, so we just report it as such.
			propList.add (new Property (propName,
						    PropertyType.STRING,
						    "External"));
		    }
		    else {
			propList.add (new Property (propName,
						    PropertyType.INTEGER,
						    new Integer (pageObjNum)));
		    }
		}
	    }
	    else {
		int pageObjNum = dest.getPageDestObjNumber ();
		Integer destPg = (Integer) 
		    _pageSeqMap.get (new Integer (pageObjNum));
		if (destPg != null) {
		    propList.add (new Property (propName,
						PropertyType.INTEGER,
						destPg));
		}
	    }
	}
	catch (Exception e) {
	    propList.add (new Property (propName, PropertyType.STRING,
					"null"));
            info.setMessage (new ErrorMessage (e.getMessage (),
					       _parser.getOffset ()));
	    info.setValid (false);
	}
    }

    /*  Build up a property for one of the kinds of fonts
     *  in the file.
    */
    protected Property buildFontProperty (String name, Map map, int fontType)
    {
        List<Property> fontList = new LinkedList<Property> ();  // list of fonts
        Iterator<PdfObject> fontIter = map.values ().iterator ();
        while (fontIter.hasNext ()) {
            // For each font in the map, build a property for it,
            // which consists of a list of scalar properties.  Each kind
            // of font is spec'ed to have a slightly different set of
            // properties, grumble...
            PdfDictionary dict = (PdfDictionary) fontIter.next ();
            List<Property> fontPropList = oneFontPropList (dict, fontType);
            Property fProp = new Property ("Font",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            fontPropList);
            fontList.add (fProp);
        }
        return new Property (name,
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        fontList);
    }
    
    /* Build the Property list for a given font */
    protected List<Property> oneFontPropList (PdfDictionary dict, int fontType) 
    {
        List<Property> fontPropList = new LinkedList<Property> ();
        Property prop;
        if (fontType == F_TYPE1 || fontType == F_TYPE3 || fontType == F_MM1 ||
	    fontType == F_TT) {
	    PdfObject tempObj = dict.get ("Name");
	    PdfSimpleObject nameObj = null;
	    if (tempObj instanceof PdfSimpleObject) {
		nameObj = (PdfSimpleObject) tempObj;
	    }
	    else if (tempObj instanceof PdfIndirectObj) {
		nameObj = (PdfSimpleObject)
		    ((PdfIndirectObj) tempObj).getObject ();
	    }

            if (nameObj != null) {
                String nameStr = nameObj.getStringValue ();
                prop = new Property ("Name", PropertyType.STRING, nameStr);
                fontPropList.add (prop);
            }
        }

        String baseStr = null;
        if (fontType != F_TYPE3) {
	    PdfObject tempObj = dict.get ("BaseFont");
            PdfSimpleObject baseFontObj = null;
	    if (tempObj instanceof PdfSimpleObject) {
		baseFontObj = (PdfSimpleObject) tempObj;
	    }
	    else if (tempObj instanceof PdfIndirectObj) {
		baseFontObj = (PdfSimpleObject)
		    ((PdfIndirectObj) tempObj).getObject ();
	    }

            if (baseFontObj != null) {
                baseStr = baseFontObj.getStringValue ();
                prop = new Property ("BaseFont", PropertyType.STRING,
				     baseStr);
                fontPropList.add (prop);
            }
        }
        
        if (fontType == F_CID0 || fontType == F_CID2) {
            PdfObject elCid = dict.get ("CIDSystemInfo");
            try {
                elCid = resolveIndirectObject (elCid);
            }
            catch (Exception e) {}
            if (elCid instanceof PdfDictionary) {
                prop = buildCIDInfoProperty ((PdfDictionary) elCid);
                fontPropList.add (prop);
            }
        }
        
        if (fontType == F_TYPE1 || fontType == F_TT || fontType == F_MM1) {
            if (isFontSubset (baseStr)) {
                prop = new Property ("FontSubset", PropertyType.BOOLEAN,
				     Boolean.TRUE);
                fontPropList.add (prop);
            }
        }

        if (fontType == F_TYPE1 || fontType == F_TT || fontType == F_MM1 ||
	    fontType == F_TYPE3) {
            PdfObject firstCharObj = dict.get("FirstChar");
	    if (firstCharObj instanceof PdfIndirectObj) {
		firstCharObj = ((PdfIndirectObj) firstCharObj).getObject ();
	    }
            try {
                int firstChar = ((PdfSimpleObject) firstCharObj).getIntValue();
                prop = new Property ("FirstChar", PropertyType.INTEGER,
				     new Integer (firstChar));
                fontPropList.add (prop);
            }
            catch (Exception e) {}

            PdfObject lastCharObj = dict.get("LastChar");
	    if (lastCharObj instanceof PdfIndirectObj) {
		lastCharObj = ((PdfIndirectObj) lastCharObj).getObject ();
	    }
            try {
                int lastChar = ((PdfSimpleObject) lastCharObj).getIntValue ();
                prop = new Property ("LastChar", PropertyType.INTEGER,
				     new Integer (lastChar));
                fontPropList.add (prop);
            }
            catch (Exception e) {}
        }
        
        if (fontType == F_TYPE3) {
            // Put FontBBox and CharProcs into properties
            PdfObject bboxObj = dict.get("FontBBox");
            try {
                if (bboxObj instanceof PdfArray) {
                    fontPropList.add (makeRectProperty ((PdfArray) bboxObj,
							"FontBBox"));
                }
            }
            catch (Exception e) {}
            
            // For CharProcs, we're just checking if it's there.
            // (It's required for a Type 3 font.)
//            PdfObject charProcs = dict.get ("CharProcs");
//            prop = new Property ("CharProcs",
//                        PropertyType.BOOLEAN,
//                        new Boolean (charProcs != null));
//            fontPropList.add (prop);
        }
        
        if (fontType == F_TYPE1 || fontType == F_TT || fontType == F_MM1 ||
	    fontType == F_CID0  || fontType == F_CID2) {
            PdfObject descriptorObj = dict.get ("FontDescriptor");
            try {
                descriptorObj = resolveIndirectObject (descriptorObj);
            }
            catch (Exception e) {}
            if (descriptorObj instanceof PdfDictionary) {
		prop = buildFontDescriptorProperty ((PdfDictionary)
						    descriptorObj);
		fontPropList.add (prop);
            }
        }

       PdfObject encodingObj = dict.get ("Encoding");
       try {
	   encodingObj = resolveIndirectObject (encodingObj);
       }
       catch (Exception e) {}

       if (fontType == F_TYPE0 || fontType == F_TYPE1 || fontType == F_TT ||
	   fontType == F_MM1   || fontType == F_TYPE3) {
            // Encoding property -- but only if Encoding is a name
            if (encodingObj instanceof PdfSimpleObject) {
                prop = new Property ("Encoding", PropertyType.STRING,
				     ((PdfSimpleObject) encodingObj).getStringValue ());
                fontPropList.add (prop);
            }
        }

        if (fontType == F_TYPE1 || fontType == F_TT || fontType == F_MM1 ||
	    fontType == F_TYPE3) {
            if (encodingObj != null && encodingObj instanceof PdfDictionary) {
                prop = buildEncodingDictProperty ((PdfDictionary) encodingObj);
                fontPropList.add (prop);
            }
        }

        if (fontType == F_TYPE0) {
            // Encoding is reported as a CMapDictionary property for type 0
            if (encodingObj != null && encodingObj instanceof PdfStream) {
                prop = buildCMapDictProperty ((PdfStream) encodingObj);
                fontPropList.add (prop);
            }
        }

        if (fontType == F_TYPE3) {
            // All we're interested in for Resources is whether
            // the dictionary exists
            PdfObject rsrc = dict.get ("Resources");
            if (rsrc != null) {
                prop = new Property ("Resources", PropertyType.BOOLEAN,
				     Boolean.TRUE);
                fontPropList.add (prop);
            }
        }

        if (fontType == F_TYPE0 || fontType == F_TYPE1 || fontType == F_TT ||
	    fontType == F_MM1   || fontType == F_TYPE3) {
            PdfObject toUniObj = dict.get ("ToUnicode");
            if (toUniObj != null) {
                prop = new Property ("ToUnicode", PropertyType.BOOLEAN,
				     Boolean.TRUE);
                fontPropList.add (prop);
            }
        }

        return fontPropList;
    }

    /* Code for CMapProperty for Type 0 fonts, based on the Encoding
     * entry, broken out of buildFontProperty.
     */
    protected Property buildCMapDictProperty (PdfStream encoding)
    {
        PdfDictionary dict = encoding.getDict ();
        List<Property> propList = new ArrayList<Property> (4);
        Property prop = new Property ("CMapDictionary",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        propList);
        Property subprop;
        
        //PdfObject mapName = dict.get  ("CMapName");
        
        PdfObject cidSysInfo = dict.get  ("CIDSystemInfo");
        // We can use buildCIDInfoProperty here to build the subproperty
        PdfDictionary cidDict;
        List<Property> cidList = new LinkedList<Property> ();
        try {
            if (cidSysInfo instanceof PdfDictionary) {
                // One CIDInfo dictionary
                cidDict = (PdfDictionary) cidSysInfo;
                subprop = buildCIDInfoProperty (cidDict);
                cidList.add (subprop);
            }
            else if (cidSysInfo instanceof PdfArray) {
                // Many CIDInfo dictionaries
                Vector<PdfObject> v = ((PdfArray) cidSysInfo).getContent ();
                for (int i = 0; i < v.size (); i++) {
                    cidDict = (PdfDictionary) v.elementAt (i);
                    Property subsubprop = buildCIDInfoProperty (cidDict);
                    cidList.add (subsubprop);
                }
            }
        }
        catch (Exception e) {}

        if (!cidList.isEmpty ()) {
            subprop = new Property ("CIDSystemInfos",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        cidList);
            propList.add (subprop);
        }

        //PdfObject wMod = dict.get ("WMode");
        //PdfObject useCMap = dict.get ("UseCMap");

        return prop;
    }

    /* Code for CIDInfoProperty for CIDFontType0 and CIDFontType2
     * conts.
     */
    protected Property buildCIDInfoProperty (PdfDictionary dict)
    {
        List<Property> propList = new ArrayList<Property> (3);
        Property prop = new Property ("CIDSystemInfo",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList);
        Property subprop;
                        
        // Add the registry identifier
        PdfObject reg = dict.get ("Registry");
        if (reg instanceof PdfSimpleObject) {
            try {
            String regText = ((PdfSimpleObject) reg).getStringValue ();
            subprop = new Property ("Registry", PropertyType.STRING,
				    _encrypted ? ENCRYPTED : regText);
            propList.add (subprop);
            }
            catch (Exception e) {}
        }

        // Add the name of the char collection within the registry
        PdfObject order = dict.get ("Ordering");
        if (reg instanceof PdfSimpleObject) {
            try {
            String ordText = 
                ((PdfSimpleObject) order).getStringValue ();
            subprop = new Property ("Registry",
                PropertyType.STRING,
                ordText);
            propList.add (subprop);
            }
            catch (Exception e) {}
        }

        PdfObject supp = dict.get ("Supplement");
        if (supp instanceof PdfSimpleObject) {
            try {
            int suppvalue = ((PdfSimpleObject) supp).getIntValue ();
            subprop = new Property ("Supplement",
                PropertyType.INTEGER,
                new Integer (suppvalue));
            propList.add (subprop);
            }
            catch (Exception e) {}
        }
        return prop;
    }

    /* Code for EncodingDictionary Property for type 1, 3, TrueType, and
     * MM fonts.  This is based on a dictionary entry with the same name
     * as the one for buildCMapDictProperty, but different information.
     * Included properties are BaseEncoding and Differences.
     */
    protected Property buildEncodingDictProperty (PdfDictionary encodingDict)
    {
        List<Property> propList = new ArrayList<Property> (2);
        Property prop = new Property ("EncodingDictionary",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList);
        PdfObject baseEnc = encodingDict.get ("BaseEncoding");
        if (baseEnc instanceof PdfSimpleObject) {
            String baseEncString = ((PdfSimpleObject) baseEnc).getStringValue ();
            if (baseEncString != null) {
                Property baseEncProp = new Property ("BaseEncoding",
                                    PropertyType.STRING,
                                    baseEncString);
                propList.add (baseEncProp);
            }
        }
        
        PdfObject diffs = encodingDict.get ("Differences");
        Property diffsProp = new Property ("Differences",
                        PropertyType.BOOLEAN,
                        new Boolean (diffs != null));
        propList.add (diffsProp);

        return prop;
    }
    
    /* Separated-out code for FontDescriptor property.  This
     * is a list of six Properies: FontName, Flags,
     * FontBBox, FontFile, FontFile2, and FontFile3.
     */
    protected Property buildFontDescriptorProperty 
                        (PdfDictionary encodingDict)
    {
        List<Property> propList = new ArrayList<Property> (6);
        Property prop = new Property ("FontDescriptor",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList);
        Property subprop;
        try {
            PdfSimpleObject fName = 
                (PdfSimpleObject) encodingDict.get ("FontName");
            String fNameStr = fName.getStringValue ();
            subprop = new Property ("FontName",
                    PropertyType.STRING,
                    fNameStr);
            propList.add (subprop);
        }
        catch (Exception e) {}

        try {
            PdfSimpleObject flags = 
                (PdfSimpleObject) encodingDict.get ("Flags");
            int flagValue = flags.getIntValue ();
            subprop = buildBitmaskProperty (flagValue,
                    "Flags",
                    PdfStrings.FONTDESCFLAGS,
                    "No flags set");
            if (subprop != null) {
                propList.add (subprop);
            }
        }
        catch (Exception e) {}

        try {
            PdfArray bboxObj = 
                (PdfArray) encodingDict.get ("FontBBox");
            double[] bbox = bboxObj.toRectangle ();
            // toRectangle is written to return an array of double,
            // which is what the bounding box is in the most general
            // case; but the spec requires an array of integer, so
            // we convert is.  This may seem like an excess of work,
            // but I'd rather have toRectangle do the right thing
            // rather than losing generality.
            if (bbox != null) {
                int [] ibbox = new int[4];
                for (int i = 0; i < 4; i++) {
                    ibbox[i] = (int) bbox[i];
                }
                subprop = new Property ("FontBBox",
                        PropertyType.INTEGER,
                        PropertyArity.ARRAY,
                        ibbox);
                propList.add (subprop);
            }
        }
        catch (Exception e) {}

        PdfObject fontFile = encodingDict.get ("FontFile");
        if (fontFile != null) {
            // All we care about is whether it exists or not
            subprop = new Property ("FontFile", PropertyType.BOOLEAN,
				    Boolean.TRUE);
            propList.add (subprop);
        }
	fontFile = encodingDict.get ("FontFile2");
        if (fontFile != null) {
            subprop = new Property ("FontFile2", PropertyType.BOOLEAN,
				    Boolean.TRUE);
            propList.add (subprop);
        }
	fontFile = encodingDict.get ("FontFile3");
        if (fontFile != null) {
            subprop = new Property ("FontFile3", PropertyType.BOOLEAN,
				    Boolean.TRUE);
            propList.add (subprop);
        }
        return prop;
    }

    protected Property buildViewPrefProperty (PdfDictionary prefDict) 
    {
        Property p;
        PdfObject ob;
        boolean b;
        String s;
        List<Property> propList = new ArrayList<Property> (12);
        Property prop = new Property ("ViewerPreferences",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            propList);
        
        ob = prefDict.get("HideToolbar");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("HideToolbar", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("HideMenubar");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("HideMenubar", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("HideWindowUI");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("HideWindowUI", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("FitWindow");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("FitWindow", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("CenterWindow");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("CenterWindow", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("DisplayDocTitle");
        if (ob instanceof PdfSimpleObject) {
            b = ((PdfSimpleObject) ob).isTrue ();
        }
        else {
            b = false;
        }
        p = new Property ("DisplayDocTitle", PropertyType.BOOLEAN, new Boolean (b));
        propList.add (p);

        ob = prefDict.get("NonFullScreenPageMode");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "UseNone";
        p = new Property ("NonFullScreenPageMode", PropertyType.STRING, s);
        propList.add (p);

        ob = prefDict.get("Direction");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "L2R";
        p = new Property ("Direction", PropertyType.STRING, s);
        propList.add (p);

        ob = prefDict.get("ViewArea");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "CropBox";
        p = new Property ("ViewArea", PropertyType.STRING, s);
        propList.add (p);

        ob = prefDict.get("ViewClip");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "CropBox";
        p = new Property ("ViewClip", PropertyType.STRING, s);
        propList.add (p);

        ob = prefDict.get("PrintArea");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "CropBox";
        p = new Property ("PrintArea", PropertyType.STRING, s);
        propList.add (p);

        ob = prefDict.get("PageClip");
        if (ob instanceof PdfSimpleObject) {
            s = ((PdfSimpleObject) ob).getStringValue ();
        }
        else s = "CropBox";
        p = new Property ("PageClip", PropertyType.STRING, s);
        propList.add (p);
        return prop;
    }

    /* Return TRUE if the string is a font subset string, which begins
       with six uppercase letters and then a plus sign */
    protected boolean isFontSubset (String baseStr)
    {
        if (baseStr == null || baseStr.length () < 7) {
            return false;
        }
        for (int i = 0; i < 6; i++) {
            char ch = baseStr.charAt (i);
            if (!Character.isUpperCase (ch)) {
                return false;
            }
        }
        return (baseStr.charAt (6) == '+');
    }
    
    
    /* Create the "Outlines" property from the Outlines item in the
       catalog dictionary.  As a side effect, we set the actionsExist
       flag if any Actions are found. Because we check destinations,
       this can't be called till the page tree is built. 
       
       Outlines can be recursive, according to Adobe people, so we have
       to track visited nodes.
    */
    protected Property buildOutlinesProperty (PdfDictionary dict, RepInfo info)
            throws PdfException
    {
        _recursionWarned = false;
        _visitedOutlineNodes = new HashSet<Integer> ();
        String malformed = "Malformed outline dictionary";
        List<Property> itemList = new LinkedList<Property> ();
        Property prop = new Property ("Outlines",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                itemList);
        try {
            PdfObject item = resolveIndirectObject (dict.get ("First"));
            // In PDF 1.4, "First" and "Last" are unconditionally required. However,
            // in 1.6, they can be omitted if there are no open or closed outline items.
            // Strictly speaking, we should do several additional checks, but letting the
            // outline go as empty seems sufficient.
//            if (item == null || !(item instanceof PdfDictionary)) {
//                throw new PdfInvalidException ("Outline dictionary missing required entry");
//            }
            int listCount = 0;          // Guard against looping
            while (item != null) {
                Integer onum = new Integer (item.getObjNumber ());
                Property p = buildOutlineItemProperty ((PdfDictionary) item, info);
                itemList.add (p);
                item = resolveIndirectObject (((PdfDictionary) item).get ("Next"));
                if (item == null) {
                    break;
                }
                // Check if this object is its own sibling. (It really does happen!)
                if (item.getObjNumber() == onum.intValue ()) {
                    if (!_recursionWarned) {
                        info.setMessage (new InfoMessage
                                (outlinesRecursiveString));
                        _recursionWarned = true;
                    }
                    break;
                }
                if (++listCount > 2000) {
                    break;
                }
            }
        }
        catch (PdfException e1) {
            throw e1;
        }
        catch (Exception e) {
            throw new PdfMalformedException (malformed);
        }
        if (itemList.isEmpty ()) {
            return null;
        }
        return prop;
    }
    
    
    
    
    /* Create an item property within the outlines hierarchy. If an
       Outline item property has children, then there is a list
       property called "Children" with elements called "Item".
       It calls itself recursively to walk down the outline. */
    protected Property buildOutlineItemProperty (PdfDictionary dict, RepInfo info)
	            throws PdfException
    {
        String invalid = "Invalid outline dictionary item";
        List<Property> itemList = new ArrayList<Property> (3);
        try {
            Property prop = new Property ("Item",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    itemList);
            PdfSimpleObject title = (PdfSimpleObject) 
                    resolveIndirectObject (dict.get ("Title"));
            if (title == null) {
                throw new PdfInvalidException (invalid);
            }
            itemList.add (new Property ("Title", PropertyType.STRING,
					_encrypted ? ENCRYPTED :
					title.getStringValue ()));

            // Check other required stuff
            if (dict.get ("Parent") == null) {
                throw new PdfInvalidException (invalid);
            }
            PdfObject cnt = dict.get ("Count");
            if (cnt != null &&
                (!(cnt instanceof PdfSimpleObject) ||
                 !(((PdfSimpleObject) cnt).getToken () instanceof Numeric))) {
                throw new PdfInvalidException (invalid);
            }
            // The entries for Prev, Next, First, and Last must
            // all be indirect references or absent.  Just cast them to
            // throw an exception if they're something else
            PdfIndirectObj ob = (PdfIndirectObj) dict.get ("Prev");
            ob = (PdfIndirectObj) dict.get ("Next");
            ob = (PdfIndirectObj) dict.get ("First");
            ob = (PdfIndirectObj) dict.get ("First");
            
            // Check if there are Actions in the outline.  This saves going
            // through the outlines all over again if a Profile checker
            // needs to know this.  We flag only the existence of one or more Actions
            // in the document.
            if (dict.get ("A") != null) {
                _actionsExist = true;
            }
            
            PdfObject destObj = dict.get ("Dest");
            if (destObj != null) {
                destObj = resolveIndirectObject(destObj);
                Destination dest = new Destination (destObj, this, false);
                if (dest.isIndirect()) {
                    itemList.add (new Property ("Destination",
                        PropertyType.STRING,
                        dest.getIndirectDest ()));
                }
                else {
                    int pageObjNum = dest.getPageDestObjNumber ();
                    Integer destPg = (Integer) 
                        _pageSeqMap.get (new Integer (pageObjNum));
                    if (destPg != null) {
                        itemList.add (new Property ("Destination",
                            PropertyType.INTEGER,
                            destPg));
                    }
                }
            }

            PdfDictionary child = 
                    (PdfDictionary) resolveIndirectObject (dict.get ("First"));
            if (child != null) {
                List<Property> childList = new LinkedList<Property> ();
                Property childProp = new Property ("Children",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        childList);
                // We aren't catching all possible combinations of looping. Put a maximum
                // on the list just to be safe.
                int listCount = 0;
                while (child != null) {
                    Integer onum = new Integer (child.getObjNumber ());
                    if (_visitedOutlineNodes.contains (onum)) {
                        /* We have recursion! */
                        if (!_recursionWarned) {
                            // Warn of recursion
                            info.setMessage (new InfoMessage
                                    (outlinesRecursiveString));
                            _recursionWarned = true;
                        }
                    }
                    else {
                        _visitedOutlineNodes.add (onum);
                        Property p = buildOutlineItemProperty ((PdfDictionary) child, info);
                        childList.add (p);
                    }
                    child = (PdfDictionary) 
                          resolveIndirectObject (child.get ("Next"));
                    if (child == null) {
                        break;
                    }
                    // Check if this object is its own sibling. (It really does happen!)
                    if (child.getObjNumber() == onum.intValue ()) {
                        if (!_recursionWarned) {
                            info.setMessage (new InfoMessage
                                    (outlinesRecursiveString));
                            _recursionWarned = true;
                        }
                        break;
                    }
                    if (++listCount > 2000)
                        break;          // safety check
                }
                itemList.add (childProp);
            }
            return prop;
        }
        catch (PdfException pe) {
            throw pe;
        }
        catch (ClassCastException ce) {
            throw new PdfInvalidException (invalid);
        }
        catch (Exception e) {
            throw new PdfInvalidException (invalid);
        }
    }

    /* This is separated out from readDocCatalogDict, where it
       would otherwise make sense, because we can't build
       the outlines property till we have a page tree to
       locate destinations. */
    protected boolean doOutlineStuff (RepInfo info)
    {
        if (_outlineDict != null) {
            try {
                Property oprop = buildOutlinesProperty 
                        ((PdfDictionary) _outlineDict, info);
                if (_showOutlines || _verbosity == Module.MAXIMUM_VERBOSITY) {
                    if (oprop != null){
                        _docCatalogList.add (oprop);
                    }
                }
                else if (!_skippedOutlinesReported) {
                    // We report that we aren't reporting skipped outlines
                    info.setMessage (new InfoMessage
                                (outlinesSkippedString));
                    _skippedOutlinesReported = true;
                }
            }
            catch (PdfException e) {
                info.setMessage (new ErrorMessage (e.getMessage(),
                        _parser.getOffset ()));
                e.disparage (info);
                // If it's just invalid, we can keep going
                return (e instanceof PdfInvalidException); 
            }
        }
        return true;
    }

    /* Given a PdfSimpleObject representing a key, 
       look up the Destination which it references.
       There are two completely different ways this can be done,
       though any given PDF file is supposed to implement only one.
       If _destsDict is non-null, we look the string up there, and
       may find either a dictionary or an array.  Otherwise
       if _destNames is non-null, it's a NameTreeNode which contains
       the mapping.  In either case, the destination could be
       external, in which case we just return a string saying so.
       (The implementation of Destinations in PDF is a prime example
       of design by stone soup.)
       We return the page sequence number for the referenced page.
       If we can't find a match for the reference, we return -1.
    */
    protected int resolveIndirectDest (PdfSimpleObject key)
                        throws PdfException
    {
          if (_destNames != null) {
              Destination dest = new Destination (_destNames.get (key.getRawBytes ()),
                                  this, true);
//              if (dest == null) {
//                  return -1;
//              }
              return dest.getPageDestObjNumber ();
          }
          else {
              return -1;   // This is probably an error, actually
          }
    }


    /* Build the user permission property., */
    protected Property buildUserPermProperty (int flags, String[] flagStrs)
    {
        return buildBitmaskProperty (flags, "UserAccess", flagStrs,
				     "No permissions");
    }
    
    /** Add a string proprerty, based on a dictionary entry
        with a string value, to a specified List. */
    protected void addStringProperty(PdfDictionary dict,
                        List<Property> propList,
                        String key,
                        String propName)
    {
        String propText = null;
        PdfObject propObject = dict.get (key);
        if (propObject instanceof PdfSimpleObject) {
            Token tok = ((PdfSimpleObject)propObject).getToken ();
            if (tok instanceof Literal) {
                if (_encrypted) {
                    propText = ENCRYPTED;
                }
                else {
                    propText = ((Literal) tok).getValue ();
                }
                propList.add (new Property (propName,
                            PropertyType.STRING,
                            propText));
            }
        }
    }

    /** Add a date proprerty, based on a dictionary entry
        with a string value, to a specified List. */
    protected void addDateProperty(PdfDictionary dict,
                        List<Property> propList,
                        String key,
                        String propName)
                        throws PdfException
    {
        if (_encrypted) {
            return;   // can't decipher an encrypted date
        }
        PdfObject propObject = dict.get (key);
        if (propObject instanceof PdfSimpleObject) {
            Token tok = ((PdfSimpleObject)propObject).getToken ();
            if (tok instanceof Literal) {
                Date propDate = ((Literal) tok).parseDate ();
                if (propDate != null) {
                    propList.add (new Property (propName,
                                PropertyType.DATE,
                                propDate));
                }
                else {
                    throw new PdfInvalidException ("Improperly formed date", 
                                0);
                }
            }
        }
    }

    /* General function for adding a property with a 32-bit
       value, with an array of Strings to interpret
       the value as a bitmask. */
    protected Property buildBitmaskProperty (int val, String name,
                                       String [] valueNames,
                                       String defaultStr)
    {
        if (_je != null && _je.getShowRawFlag ()) {
            return new Property (name,
                        PropertyType.INTEGER,
                        new Integer (val));
        }
        else {
           List<String> slist = new LinkedList<String> ();
           try {
               for (int i = 0; i < valueNames.length; i++) {
                   if ((val & (1 << i)) != 0 && 
                           valueNames[i].length () > 0) {
                       slist.add (valueNames[i]);
                   }
               }
               // Provision for a default string if the property
               // would otherwise have an empty list
               if (slist.isEmpty() && defaultStr != null) {
                   slist.add (defaultStr);
               }
           }
           catch (Exception e) {
               return null;
           }
           return new Property (name, PropertyType.STRING,
                                             PropertyArity.LIST, slist);
        }
    }

    /* Take a PdfArray which is supposed to conform to the rectangle
       description (i.e., it's an array of 4 numbers) and create 
       a Property which is an array of 4 integers. */
    protected Property makeRectProperty (PdfArray arrObj, String name)
                throws PdfException
    {
        int [] iarr = new int[4];
        double[] arr = ((PdfArray) arrObj).toRectangle ();
        // toRectangle is written to return an array of double,
        // which is what the bounding box is in the most general
        // case; but the spec requires an array of integer, so
        // we convert is.  This may seem like an excess of work,
        // but I'd rather have toRectangle do the right thing
        // rather than losing generality.
        for (int i = 0; i < 4; i++) {
            iarr[i] = (int) arr[i];
        }
        return new Property (name,
                PropertyType.INTEGER,
                PropertyArity.ARRAY,
                iarr);
    }
}
