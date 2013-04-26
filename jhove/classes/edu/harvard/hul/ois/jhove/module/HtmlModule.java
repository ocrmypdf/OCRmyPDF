/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2007 by JSTOR and the President and Fellows of Harvard College
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

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.html.*;

/**
 *  Module for identification and validation of HTML files.
 * 
 *  HTML is different from most of the other documents in that
 *  sloppy construction is practically assumed in the specification.
 *  This module attempt to report as many errors as possible and
 *  recover reasonably from errors. To do this, there is more
 *  heuristic behavior built into this module than into the more
 *  straightforward ones.
 * 
 *  XHTML is recognized by this module, but is handed off to the
 *  XML module for processing.  If the XML module is missing (which
 *  it shouldn't be if you've installed the JHOVE application without
 *  modifications), this won't be able to deal with XHTML files.
 * 
 *  HTML should be placed ahead of XML in the module order.  If the
 *  XML module sees an XHTML file first, it will recognize it as XHTML,
 *  but won't be able to report the complete properties.
 * 
 *  The HTML module uses code created with the JavaCC parser generator
 *  and lexical analyzer generator.  There is apparently a bug in
 *  JavaCC which causes blank lines not to be counted in certain cases,
 *  causing lexical errors to be reported with incorrect line numbers.
 *
 * @author Gary McGath
 *
 */
public class HtmlModule extends ModuleBase {

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "HTML-hul";
    private static final String RELEASE = "1.3";
    private static final int [] DATE = {2006, 9, 5};
    private static final String [] FORMAT = {
        "HTML"
    };
    private static final String COVERAGE = "HTML 3.2, HTML 4.0 Strict," +
        "HTML 4.0 Transitional, HTML 4.0 Frameset, " +
        "HTML 4.01 Strict, HTML 4.01 Transitional, HTML 4.01 Frameset" +
        "XHTML 1.0 Strict, XHTML 1.0 Transitional, XHTML 1.0 Frameset" +
        "XHTML 1.1";

    private static final String [] MIMETYPE = {
        "text/html"
    };
    private static final String WELLFORMED = "An HTML file is well-formed " +
	"if it meets the criteria defined in the HTML 3.2 specification " +
	"(W3C Recommendation, 14-Jan-1997), " +
        "the HTML 4.0 specification (W3C Recommendation, 24-Apr-1998, " +
        "the HTML 4.01 specification (W3C Recommendation, 24-Dec-1999, " +
        "the XHTML 1.0 specification (W3C Recommendation, 26-Jan-2000, " +
	"revised 1-Aug-2002, " +
        "or the XHTML 1.1 specification (W3C Recommendation, 31-May-2001";
    private static final String VALIDITY = "An HTML file is valid if it is " +
	"well-formed and has a valid DOCTYPE declaration.";
    private static final String REPINFO = "Languages, title, META tags, " +
	"frames, links, scripts, images, citations, defined terms, " +
	"abbreviations, entities, Unicode entity blocks";
    private static final String NOTE = "";
    private static final String RIGHTS = "Copyright 2004-2007 by JSTOR and " +
	"the President and Fellows of Harvard College. " +
	"Released under the GNU Lesser General Public License.";

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /* Input stream wrapper which handles checksums */
    protected ChecksumInputStream _cstream;
    
    /* Data input stream wrapped around _cstream */
    protected DataInputStream _dstream;
    
    /* Doctype extracted from document */
    protected String _doctype;
    
    /* Constants for the recognized flavors of HTML */
    public static final int
        HTML_3_2 = 1,
        HTML_4_0_STRICT = 2,
        HTML_4_0_FRAMESET = 3,
        HTML_4_0_TRANSITIONAL = 4,
        HTML_4_01_STRICT = 5,
        HTML_4_01_FRAMESET = 6,
        HTML_4_01_TRANSITIONAL = 7,
        XHTML_1_0_STRICT = 8,
        XHTML_1_0_TRANSITIONAL = 9,
        XHTML_1_0_FRAMESET = 10,
        XHTML_1_1 = 11;
        
