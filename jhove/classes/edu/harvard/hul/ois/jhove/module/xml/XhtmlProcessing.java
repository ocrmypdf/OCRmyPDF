/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.xml;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.html.HtmlMetadata;
import java.util.*;
import org.xml.sax.Attributes;

/**
 * Methods for processing XHTML elements in an XML document.
 * These are closely related in functionality to corresponding
 * methods in the XML module.
 *
 * @author Gary McGath
 * @see  edu.harvard.hul.ois.jhove.module.html.HtmlDocDesc
 */
public final class XhtmlProcessing {

    /** Process an element and extract metadata */
    /** Process the element to extract any available metadata. */
    protected static void processElement (String localName,
                String qualifiedName,
                Attributes atts,
                HtmlMetadata mdata)
    {
        if ("html".equals (localName)) {
            processHtml (mdata, atts);
        }
        else if ("meta".equals (localName)) {
            processMeta (mdata, atts);
        }
        else if ("a".equals (localName)) {
            processA (mdata, atts);
        }
        else if ("img".equals (localName)) {
            processImg (mdata, atts);
        }
        else if ("frame".equals (localName)) {
            processFrame (mdata, atts);
        }
        else if ("script".equals (localName)) {
            processScript (mdata, atts);
        }
        else if ("abbr".equals (localName)) {
            processAbbr (mdata, atts);
        }
        else if ("title".equals (localName)) {
            processTitle (mdata, atts);
        }
        else if ("cite".equals (localName)) {
            processCite (mdata, atts);
        }
        
        /* Look for certain attributes in any tag. */
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("lang".equals (attname) && attval != null) {
                mdata.addLanguage (attval);
            }
        }
    }


    /** Process metadata from an HTML tag */
    private static void processHtml (HtmlMetadata mdata, Attributes atts)
    {
        String lang = null;
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("lang".equals (attname)) {
                lang = attval;
            }
        }
        if (lang != null) {
            mdata.setLanguage(lang);
        }
    }


    /** Process metadata from a META tag */
    private static void processMeta (HtmlMetadata mdata, Attributes atts) 
    {
        String name = null;
        String httpeq = null;
        String content = null;
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("name".equals (attname)) {
                name = attval;
            }
            if ("http-equiv".equals (attname)) {
                httpeq = attval;
            }
            if ("content".equals (attname)) {
                content = attval;
            }
        }
        if (name != null || httpeq != null || content != null) {
            List plist = new ArrayList (3);
            if (name != null) {
                plist.add (new Property ("Name",
                        PropertyType.STRING,
                        name));
            }
            if (httpeq != null) {
                plist.add (new Property ("Httpequiv",
                        PropertyType.STRING,
                        httpeq));
            }
            if (content != null) {
                plist.add (new Property ("Content",
                        PropertyType.STRING,
                        content));
            }
            mdata.addMeta (new Property ("Meta",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        plist));
        }
    }

    /** Process metadata from an A element.  Only elements with an
     *  HREF attribute are of interest here.  We ignore links
     *  to anchors. */
    private static void processA (HtmlMetadata mdata, Attributes atts) 
    {
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("href".equals (attname)) {
                String link = attval;
                if (link.length() > 0 && link.charAt (0) != '#') {
                    mdata.addLink (link);
                }
                break;
            }
        }
    }
    
    /** Process metadata from the IMG element. */
    private static void processImg (HtmlMetadata mdata, Attributes atts)
    {
        String alt = null;
        String longdesc = null;
        String src = null;
        int height = -1;
        int width = -1;
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("alt".equals (attname)) {
                alt = attval;
            }
            else if ("src".equals (attname)) {
                src = attval;
            }
            else if ("longdesc".equals (attname)) {
                longdesc = attval;
            }
            else if ("height".equals (attname)) {
                try {
                    height = Integer.parseInt(attval);
                }
                catch (Exception e) {}
            }
            else if ("width".equals (attname)) {
                try {
                    width = Integer.parseInt(attval);
                }
                catch (Exception e) {}
            }
        }
        List plist = new ArrayList (5);
        if (alt != null) {
            plist.add (new Property ("Alt",
                    PropertyType.STRING,
                    alt));
        }
        if (longdesc != null) {
            plist.add (new Property ("Longdesc",
                    PropertyType.STRING,
                    longdesc));
        }
        if (src != null) {
            plist.add (new Property ("Src",
                    PropertyType.STRING,
                    src));
        }
        if (height >= 0) {
            plist.add (new Property ("Height",
                    PropertyType.INTEGER,
                    new Integer (height)));
        }
        if (width >= 0) {
            plist.add (new Property ("Width",
                    PropertyType.INTEGER,
                    new Integer (width)));
        }
        if (!plist.isEmpty ()) {
            mdata.addImage(new Property ("Image",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    plist));
        }
    }
    

    /** Process metadata from the FRAME element. */
    private static void processFrame (HtmlMetadata mdata, Attributes atts)
    {
        String name = null;
        String title = null;
        String src = null;
        String longdesc = null;
        int height = -1;
        int width = -1;
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("name".equals (attname)) {
                name = attval;
            }
            else if ("title".equals (attname)) {
                title = attval;
            }
            else if ("src".equals (attname)) {
                src = attval;
            }
            else if ("longdesc".equals (attname)) {
                longdesc = attval;
            }
        }
        List plist = new ArrayList (4);
        if (name != null) {
            plist.add (new Property ("Name",
                    PropertyType.STRING,
                    name));
        }
        if (title != null) {
            plist.add (new Property ("Title",
                    PropertyType.STRING,
                    title));
        }
        if (longdesc != null) {
            plist.add (new Property ("Longdesc",
                    PropertyType.STRING,
                    longdesc));
        }
        if (src != null) {
            plist.add (new Property ("Src",
                    PropertyType.STRING,
                    src));
        }
        if (!plist.isEmpty ()) {
            mdata.addFrame(new Property ("Frame",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    plist));
        }
    }

    /** Process metadata from the SCRIPT element. */
    private static void processScript (HtmlMetadata mdata, Attributes atts)
    {
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("type".equals (attname)) {
                String stype = attval;
                if (stype.length() > 0 ) {
                    mdata.addScript (stype);
                }
            }
        }
    }

    /** Processes metadata from the ABBR element.
     *  This will require the PCdata as well as the attributes,
     *  so we deposit the Property temporarily in the Metadata.
     */
    private static void processAbbr (HtmlMetadata mdata, Attributes atts)
    {
        List lst = new ArrayList (2);
        Property p = new Property ("abbr",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            lst);
        for (int i = 0; i < atts.getLength (); i++) {
            String attname = atts.getLocalName (i);
            String attval = atts.getValue (i);
            if ("title".equals (attname)) {
                if (attval.length() > 0 ) {
                    lst.add (new Property ("title",
                            PropertyType.STRING,
                            attval));
                }
                // Note: The PCData should be stuck at the
                // front of the list when we get it, as
                // the "abbr" property.
            }
        }
        mdata.setPropUnderConstruction (p);
    }
    
    /** Processes metadata from the TITLE element.
     *  This will require PCData, so we deposit the Property
     *  temporarily in the Metadata.
     */
    private static void processTitle (HtmlMetadata mdata, Attributes atts)
    {
        Property p = new Property ("title",
            PropertyType.STRING,
            "");               // store property with placeholder value
        mdata.setPropUnderConstruction (p);
    }
    
    /** Processes metadata from the CITE element.
     *  This will require PCData, so we deposit the Property
     *  temporarily in the Metadata.
     */
    private static void processCite (HtmlMetadata mdata, Attributes atts)
    {
        Property p = new Property ("cite",
            PropertyType.STRING,
            "");               // store property with placeholder value
        mdata.setPropUnderConstruction (p);
    }

}
