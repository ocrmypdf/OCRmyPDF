/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


import org.xml.sax.*;

/**
 *  This class encapsulates XMP metadata within a file.  It makes use
 *  of an InputStream as a data source.
 *
 *  This differs from normal XML handling in that it's necessary to
 *  process the xpacket processing instruction in order to determine
 *  the encoding of the XML.  the processingInstruction function looks
 *  for xpacket, and throws a special SAXException if it's necessary
 *  to change encoding.
 *
 *  We don't actually extract any information from the XMP, but
 *  simply check it for well-formedness.  By convention, XMPHandler
 *  should be invoked on an XMPSource (TBW), which provides the
 *  ability to recapture the InputStream from which the XMP was
 *  obtained and put it into a property once it's verified here.
 *  
 */
public class XMPHandler extends org.xml.sax.helpers.DefaultHandler {

    /* URI strings */
    private final static String xmpBasicSchema = 
        "http://ns.adobe.com/xap/1.0/";
//    private final static String xmpRightsSchema =
//        "http://ns.adobe.com/xap/1.0/rights/";
//    private final static String dublinCoreSchema =
//        "http://purl.org/dc/elements/1.1/";
//    private final static String adobePDFSchema =
//        "http://ns.adobe.com/pdf/1.3/";
//    private final static String photoshopSchema =
//        "http://ns.adobe.com/photoshop/1.0/";

    private int curStructType;
    /* Values which may be assigned to curStructType */
    private final static int
        UNASSIGNED = 0,
        BAG = 1,
        ALT = 2,
        SEQ = 3;
        
    private boolean pdfaCompliant;
        
    public XMPHandler ()
    {
        super ();
        pdfaCompliant = true;            // compliance is presumed till disproven
    }


    /** Returns true if no violations of PDF/A compliance have been found,
     *  false if a problem was detected. */
    public boolean isPdfaCompliant () {
        return pdfaCompliant;
    }
    
    
    public void processingInstruction (String target, String data)
                        throws SAXException
    {
        if ("xpacket".equals (target)) {
            // We assume that the data will be non-endian (i.e., simply
            // a stream of bytes) unless we find a valid endian code.
            boolean bigEndian = false;
            boolean noEndian = true;
            // a Processing Instruction can't really have attributes,
            // so we have to parse the data string ourselves.  The order
            // of the attributes is guaranteed, fortunately.
            int idx = data.indexOf ("begin=");
            idx = data.indexOf ('"', idx + 1);
            if (data.length () >= idx + 2) {
                int char1 = (int) data.charAt (idx + 1);
                int char2 = (int) data.charAt (idx + 2);
                if (char1 == 0XFF && char2 == 0XFE) {
                    noEndian = false;
                    bigEndian = false;
                } 
                else if (char1 == 0XFE && char2 == 0XFF) {
                    noEndian = false;
                    bigEndian = true;
                } 
                // EF BB B8 signifies UTF-8, but that's the default anyway.
            }
            // Check the bytes attribute. We don't do anything with it except
            // note that it isn't allowed with PDF/A.
            idx = data.indexOf("bytes=");
            if (idx > 0) {
                pdfaCompliant = false;
            }
            // Next find encoding, which is optional.
            idx = data.indexOf ("encoding=");
            if (idx > 0) {
                pdfaCompliant = false;          // not allowed in PDF/A
                idx = data.indexOf ('"', idx + 1);
                int encEnd = data.indexOf ('"', idx + 1 );
                String encoding = data.substring (idx + 1, encEnd);
                // Throw a SAXException which consists of 
                // "ENC=<endian>,<enc>", where 
                // endian is either 'B' (big), 'L' (little) or space (none), and 
                // enc is the encoding attribute.
                // This is an expected exception, not an error.
                String exText = "ENC=";
                if (noEndian) {
                    exText += " ,";
                }
                else if (bigEndian) {
                    exText += "B,";
                }
                else {
                    exText += "L,";
                }
                exText += encoding;
                throw new SAXException (exText);
            }
        }
    }
    
    
    /**
     *  Catches the start of an element and, if it's one we care
     *  about, sets state information.
     */
    public void startElement (String namespaceURI, String localName,
                  String rawName, Attributes atts)
    throws SAXException
    {
        //System.out.println (namespaceURI);   // Just for debugging and placeholding
        if (xmpBasicSchema.equals (namespaceURI)) {
            if ("Bag".equals (rawName)) {
                curStructType = BAG;
            }
            else if ("Seq".equals (rawName)) {
                curStructType = SEQ;
            }
            else if ("Alt".equals (rawName)) {
                curStructType = ALT;
            }
        }
    }
    
    
    /**
     *  Catches the end of an element.
     */
    public void endElement (String namespaceURI, String localName,
                String rawName)
    throws SAXException
    {
        if (xmpBasicSchema.equals (namespaceURI)) {
            // Check for the end of an XMP structure
            if ("Bag".equals (rawName)||
                    "Seq".equals (rawName) ||
                    "Alt".equals (rawName)) {
                curStructType = UNASSIGNED;
            }
        }
    }
    
    /** Catch a fatal error.  This is put here because the default
     *  behavior is to report a "fatal error" to standard output,
     *  which is harmless but scary.  
     */
    public void fatalError(SAXParseException exception)
                throws SAXException
    {
    }
}