    /* Profile names, matching the above indices */
    private static final String[] profileNames = 
    {
        null,
        null,           // there are no profiles for HTML 3.2
        "Strict",
        "Frameset",
        "Transitional",
        "Strict",
        "Frameset",
        "Transitional",
        "Strict",
        "Frameset",
        "Transitional",
        null            // there are no profiles for XHTML 1.1
    };
    
    /* Version names, matching the above indices */
    private static final String[] versionNames =
    {
        null,
        "HTML 3.2",
        "HTML 4.0",
        "HTML 4.0",
        "HTML 4.0",
        "HTML 4.01",
        "HTML 4.01",
        "HTML 4.01",
        "XHTML 1.0",
        "XHTML 1.0",
        "XHTML 1.0",
        "XHTML 1.1"
    };
    
    /* Flag to know if the property TextMDMetadata is to be added */
    protected boolean _withTextMD = false;
    /* Hold the information needed to generate a textMD metadata fragment */
    protected TextMDMetadata _textMD;

    /******************************************************************
    * CLASS CONSTRUCTOR.
    ******************************************************************/
    /**
     *  Instantiate an <tt>HtmlModule</tt> object.
     */
    public HtmlModule ()
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

       /* HTML 3.2 spec */
       Document doc = new Document ("HTML 3.2 Reference Specification", 
             DocumentType.REPORT);        

       Agent w3cAgent = new Agent ("Word Wide Web Consortium", AgentType.NONPROFIT);
       w3cAgent.setAddress ("Massachusetts Institute of Technology, " +
             "Computer Science and Artificial Intelligence Laboratory, " +
             "32 Vassar Street, Room 32-G515, " +
             "Cambridge, MA 02139");
       w3cAgent.setTelephone ("(617) 253-2613");
       w3cAgent.setFax ("(617) 258-5999");
       w3cAgent.setWeb ("http://www.w3.org/");
       doc.setPublisher (w3cAgent);

       Agent dRaggett = new Agent ("Dave Raggett", AgentType.OTHER);
       doc.setAuthor(dRaggett);
       
       doc.setDate ("1997-01-14");
       doc.setIdentifier(new Identifier 
           ("http://www.w3c.org/TR/REC-html32-19970114", IdentifierType.URL));
       _specification.add (doc);
       
       /* HTML 4.0 spec */
       doc = new Document ("HTML 4.0 Specification", DocumentType.REPORT);
       doc.setPublisher (w3cAgent);
       doc.setAuthor(dRaggett);
       Agent leHors = new Agent ("Arnaud Le Hors", AgentType.OTHER);
       doc.setAuthor(leHors);
       Agent jacobs = new Agent ("Ian Jacobs", AgentType.OTHER);
       doc.setAuthor(jacobs);
       doc.setDate ("1998-04-24");
       doc.setIdentifier(new Identifier 
           ("http://www.w3.org/TR/1998/REC-html40-19980424/", IdentifierType.URL));
       _specification.add (doc);


       /* HTML 4.01 spec */
       doc = new Document ("HTML 4.01 Specification", DocumentType.REPORT);
       doc.setPublisher (w3cAgent);
       doc.setAuthor(dRaggett);
       doc.setAuthor(leHors);
       doc.setAuthor(jacobs);
       doc.setDate ("1999-12-24");
       doc.setIdentifier(new Identifier 
           ("http://www.w3.org/TR/1999/REC-html401-19991224/", IdentifierType.URL));
       _specification.add (doc);
       
       /* XHTML 1.0 spec */
       doc = new Document ("XHTML(TM) 1.0 The Extensible HyperText Markup Language " +
                  "(Second Edition)", DocumentType.REPORT);
       doc.setPublisher (w3cAgent);
       doc.setDate ("01-08-2002");
       doc.setIdentifier (new Identifier
            ("http://www.w3.org/TR/xhtml1/", IdentifierType.URL));
       _specification.add (doc);
       
       /* XHTML 1.1 spec */
       doc = new Document (" XHTML(TM) 1.1 - Module-based XHTML",
                  DocumentType.REPORT);
       doc.setPublisher (w3cAgent);
       doc.setDate ("31-05-2001");
       doc.setIdentifier (new Identifier
            ("http://www.w3.org/TR/2001/REC-xhtml11-20010531/",
             IdentifierType.URL));
       _specification.add (doc);
       
