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
import edu.harvard.hul.ois.jhove.module.xml.*;
import edu.harvard.hul.ois.jhove.module.html.HtmlMetadata;
import edu.harvard.hul.ois.jhove.module.html.DTDMapper;

import org.xml.sax.XMLReader;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import org.xml.sax.helpers.*;

/**
 *  Module for identification and validation of XML files.
 *  @author Gary McGath
 */
public class XmlModule
    extends ModuleBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "XML-hul";
    private static final String RELEASE = "1.4";
    private static final int [] DATE = {2007, 1, 8};
    private static final String [] FORMAT = {
        "XML", "XHTML"
    };
    private static final String COVERAGE = "XML 1.0";
    /* According to RFC 3023, text/xml should be used for human-readable
     * XML documents, and application/xml should be used for documents
     * that aren't easily read by humans.  Since that determination
     * is beyond the scope of this project, we err on the side of 
     * pessimism and use application/xml as the primary MIME type.
     * <code>MIMETYPE[2]</code> is only for XHTML. */
    private static final String [] MIMETYPE = {
	"text/xml", "application/xml", "text/html"
    };
    private static final String WELLFORMED = "An XML file is well-formed if " +
	"it meets the criteria defined in Section 2.1 of the XML " +
	"specification (W3C Recommendation, 3rd edition, 2004-02-04)";
    private static final String VALIDITY = "An XML file is valid if " +
	"well-formed, and the file has an associated DTD or XML Schema and " +
	"the file meets the constraints defined by that DTD or Schema";
    private static final String REPINFO = "Additional representation " +
	"information includes: version, endcoding, standalone flag, DTD or " +
	"schema, namespaces, notations, character references, entities, " +
	"processing instructions, and comments";
    private static final String NOTE = "This module determines " +
	"well-formedness and validity using the SAX2-conforming parser " +
	"specified by the invoking application";
    private static final String RIGHTS = "Copyright 2004-2007 by JSTOR and " +
	"the President and Fellows of Harvard College. " +
	"Released under the GNU Lesser General Public License.";

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /* Checksummer object */
    protected Checksummer _ckSummer;
    
    /* Input stream wrapper which handles checksums */
    protected ChecksumInputStream _cstream;
    
    /* Data input stream wrapped around _cstream */
    protected DataInputStream _dstream;

    /* Top-level property list. */
    protected List<Property> _propList;
    
    /* Top-level property. */
    protected Property _metadata;
    
    /* Doctype for XHTML documents only, otherwise null. */
    protected String _xhtmlDoctype;
    
    /* Base URL for DTD's.  If null, all DTD URL's are absolute. */
    protected String _baseURL;
    
    /* Flag to control signature checking behavior. If true,
     * checkSignatures insists on an XML document declaration; if
     * false, it will parse the file if there is no document
     * declaration.
     */
    protected boolean _sigWantsDecl;
    
    /* Flag to indicate we're invoking the parser from checkSignatures.
     * When true, it's up to checkSignatures to mark a signature as present.
     */
    protected boolean _parseFromSig;

    /* Flag to know if the property TextMDMetadata is to be added */
    protected boolean _withTextMD = false;
    /* Hold the information needed to generate a textMD metadata fragment */
    protected TextMDMetadata _textMD;
    
    /* Map from URIs to locally stored schemas */
    protected Map<String, File> _localSchemas;
    
    /******************************************************************
    * CLASS CONSTRUCTOR.
    ******************************************************************/
   /**
     *  Instantiate an <tt>XmlModule</tt> object.
     */
   public XmlModule ()
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

       Document doc = new Document ("Extensible Markup Language (XML) 1.0 " +
				    "(Third Edition)", DocumentType.REPORT);
       agent = new Agent ("Word Wide Web Consortium", AgentType.NONPROFIT);
       agent.setAddress ("Massachusetts Institute of Technology, " +
			 "Computer Science and Artificial Intelligence Laboratory, " +
			 "32 Vassar Street, Room 32-G515, " +
			 "Cambridge, MA 02139");
       agent.setTelephone ("(617) 253-2613");
       agent.setFax ("(617) 258-5999");
       agent.setWeb ("http://www.w3.org/");
       doc.setPublisher (agent);
       doc.setDate ("2004-02-04");
       doc.setIdentifier (new Identifier ("http://www.w3.org/TR/REC-xml",
                                          IdentifierType.URL));
       _specification.add (doc);

       doc = new Document ("SAX", DocumentType.WEB);
       doc.setIdentifier (new Identifier ("http://sax.sourceforge.net/",
                                          IdentifierType.URL));
       _specification.add (doc);

       Signature sig = new ExternalSignature (".xml", SignatureType.EXTENSION,
                                    SignatureUseType.OPTIONAL);
       _signature.add (sig);
       _localSchemas = new HashMap<String, File> ();
   }

   /**  Sets the value of the doctype string, assumed to have been forced
    *   to upper case.  This is set only when the HTML module invokes the
    *   XML module for an XHTML document. */
   public void setXhtmlDoctype (String doctype)
   {
       _xhtmlDoctype = doctype;
       if (_textMD != null) {
           _textMD.setMarkup_language(_xhtmlDoctype);
       }
   }

    /** Reset parameter settings.
     *  Returns to a default state without any parameters.
     */
    public void resetParams ()
        throws Exception
    {
        _baseURL = null;
        _sigWantsDecl = false;
        _parseFromSig = false;
    }

    /**
     * Per-action initialization.
     *
     * @param	param The module parameter; under command-line Jhove, the -p parameter.
     *        If the parameter starts with "schema", then the part to the
     *        right of the equal sign identifies a URI with a local path
     *        (URI, then semicolon, then path).
     *        If the first character is 's' and the parameter isn't "schema", 
     *        then signature checking requires
     *        a document declaration, and the rest of the URL is considered
     *        as follows.
     *        If the parameter begins with 'b' or 'B', then the remainder of
     *        the parameter is used as a base URL.  Otherwise it is ignored,
     *        and there is no base URL.
     */
    public void param (String param)
    {
        if (param != null) {
            param = param.toLowerCase ();
            if (param.toLowerCase ().startsWith("schema=")) {
                addLocalSchema(param);
            }
            else if (param.indexOf ('s') == 0) {
                _sigWantsDecl = true;
                param = param.substring(1);
            }
            else if (param.indexOf ('b') == 0) {
                _baseURL = param.substring (1);
            }
        }
    }


   /**
    *   Parse the content of a purported XML digital object and store the
    *   results in RepInfo.
    * 
    *   This is designed to be called in two passes.  On the first pass,
    *   a nonvalidating parse is done.  If this succeeds, and the presence
    *   of DTD's or schemas is detected, then parse returns 1 so that it
    *   will be called again to do a validating parse.  If there is nothing
    *   to validate, we consider it "valid."
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
        // Test if textMD is to be generated

        if (_defaultParams != null) {
            _withTextMD = false;
            Iterator<String> iter = _defaultParams.iterator ();
            while (iter.hasNext ()) {
                String param = iter.next ();
                if (param.toLowerCase ().equals ("withtextmd=true")) {
                    _withTextMD = true;
                }
            }
        }
        
        //boolean foundDTD = false;
        boolean canValidate = true;
        initParse ();
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        if (_textMD == null || parseIndex == 0) {
            _textMD = new TextMDMetadata();
            _xhtmlDoctype = null;
        }
        
        /* We may have already done the checksums while converting a
           temporary file. */
        _ckSummer = null;
        if (_je != null && _je.getChecksumFlag () &&
            info.getChecksum ().size () == 0) {
            _ckSummer = new Checksummer ();
        }
        _cstream = new ChecksumInputStream (stream, _ckSummer);

        _propList = new LinkedList<Property> ();
        _metadata = new Property ("XMLMetadata",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                _propList);

        XMLReader parser = null;
        InputSource src = null;
        XmlModuleHandler handler = null;
        XmlLexicalHandler lexHandler = new XmlLexicalHandler ();
        XmlDeclHandler declHandler = new XmlDeclHandler ();
        
        // The XmlDeclStream filters the characters, looking for an
        // XML declaration,  since there's no way to get that info
        // out of SAX.
        XmlDeclStream xds = new XmlDeclStream (_cstream);
        try {
            // Create an InputSource to feed the parser.
            // If a SAX class was specified, use it, otherwise use
            // the default parser.
            src = new InputSource (xds);
            // setSystemId may be helpful in resolving relative URI's,
            // though its use is unclear.  Its actual content is merely
            // informative, not a part of any actual link
            //src.setSystemId ("http://hul.harvard.edu/hul");
            if (_baseURL != null) {
                src.setSystemId(new File(_baseURL).toURI().toURL().toString());
            }
            String saxClass = _je.getSaxClass();
            if (saxClass == null) {
                SAXParserFactory factory = 
                                SAXParserFactory.newInstance();
                factory.setNamespaceAware (true);
                parser = factory.newSAXParser ().getXMLReader ();
            }
            else {
                parser = XMLReaderFactory.createXMLReader (saxClass);
            }
            handler = new XmlModuleHandler ();
            handler.setXhtmlFlag (_xhtmlDoctype != null);
            handler.setLocalSchemas (_localSchemas);
            parser.setContentHandler (handler);
            parser.setErrorHandler (handler);
            parser.setEntityResolver (handler);
            parser.setDTDHandler (handler);
            try {
                parser.setProperty 
                    ("http://xml.org/sax/properties/lexical-handler",
                     lexHandler);
            }
            catch (SAXException e) {
                info.setMessage (new InfoMessage 
                        ("The XML implementation in use does not " +
                        "support the LexicalHandler interface. " +
                        "This may result in some properties not being reported."));
            }
            try {
                parser.setProperty 
                    ("http://xml.org/sax/properties/declaration-handler",
                     declHandler);
            }
            catch (SAXException e) {
                info.setMessage (new InfoMessage 
                        ("The XML implementation in use does not " +
                        "support the DeclHandler interface. " +
                        "This may result in some properties not being reported."));
            }
            
        }
        catch (Exception f) {
            info.setMessage(new ErrorMessage (f.getMessage()));
            info.setWellFormed (false);  // actually not the file's fault
            return 0;
        }
        try {
            // On the first pass, we parse without validation.
            parser.setFeature ("http://xml.org/sax/features/validation",
                parseIndex == 0 ? false : true);
        }
        catch (SAXException se) {
            if (parseIndex != 0) {
                info.setMessage (new InfoMessage 
                    ("The SAX parser is not capable of validation."));
            }
            canValidate = false;
        }
        try {
            parser.setFeature ("http://xml.org/sax/features/namespaces",
                true);
        }
        catch (SAXException se) {
            info.setMessage (new InfoMessage 
                ("The SAX parser does not support namespaces."));
        }
        // This property for supporting schemas is a JAXP 1.2
        // recommendation, not likely to be supported widely as
        // of this (February 2004) writing, and not supported in
        // standard Crimson.  But it looks like the way to prepare
        // for schema validation in the future, and at least the
        // info message will tell users why they're getting bogus
        // invalid status.
        
        // Try 2 different ways of setting schema validation;
        // it appears that no one way works for all parsers.
        if (parseIndex > 0) {
            try {
                parser.setFeature("http://apache.org/xml/features/validation/schema",
                        true);
            }
            catch (SAXException ee) {
                try {
                    parser.setProperty 
                        ("http://java.sun.com/xml/jaxp/properties/schemaLanguage",
                         "http://www.w3.org/2001/XMLSchema");
                }
                catch (SAXException e) {
                    info.setMessage (new InfoMessage 
                            ("The XML implementation in use does not " +
                            "support schema language identification.  This " +
                            "may result in documents specified by schemas " +
                            "being reported as invalid."));
                }
            }
        }
        try {
            parser.parse (src);
        }
        catch (FileNotFoundException ef) {
            // Make this particular exception a little more user-friendly
            info.setMessage (new ErrorMessage
                    ("File not found",
                     ef.getMessage ().toString ()));
            info.setWellFormed (false);
            return 0;
        }
        catch (UTFDataFormatException u) {
            if (handler.getSigFlag () && !_parseFromSig) {
                info.setSigMatch(_name);
            }
            info.setMessage (new ErrorMessage ("Invalid character encoding"));
            info.setWellFormed (false);
            return 0;
        }
        catch (IOException e) {
            // We may get an IOException from trying to resolve an
            // external entity.
            if (handler.getSigFlag () && !_parseFromSig) {               
                info.setSigMatch(_name);
            }
            info.setMessage (new ErrorMessage
                    (e.getClass().getName() + ": " + 
                     e.getMessage ().toString ()));
            info.setWellFormed (false);
            return 0;
        }
        catch (SAXParseException e) {
            // Document failed to parse.
            if (handler.getSigFlag () && !_parseFromSig) {
                info.setSigMatch(_name);
            }
            int line = e.getLineNumber();
            int col = e.getColumnNumber();
            info.setMessage (new ErrorMessage 
                    (e.getMessage ().toString (),
                     "Line = " + line + ", Column = " + col));
            info.setWellFormed (false);
            return 0;
        }
        catch (SAXException e) {
            // Other SAX error.
            if (handler.getSigFlag ()) {
                info.setSigMatch(_name);
            }
            // Sometimes the message will be null and another message
            // wrapped inside it.  Try to report that.
            String msg = e.getMessage ();
            if (msg == null) {
                Throwable ee = e.getCause();
                if (ee != null) {
                    msg = "SAXException, cause = " +
                        ee.getClass().getName();
                }
                else {
                    msg = "Unspecified SAXException";
                }
            }
            info.setMessage (new ErrorMessage (msg));
            info.setWellFormed (false);
            return 0;
        }
        
        // Check if user has aborted
        if (_je.getAbort ()) {
            return 0;
        }
        
        if (handler.getSigFlag () && parseIndex == 0) {
            info.setSigMatch(_name);
        }
        // If it's the first pass, check if we found a DTD
        // or schema.
        // If so, reparse with validation enabled.
        // (Validation with schemas may prove futile, as the
        // Crimson parser understands only DTD and DOCTYPE
        // declarations as contributing to validity.)
        String dtdURI = handler.getDTDURI ();
        List<SchemaInfo> schemaList = handler.getSchemas ();
        
        // In order to find the "primary" markup language, we try 3 things :
        // 1/ first, the first NamespaceURI
        // 3/ then, the first SchemaLocation
        // 1/ finally, the dtd URI
        // It should be noted that latter on when we look at the namespace in relation with the Root element
        // if a URI is defined with it, it will get the preference ...
        if (!schemaList.isEmpty()) {
            SchemaInfo schItems = schemaList.get(0);
            // First NamespaceURI
            if (isNotEmpty(schItems.namespaceURI)) {
                _textMD.setMarkup_language(schItems.namespaceURI);
            // Then SchemaLocation
            } 
            else if (isNotEmpty(schItems.location)) {
                _textMD.setMarkup_language(schItems.location);
            }
        } 
        else if (isNotEmpty(dtdURI)) {
            _textMD.setMarkup_language(dtdURI);
        }
        
        if (parseIndex == 0) {
            if ((handler.getDTDURI () != null ||
                 !schemaList.isEmpty ()) &&
                canValidate) {
                return 1;
            }
            else {
                info.setValid (RepInfo.UNDETERMINED);
                // This may get downgraded to false, but won't
                // be upgraded to true.
            }
        }
        
        // Take a deep breath.  We parsed it.  Now assemble the
        // properties.
        info.setProperty (_metadata);
        
        // If it's XHTML, add the HTML property.
        HtmlMetadata hMetadata = handler.getHtmlMetadata ();
        if (hMetadata != null) {
            info.setProperty (hMetadata.toProperty (_withTextMD?_textMD:null));
        }

        // Report the parser in a property.
        _propList.add (new Property ("Parser",
                        PropertyType.STRING,
                        parser.getClass().getName()));

        // Add the version property.  Give precedence to XHTML doctype.
        String vers = null;
        if (_xhtmlDoctype != null) {
            vers = DTDMapper.getXHTMLVersion(_xhtmlDoctype);
            _textMD.setMarkup_language_version(vers);
        }
        if (vers != null) {
            info.setVersion (vers);
        }
        else {
            vers = xds.getVersion ();
            if (vers != null) {
                info.setVersion (vers);
            }
        }
        _textMD.setMarkup_basis_version(vers);
        
        // Add the encoding property.
        String encoding = xds.getEncoding ();
        if (encoding == null) {
            // If no explicit encoding, use default (Bugzilla 136)
            encoding = "UTF-8";
        }
        _propList.add (new Property ("Encoding",
                        PropertyType.STRING,
                        encoding));
        
        _textMD.setCharset(encoding);
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
        // CRLF from XmlDeclStream ...
        String lineEnd = xds.getKindOfLineEnd();
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
        
        // Add the standalone property.
        String sa = xds.getStandalone ();
        if (sa != null) {
            _propList.add (new Property ("Standalone",
                        PropertyType.STRING,
                        sa));
        }
        
        // Add the DTD property.
        if (dtdURI != null) {
            _propList.add (new Property ("DTD_URI",
                        PropertyType.STRING,
                        dtdURI));
        }

        if (!schemaList.isEmpty ()) {
            // Build a List of Properties, which will be the value
            // of the Schemas Property.
            List<Property> schemaPropList = new ArrayList<Property> (schemaList.size());
            ListIterator<SchemaInfo> iter = schemaList.listIterator();
            // Iterate through all the schemas.
            while (iter.hasNext ()) {
                SchemaInfo schItems = iter.next ();
                // Build a Property (Schema) whose value is an array
                // of two Properties (NamespaceURI and SchemaLocation).
                Property [] schItemProps = new Property[2];
                schItemProps[0] = new Property ("NamespaceURI",
                        PropertyType.STRING,
                        schItems.namespaceURI);
                schItemProps[1] = new Property ("SchemaLocation",
                        PropertyType.STRING,
                        schItems.location);
                schemaPropList.add (new Property ("Schema",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        schItemProps));
            }
            // Now put the list into a Property, which goes into
            // the metadata.
            Property prop = new Property ("Schemas",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            schemaPropList);
            _propList.add (prop);
        }
        
        // Add the root element.
        String root = handler.getRoot ();
        String rootPrefix = null;
        if (root != null) {
            _propList.add (new Property ("Root",
                        PropertyType.STRING,
                        root));
            if ("html".equals (root)) {
                // Specify format as XHTML
                info.setFormat (_format[1]);
                // Set the version according to the doctype... how?

            }
            // Get the prefix of root
            int indexOfColon = root.indexOf(':');
            if (indexOfColon != -1) {
                rootPrefix = root.substring(0, indexOfColon);
            }
        }
        if (rootPrefix == null) {
            rootPrefix = "";
        }
        
        // Declare properties we're going to add.  They have
        // some odd interdependencies, so we create them all
        // and them add them in the right (specified) order.
        Property namespaceProp = null;
        Property notationsProp = null;
        Property charRefsProp = null;
        Property entitiesProp = null;
        Property procInstProp = null;
        Property commentProp = null;
        Property unicodeBlocksProp = null;
        
        Map<String, String> ns = handler.getNamespaces ();
        if (!ns.isEmpty ()) {
            Set<String> keys = ns.keySet ();
            List<Property> nsList = new ArrayList<Property> (keys.size());
            Iterator<String> iter = keys.iterator();
            while (iter.hasNext ()) {
                String key =  iter.next ();
                String val = (String) ns.get (key);
                Property [] supPropArr = new Property[2];
                supPropArr[0] = new Property ("Prefix",
                            PropertyType.STRING,
                            key);
                supPropArr[1] = new Property ("URI",
                            PropertyType.STRING,
                            val);
                Property onens = new Property ("Namespace",
                            PropertyType.PROPERTY,
                            PropertyArity.ARRAY,
                            supPropArr);
                nsList.add (onens); 
                
                // Try to find the namespace URI of root
                if (rootPrefix.equalsIgnoreCase(key) && isNotEmpty(val)) {
                    _textMD.setMarkup_language(val);
                }
            }
            namespaceProp = new Property ("Namespaces",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            nsList);
        }
       
        // CharacterReferences property goes here.
        // Report as a list of 4-digit hexadecimal strings,
        // e.g., 003C, 04AA, etc.
        // Also build the Unicode blocks here.
        List<Integer> refs = xds.getCharacterReferences ();
        if (!refs.isEmpty ()) {
            Utf8BlockMarker utf8BM = new Utf8BlockMarker ();
            List<String> refList = new ArrayList<String> (refs.size ());
            ListIterator<Integer> iter = refs.listIterator ();
            while (iter.hasNext ()) {
                Integer refi = iter.next ();
                int refint = refi.intValue ();
                refList.add (intTo4DigitHex (refint));
                utf8BM.markBlock(refint);
            }
            charRefsProp = new Property 
                    ("CharacterReferences",
                     PropertyType.STRING,
                     PropertyArity.LIST,
                     refList);
            unicodeBlocksProp = 
                utf8BM.getBlocksUsedProperty("UnicodeCharRefBlocks");
        }
        
        // Entities property
        // External unparsed entities
        Set<String> entNames = lexHandler.getEntityNames ();
        Set<String> attributeVals = handler.getAttributeValues ();
        List<Property> entProps = new LinkedList<Property> ();
        List<String[]> uent = handler.getUnparsedEntities ();
        List<String> unparsedNotationNames = new LinkedList<String> ();
        if (!uent.isEmpty ()) {
             ListIterator<String[]> iter = uent.listIterator ();
            //int i = 0;
            while (iter.hasNext ()) {
                // We check external parsed entities against
                // the list of attribute values which we've
                // accumulated.  If a parsed entity name matches an
                // attribute value, we assume it's used.
                String[] entarr = (String[]) iter.next ();
                String name = entarr[0];
                if (nameInCollection (name, attributeVals)) {
                    // Add the notation name to the list 
                    // unparsedNotationNames, so we can use it
                    // in determining which notations are used.
                    unparsedNotationNames.add (entarr[3]);
                    List<Property> subPropList = new ArrayList<Property> (6);
                    subPropList.add( new Property ("Name",
                            PropertyType.STRING,
                            name));
                    subPropList.add (new Property ("Type",
                            PropertyType.STRING,
                            "External unparsed"));
                    subPropList.add( new Property ("PublicID",
                            PropertyType.STRING,
                            entarr[1]));
                    subPropList.add( new Property ("SystemID",
                            PropertyType.STRING,
                            entarr[2]));
                    subPropList.add( new Property ("NotationName",
                            PropertyType.STRING,
                            entarr[3]));
                    
                    entProps.add (new Property ("Entity",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            subPropList));
                }
            }
        }
  
        // Internal entities
        List<String[]> declEnts = declHandler.getInternalEntityDeclarations ();
        if (!declEnts.isEmpty ()) {
            ListIterator<String[]> iter = declEnts.listIterator ();
            while (iter.hasNext ()) {
                String[] entarr =  iter.next ();
                String name = entarr[0];
                // include only if the entity was actually used
                if (nameInCollection (name, entNames)) {
                    List<Property> subPropList = new ArrayList<Property> (4);
                    subPropList.add (new Property ("Name",
                            PropertyType.STRING,
                            name));
                    subPropList.add (new Property ("Type",
                            PropertyType.STRING,
                            "Internal"));
                    subPropList.add (new Property ("Value",
                            PropertyType.STRING,
                            entarr[1]));
                    entProps.add (new Property ("Entity",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        subPropList));
                }
            }
        }

        // External parsed entities
        declEnts = declHandler.getExternalEntityDeclarations ();
        if (!declEnts.isEmpty ()) {
            ListIterator<String[]> iter = declEnts.listIterator ();
            while (iter.hasNext ()) {
                String[] entarr =  iter.next ();
                String name = entarr[0];
                // include only if the entity was actually used
                if (nameInCollection (name, entNames)) {
                    List<Property> subPropList = new ArrayList<Property> (4);
                    subPropList.add (new Property ("Name",
                            PropertyType.STRING,
                            name));
                    subPropList.add (new Property ("Type",
                            PropertyType.STRING,
                            "External parsed"));
                    if (entarr[1] != null) {
                        subPropList.add (new Property ("PublicID",
                            PropertyType.STRING,
                            entarr[1]));
                    }
                    if (entarr[2] != null) {
                        subPropList.add (new Property ("SystemID",
                            PropertyType.STRING,
                            entarr[2]));
                    }
                    
                    entProps.add (new Property ("Entity",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        subPropList));
                }
            }
        }
        
        if (!entProps.isEmpty ()) {
            entitiesProp = new Property ("Entities",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    entProps);
        }
        
        List<ProcessingInstructionInfo> pi = handler.getProcessingInstructions ();
        List<String> piTargets = new LinkedList<String> ();
        if (!pi.isEmpty()) {
            // Build a property, which consists of a list
            // of properties, each of which is an array of
            // two String properties, named Target and
            // Data respectively.
            List<Property> piPropList = new ArrayList<Property> (pi.size());
            ListIterator<ProcessingInstructionInfo> pii = pi.listIterator ();
            while (pii.hasNext ()) {
                ProcessingInstructionInfo pistr =  pii.next ();
                Property[] subPropArr = new Property[2];
                // Accumulate targets in a list, so we can tell
                // which Notations use them.
                // Wait a minute -- what we're doing here can't work!! TODO what's supposed to be happening?
                //piTargets.add (subPropArr[0]);
                subPropArr[0] = new Property ("Target",
                            PropertyType.STRING,
                            pistr.target);
                subPropArr[1] = new Property ("Data",
                            PropertyType.STRING,
                            pistr.data);
                piPropList.add(new Property ("ProcessingInstruction",
                            PropertyType.PROPERTY,
                            PropertyArity.ARRAY,
                            subPropArr));
            }
            procInstProp = new Property ("ProcessingInstructions",
                            PropertyType.PROPERTY,
                            PropertyArity.LIST,
                            piPropList);
        }

        // Notations property.  We list notations only if they're
        // "actually used," meaning that they designate either
        // the target of a processing instruction or the ndata
        // of an unparsed entry which is itself "actually used."
        List<String[]> notations = handler.getNotations ();
        if (!notations.isEmpty ()) {
            List<Property> notProps = new ArrayList<Property> (notations.size ());
            ListIterator<String[]> iter = notations.listIterator ();
            List<Property> subPropList = new ArrayList<Property> (3);
            while (iter.hasNext ()) {
                String[] notArray = iter.next();
                String notName = notArray[0];
                // Check for use of Notation before including 
                // TODO this is implemented wrong! Need to reinvestigate
                if (nameInCollection (notName, piTargets) ||
                    nameInCollection (notName, unparsedNotationNames)) {
                    // notArray has name, public ID, system ID
                    subPropList.add (new Property ("Name",
                                PropertyType.STRING,
                                notName));
                    if (notArray[1] != null) {
                        subPropList.add (new Property ("PublicID",
                                PropertyType.STRING,
                                notArray[1]));
                    }
                    if (notArray[2] != null) {
                        subPropList.add (new Property ("SystemID",
                                PropertyType.STRING,
                                notArray[2]));
                    }
                    notProps.add (new Property ("Notation",
                                PropertyType.PROPERTY,
                                PropertyArity.LIST,
                                subPropList));
                }
            }
            // Recheck emptiness in case only unprocessed notations were found
            if (!notProps.isEmpty()) {
                notationsProp = new Property ("Notations",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        notProps);
            }
        } 

        // Now add all the properties we created.
        if (namespaceProp != null) {
            _propList.add (namespaceProp);
        }
        if (notationsProp != null) {
            _propList.add (notationsProp);
        }
        if (charRefsProp != null) {
            _propList.add (charRefsProp);
        }
        if (unicodeBlocksProp != null) {
            _propList.add (unicodeBlocksProp);
        }
        if (entitiesProp != null) {
            _propList.add (entitiesProp);
        }
        if (procInstProp != null) {
            _propList.add (procInstProp);
        }

        List<String> comm = lexHandler.getComments ();
        if (!comm.isEmpty ()) {
            commentProp = new Property ("Comments",
                            PropertyType.STRING,
                            PropertyArity.LIST,
                            comm);
        }
        if (commentProp != null) {
            _propList.add (commentProp);
        }
        
        // Check if parse detected invalid XML
        if (!handler.isValid ()) {
            info.setValid (false);
        }

        if (info.getWellFormed () == RepInfo.TRUE) {
            if (_xhtmlDoctype != null) {
                info.setMimeType (_mimeType[2]);
            }
            else {
                info.setMimeType (_mimeType[0]);
            }
        }
        
        // Add any messages from the parse.
        List msgs = handler.getMessages ();
        ListIterator msgi = msgs.listIterator ();
        while (msgi.hasNext ()) {
            info.setMessage ((Message) msgi.next ());
        } 
        
        if (_withTextMD) {
            _textMD.setMarkup_basis(info.getFormat());
            _textMD.setMarkup_basis_version(info.getVersion());
            Property property = new Property ("TextMDMetadata",
                    PropertyType.TEXTMDMETADATA, PropertyArity.SCALAR, _textMD);
            _propList.add(property);
        }
        
        if (_ckSummer != null){
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
        if (info.getVersion () == null) {
            info.setVersion ("1.0");
            _textMD.setMarkup_basis_version("1.0");
        }
        return 0;
    }
    
    
    /**
     *  Check if the digital object conforms to this Module's
     *  internal signature information.
     *  
     *  XML is a particularly messy case; in general, there's no 
     *  even moderately good way to check "signatures" without parsing
     *  the whole file, since the document declaration is optional.
     *  We provide the user two choices, based on the "s" parameter.
     *  If 's' is the first character of the module parameter, then
     *  we look for an XML document declaration, and say there's no
     *  signature if it's missing. (This can reject well-formed
     *  XML files, though not valid ones.) Otherwise, if there's no
     *  document declaration, we parse the whole file.
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
        _parseFromSig = false;
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        String sigStr = "<?xml";
        int sigidx = 0;
        JhoveBase jb = getBase();
        int sigBytes = jb.getSigBytes();
        DataInputStream dstream = new DataInputStream (stream);
        int charsRead = 0;
        try {
            while (charsRead < sigBytes) {
                char ch = dstream.readChar();
                ++charsRead;
                // Skip over all whitespace till we reach "xml"
                if (sigidx <= 2 && Character.isWhitespace(ch)) {
                    continue;
                }
                if (ch == sigStr.charAt (sigidx)) {
                    if (++sigidx >= sigStr.length()) {
                        info.setSigMatch(_name);
                        return;     // sig matches
                    }
                }
                else break;
            }
        }
        catch (IOException e) {
            info.setWellFormed (false);
            return;
        }
        if (_sigWantsDecl) {
            
            // No XML declaration, and it's manadatory according to the param.
            info.setWellFormed (false);
            return;
        }
        
        // No XML signature, but we're allowed to parse the file now.
        // This means rewinding back to the start of the file.
        int parseIndex = 1;
        _parseFromSig = true;    // we set the sig match ourselves
        while (parseIndex != 0) {
            stream.close ();
            stream = new FileInputStream (file);
            parseIndex = parse (stream, info, parseIndex);
        }
        if (info.getWellFormed() == RepInfo.TRUE) {
            info.setSigMatch (_name);
        }
    }
    
    
    
    protected void initParse ()
    {
       super.initParse ();
//       if (_defaultParams != null) {
//           Iterator<String> iter = _defaultParams.iterator ();
//           while (iter.hasNext ()) {
//               String param =  iter.next ();
//               if (param.toLowerCase ().startsWith("localschema=")) {
//                   addLocalSchema(param);
//               }
//           }
//       }
    }
    
    /* Checks if a String is .equals to any member of a Set of strings. */
    protected static boolean nameInCollection (String name, Collection<String> coll) 
    {
        Iterator<String> iter = coll.iterator ();
        while (iter.hasNext ()) {
            String s = (String) iter.next ();
            if (name.equals (s)) {
                return true;
            }
        }
        return false;
    }
    
    /* Converts an int to a 4-digit hex value, e.g.,
     * 003F or F10A.  This is used for Character References. */
    protected static String intTo4DigitHex (int n)
    {
        StringBuffer buf = new StringBuffer(4);
        for (int i = 3; i >= 0; i--) {
            int d = (n >> (4 * i)) & 0XF;  // extract a nybble
            if (d < 10) {
                buf.append ((char) ((int) '0' + d));
            }
            else {
                buf.append ((char) ((int) 'A' + (d - 10)));
            }
        }
        return buf.toString ();
    }
    
    /**
     * Verification that the string contains something usefull.
     * @param value string to test
     * @return boolean
     */
    protected static boolean isNotEmpty(String value) {
        return (
                (value != null) && 
                (value.length() != 0) && 
                !("[None]".equals(value))
         );
    }
    
    /**
     * Add a mapping from a schema URI to a local file.
     * The parameter is of the form schema=[URI];[path]
     */
    private void addLocalSchema (String param) {
        int eq = param.indexOf('=');
        int semi = param.indexOf(';');
        try {
            String uri = param.substring(eq+1, semi).trim();
            String path = param.substring(semi + 1).trim();
            File f = new File (path);
            if (f.exists()) {
                _localSchemas.put (uri, f);
            }
        }
        catch (Exception e) {}
    }
}