       /* XHTML 2.0 spec -- NOT included yet; this is presented in "conditionalized-out"
        * form just as a note for future expansion. */
       if (false) {
           doc = new Document ("XHTML 2.0, W3C Working Draft", DocumentType.OTHER);
           doc.setPublisher (w3cAgent);
           doc.setDate ("22-07-2004");
           doc.setIdentifier (new Identifier
              ("http://www.w3.org/TR/2004/WD-xhtml2-20040722/", IdentifierType.URL));
           _specification.add (doc);
       }
       
       Signature sig = new ExternalSignature (".html", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
       sig = new ExternalSignature (".htm", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
    }

    /**
     *   Parse the content of a purported HTML stream digital object and store the
     *   results in RepInfo.
     * 
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
        if (parseIndex != 0) {
            // Coming in with parseIndex = 1 indicates that we've determined
            // this is XHTML; so we invoke the XML module to parse it.
            // If parseIndex is 100, this is the first invocation of the
            // XML module, so we call it with 0; otherwise we call it with
            // the value of parseIndex.
            if (isXmlAvailable ()) {
                edu.harvard.hul.ois.jhove.module.XmlModule xmlMod = 
                    new edu.harvard.hul.ois.jhove.module.XmlModule ();
                if (parseIndex == 100) {
                    parseIndex = 0;
                }
                xmlMod.setApp  (_app);
                xmlMod.setBase (_je);
                xmlMod.setXhtmlDoctype(_doctype);
                return xmlMod.parse (stream, info, parseIndex);
            }
            else {
                // The XML module shouldn't be missing from any installation,
                // but someone who really wanted to could remove it.  In
                // that case, you deserve what you get.
                info.setMessage ( new ErrorMessage
                    ("XML-HUL module required to validate XHTML documents"));
                info.setWellFormed (false);  // Treat it as completely wrong
                return 0;
            }
        }
        else {
            /* parseIndex = 0, first call only */
            _doctype = null;
        }
        // Test if textMD is to be generated
        if (_defaultParams != null) {
            Iterator iter = _defaultParams.iterator ();
            while (iter.hasNext ()) {
                String param = (String) iter.next ();
                if (param.toLowerCase ().equals ("withtextmd=true")) {
                    _withTextMD = true;
                }
            }
        }
        
        initParse ();
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);

        if (_textMD == null || parseIndex == 0) {
            _textMD = new TextMDMetadata();
        }
        /* We may have already done the checksums while converting a
           temporary file. */
        Checksummer ckSummer = null;
        if (_je != null && _je.getChecksumFlag () &&
            info.getChecksum ().size () == 0) {
            ckSummer = new Checksummer ();
            _cstream = new ChecksumInputStream (stream, ckSummer);
            _dstream = getBufferedDataStream (_cstream, _je != null ?
                    _je.getBufferSize () : 0);
        }
        else {
            _dstream = getBufferedDataStream (stream, _je != null ?
                    _je.getBufferSize () : 0);
        }

        ParseHtml parser = null;
        HtmlMetadata metadata = null;
        HtmlCharStream cstream = null;
        try {
            cstream = new HtmlCharStream (_dstream, "ISO-8859-1");
            parser = new ParseHtml (cstream);
        }
        catch (UnsupportedEncodingException e) {
            info.setMessage (new ErrorMessage
                ("Internal error: " + e.getMessage ()));
            info.setWellFormed (false);
            return 0;    // shouldn't happen!
        }
        int type = 0;
        try {
            List elements = parser.HtmlDoc ();
            if (elements.isEmpty ()) {
                // Consider an empty document bad
                info.setWellFormed (false);
                info.setMessage (new ErrorMessage
                    ("Document is empty"));
                return 0;
            }
            type = checkDoctype (elements);
            if (type < 0) {
                info.setWellFormed (false);
                info.setMessage (new ErrorMessage
                    ("DOCTYPE is not HTML"));
                return 0;
            }
            /* Check if there is at least one html, head, body or title tag.  
             * A plain text document
             * might be interpreted as a single PCDATA, which is in some
             * ethereal sense well-formed HTML, but it's pointless to consider
             * it such.  It might also use angle brackets as a text delimiter,
             * and that shouldn't count as HTML either. */
            boolean hasElements = false;
            Iterator iter = elements.iterator ();
            while (iter.hasNext ()) {
                Object o = iter.next ();
                if (o instanceof JHOpenTag) {
                    String name = ((JHOpenTag) o).getName ();
                    if ("html".equals (name) ||
                            "head".equals (name) ||
                            "body".equals (name) ||
                            "title".equals (name)) {
                        hasElements = true;
                    }
                    break;
                }
            }
            if (!hasElements) {
                info.setMessage (new ErrorMessage ("Document contains no html, head, body or title tags"));
                info.setWellFormed (false);
                return 0;
            }
            
            // CRLF from HtmlCharStream ...
            String lineEnd = cstream.getKindOfLineEnd();
            if (lineEnd == null) {
                info.setMessage(new InfoMessage("Not able to determine type of end of line"));
                _textMD.setLinebreak(TextMDMetadata.NILL);
            } else if (lineEnd.equalsIgnoreCase("CR")) {
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_CR);
            } else if (lineEnd.equalsIgnoreCase("LF")) {
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_LF);
            } else if (lineEnd.equalsIgnoreCase("CRLF")) {
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_CRLF);
            }
            
            if (type == 0) {
                /* If we can't find a doctype, it still might be XHTML
                 * if the elements start with an XML declaration and
                 * the root element is "html" */
                switch (seemsToBeXHTML (elements)) {
                    case 0:      // Not XML
                        break;   // fall through
                    case 1:      // XML but not HTML
                        info.setMessage (new ErrorMessage
                            ("Document has XML declaration but no DOCTYPE; " +
                                "probably XML rather than HTML"));
                            info.setWellFormed (false);
                            return 0;
                    case 2:      // probably XHTML
                        return 100;
                }
                info.setMessage (new ErrorMessage
                    ("Unrecognized or missing DOCTYPE declaration; " +
                        "validation continuing as HTML 3.2"));
                info.setValid (false);
                // But keep going
            }
            
            HtmlDocDesc docDesc = null;
            switch (type) {
                case HTML_3_2:
                default:
                    docDesc = new Html3_2DocDesc ();
                    _textMD.setMarkup_basis("HTML");
                    _textMD.setMarkup_basis_version("3.2");
                    break;
     
                case HTML_4_0_FRAMESET:
                   docDesc = new Html4_0FrameDocDesc ();
                   _textMD.setMarkup_basis("HTML");
                   _textMD.setMarkup_basis_version("4.0");
                    break;
                case HTML_4_0_TRANSITIONAL:
                   docDesc = new Html4_0TransDocDesc ();
                   _textMD.setMarkup_basis("HTML");
                   _textMD.setMarkup_basis_version("4.0");
                    break;
                case HTML_4_0_STRICT:
                    docDesc = new Html4_0StrictDocDesc ();
                    _textMD.setMarkup_basis("HTML");
                    _textMD.setMarkup_basis_version("4.0");
                    break;
                case HTML_4_01_FRAMESET:
                    docDesc = new Html4_01FrameDocDesc ();
                    _textMD.setMarkup_basis("HTML");
                    _textMD.setMarkup_basis_version("4.01");
                    break;
                case HTML_4_01_TRANSITIONAL:
                    docDesc = new Html4_01TransDocDesc ();
                    _textMD.setMarkup_basis("HTML");
                    _textMD.setMarkup_basis_version("4.01");
                    break;
                case HTML_4_01_STRICT:
                    docDesc = new Html4_01StrictDocDesc ();
                    _textMD.setMarkup_basis("HTML");
                    _textMD.setMarkup_basis_version("4.01");
                    break;
                case XHTML_1_0_STRICT:
                case XHTML_1_0_TRANSITIONAL:
                case XHTML_1_0_FRAMESET:
                case XHTML_1_1:
                    // Force a second call to parse as XML. 100 is a
                    // magic code for the first XML call.
                    return 100;
            }
            _textMD.setMarkup_language(_doctype);
            if (docDesc == null) {
                info.setMessage (new InfoMessage ("Code for appropriate HTML version not available yet:" +
                    "substituting HTML 3.2"));
                docDesc = new Html3_2DocDesc ();
            }
            docDesc.validate (elements, info);
            metadata = docDesc.getMetadata ();
            
            // Try to get the charset from the meta Content
            if (metadata.getCharset() != null) {
                _textMD.setCharset(metadata.getCharset());
            } else {
                _textMD.setCharset(TextMDMetadata.CHARSET_ISO8859_1);
            }
            String textMDEncoding = _textMD.getCharset();
            if (textMDEncoding.indexOf("UTF") != -1) {
                _textMD.setByte_order(
                        _bigEndian?TextMDMetadata.BYTE_ORDER_BIG:TextMDMetadata.BYTE_ORDER_LITTLE);
                    _textMD.setByte_size("8");
                    _textMD.setCharacter_size("variable");
            } 
            else {
                _textMD.setByte_order(
                        _bigEndian?TextMDMetadata.BYTE_ORDER_BIG:TextMDMetadata.BYTE_ORDER_LITTLE);
                    _textMD.setByte_size("8");
                    _textMD.setCharacter_size("1");
            }
        }
        catch (ParseException e) {
            Token t = e.currentToken;
            info.setMessage (new ErrorMessage ("Parse error",
                "Line = " + t.beginLine + ", column = " + t.beginColumn));
            info.setWellFormed (false);
        }
        catch (TokenMgrError f) {
            info.setMessage (new ErrorMessage ("TokenMgrError: " +
                f.getLocalizedMessage()));
            info.setWellFormed (false);
        }

        if (info.getWellFormed() == RepInfo.FALSE) {
            return 0;
        }

        if (type != 0) {
            if (profileNames[type] != null) {
                info.setProfile (profileNames[type]);
            }
            info.setVersion (versionNames[type]);
        }
        
        if (metadata != null) {
	    Property property = metadata.toProperty (_withTextMD?_textMD:null);
	    if (property != null) {
		info.setProperty (property);
	    }
        }
        
        if (ckSummer != null){
            info.setSize (_cstream.getNBytes ());
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

        return 0;
    }
    
    
    /**
     *  Check if the digital object conforms to this Module's
     *  internal signature information.
     *  
     *  HTML is one of the most ill-defined of any open formats, so
     *  checking a "signature" really means using some heuristics. The only
     *  required tag is TITLE, but that could occur well into the file. So we
     *  look for any of three strings -- taking into account case-independence
     *  and white space -- within the first sigBytes bytes, and call that
     *  a signature check.
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
        char[][] sigtext = new char[3][];
        sigtext[0] = "<!DOCTYPE HTML".toCharArray();
        sigtext[1] = "<HTML".toCharArray();
        sigtext[2] = "<TITLE".toCharArray();
        int[] sigstate = {0, 0, 0};
        JhoveBase jb = getBase();
        int sigBytes = jb.getSigBytes();
        int bytesRead = 0;
        boolean eof = false;
        DataInputStream dstream = new DataInputStream (stream);
        while (!eof && bytesRead < sigBytes) {
                try {
                    int ch = readUnsignedByte (dstream, this);
                    char chr = Character.toUpperCase((char) ch);
                    ++bytesRead;
                    if (Character.isWhitespace (chr)) {
                        continue;  // ignore all whitespace
                    }
                    for (int i = 0; i < 3; i++) {
                        int ss = sigstate[i];
                        char[] st = sigtext[i];
                        if (chr == st[ss]) {
                            ++sigstate[i];
                            if (sigstate[i] == st.length) {
                                // One of the sig texts matches!
                                info.setSigMatch(_name);
                                return;
                            }
                        }
                        else sigstate[i] = 0;
                    }
                }
                catch (EOFException e) {
                    eof = true;
                }
        }
        // If we fall through, there was no sig match
        info.setWellFormed (false);
        return;
        
    }
    
    
    
    /* Check if there is a DOCTYPE at the start of the elements
    * list.  If there is, return the appropriate version string.
    * If the DOCTYPE says it isn't HTML, trust it and call this
    * document ill-formed by returning -1.
    * If there is no DOCTYPE, or an unrecognized one, return 0.
    */
    protected int checkDoctype (List elements)
    {
        JHElement firstElem = (JHElement) elements.get (0);
        if (firstElem instanceof JHXmlDecl && elements.size() >= 2) {
            firstElem = (JHElement) elements.get (1);
        }
        if (!(firstElem instanceof JHDoctype)) {
            return 0;   // no DOCTYPE found
        }
        List dt = ((JHDoctype) firstElem).getDoctypeElements ();
        if (dt.size () < 3) {
            return 0;
        }
        try {
            // Is DOCTYPE case sensitive?  Assume not.
            String str = ((String) dt.get(0)).toUpperCase ();
            if (!"HTML".equals (str)) {
                // It's not HTML
                return -1;
            }
            str = ((String) dt.get (1)).toUpperCase ();
            if (!"PUBLIC".equals (str)) {
                return 0;
            }
            str = stripQuotes (((String) dt.get (2)).toUpperCase ());
            _doctype = str;
            if ("-//W3C//DTD HTML 3.2 FINAL//EN".equals (str) ||
                "-//W3C//DTD HTML 3.2//EN".equals (str)) {
                return HTML_3_2;
            }
            else if ("-//W3C//DTD HTML 4.0//EN".equals (str)) {
                return HTML_4_0_STRICT;
            }
            else if ("-//W3C//DTD HTML 4.0 TRANSITIONAL//EN".equals (str)) {
                return HTML_4_0_TRANSITIONAL;
            }
            else if ("-//W3C//DTD HTML 4.0 FRAMESET//EN".equals (str)) {
                return HTML_4_0_FRAMESET;
            }
            else if ("-//W3C//DTD HTML 4.01//EN".equals (str)) {
                return HTML_4_01_STRICT;
            }
            else if ("-//W3C//DTD HTML 4.01 TRANSITIONAL//EN".equals (str)) {
                return HTML_4_01_TRANSITIONAL;
            }
            else if ("-//W3C//DTD HTML 4.01 FRAMESET//EN".equals (str)) {
                return HTML_4_01_FRAMESET;
            }
        }
        catch (Exception e) {
            // Really shouldn't happen, but if it does we've got
            // a bad doctype
            return 0;
        }
        return 0;
    }
    
    /*  See if this document, even if it lacks a doctype, is most likely
     *  XHTML.  The test is that the document starts with an XML declaration
     *  and has "html" for its first tag.
     * 
     *  Returns:
     *     0 if there's no XML declaration
     *     1 if there's an XML declaration but no html tag; in this
     *       case it's probably some other kind of XML
     *     2 if there's an XML declaration and an html tag
     * 
     */
    protected int seemsToBeXHTML (List elements)
    {
        JHElement elem;
        try {
            elem = (JHElement) elements.get (0);
            if (!(elem instanceof JHXmlDecl)) {
                return 0;
            }
            Iterator iter = elements.iterator ();
            while (iter.hasNext ()) {
                elem = (JHElement) iter.next ();
                if (elem instanceof JHOpenTag) {
                    JHOpenTag tag = (JHOpenTag) elem;
                    return ("html".equals (tag.getName()) ? 2 : 1);
                }
            }
        }
        catch (Exception e) {
            return 0;    // document must be really empty
        }
        return 1;
    }
    
    /* Remove quotes from the beginning and end of a string.  If it doesn't
     * have quotes in both places, leave it alone. */
    protected String stripQuotes(String str) {
        int len = str.length ();
        if (str.charAt (0) == '"' &&
                str.charAt (len - 1) == '"') {
            return str.substring(1, len - 1);
        }
        else {
            return str;
        }
    }

    /* Checks if the XML module is available. 
     */
    protected static boolean isXmlAvailable ()
    {
        try {
            Class.forName ("edu.harvard.hul.ois.jhove.module.XmlModule");
            return true;
        }
        catch (Exception e) {
            return false;
        }
    }

}
