/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2009 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;

/**
 * Repository for an HTML document's metadata.
 * Also hold some state information, so that properties involving
 * tags, attributes and pcdata can be constructed.
 *
 * @author Gary McGath
 *
 */
public class HtmlMetadata {

    private String _title;
    private String _lang;
    private List _meta;
    private String _charset;
    private TreeSet _languages;
    private List _links;
    private List _images;
    private List _citations;
    private List _defs;
    private List _frames;
    private List _scripts;
    private List _abbrs;
    private TreeSet _entities;
    private Property _propUnderConstruction;

    /** Object for tracking UTF8 blocks. */
    private Utf8BlockMarker utf8BM;

    /** Constructor.  Initializes to the empty state. */    
    public HtmlMetadata ()
    {
        // Mostly sets variables to their defaults; it's good
        // documentation practice.  Lists are set to null until
        // there's actually something to add to them; this guarantees
        // that toProperty() doesn't have to deal with empty lists.
        _title = null;
        _lang = null;
        _meta = null;
        _charset = null;
        _links = null;
        _images = null;
        _citations = null;
        _defs = null;
        _frames = null;
        _scripts = null;
        _entities = null;
        _languages = null;
        _propUnderConstruction = null;
        utf8BM = new Utf8BlockMarker ();
    }
    
    /** Stores the contents of the TITLE element. */
    public void setTitle (String title)
    {
        _title = title;
    }
    
    /** Stores the language defined in the HTML element. */
    public void setLanguage (String lang)
    {
        _lang = lang;
    }
    
    /** Add a language defined in an attribute of any element
     *  except the HTML element. */
    public void addLanguage (String lang) 
    {
        if (!lang.equals(_lang)) {
            if (_languages == null) {
                _languages = new TreeSet ();
            }
            _languages.add (lang);
        }
    }
    
    /** Adds a CITE element's pcdata to the Citations property. */
    public void addCitation (String text)
    {
        if (_citations == null) {
            _citations = new LinkedList ();
        }
        _citations.add (text);
    }
    
    /** Adds a META tag's contents to the Meta property. */
    public void addMeta (Property prop) 
    {
        // We don't set _meta until there's a property;
        // thus, we guarantee it will never be an empty list.
        if (_meta == null) {
            _meta = new LinkedList ();
        }
        _meta.add (prop);
        
        // Is it a httpequiv=Content-Type ?
        String valContentType = extractHttpEquivValue(prop, "Content-Type");
        if (valContentType != null) {
            final String toSearch = "charset=";
            int indexOfCharset = valContentType.indexOf(toSearch);
            if (indexOfCharset != -1) {
                setCharset(valContentType.substring(indexOfCharset + toSearch.length()));
            }
        }
        // Is it a httpequiv=Content-Language ?
        String valContentLanguage = extractHttpEquivValue(prop, "Content-Language");
        if (valContentLanguage != null) {
            setLanguage(valContentLanguage);
        }
    }

    /**
     * Extract the content value associated with a given httpEquiv.
     * @param prop List containing the description of the meta tag
     * @param httpEquivValue the httpEquiv to consider
     * @return the content value
     */
    public String extractHttpEquivValue(Property prop, String httpEquivValue) {
        if (httpEquivValue == null) return null;
        String value = null;
        Property httpEquiv = prop.getByName("Httpequiv");
        if (httpEquiv != null &&
            PropertyArity.SCALAR.equals(httpEquiv.getArity()) &&
            PropertyType.STRING.equals(httpEquiv.getType())
        ) {
            String val = (String)httpEquiv.getValue();
            if (httpEquivValue.equalsIgnoreCase(val)) {
                // Look for charset in the Content property
                Property content = prop.getByName("Content");
                if (content != null &&
                    PropertyArity.SCALAR.equals(content.getArity()) &&
                    PropertyType.STRING.equals(content.getType())
                ) {
                    value = (String)content.getValue();
                }
            }
        }
        return value;
    }
    
    /** Stores the charset defined in the HTML element. */
    public void setCharset (String charset)
    {
        _charset = charset;
    }
    
    /** Adds a FRAME tag's contents to the Meta property. */
    public void addFrame (Property prop) 
    {
        // We don't set _frames until there's a property;
        // thus, we guarantee it will never be an empty list.
        if (_frames == null) {
            _frames = new LinkedList ();
        }
        _frames.add (prop);
    }
    
    /** Adds an ABBR tag's contents to the Meta property. */
    public void addAbbr (Property prop)
    {
        if (_abbrs == null) {
            _abbrs = new LinkedList ();
        }
        _abbrs.add (prop);
    }
    
    /** Adds a link to the Links property. */
    public void addLink (String link)
    {
        if (_links == null) {
            _links = new LinkedList ();
        }
        _links.add (link);
    }
    
    /** Adds an item to the Images property. */
    public void addImage (Property prop)
    {
        if (_images == null) {
            _images = new LinkedList ();
        }
        _images.add (prop);
    }
    
    /** Adds a defined term to the Defined Terms property. */
    public void addDef (String text)
    {
        if (_defs == null) {
            _defs = new LinkedList ();
        }
        _defs.add (text);
    }
    
    /** Adds the language of a SCRIPT element to the Scripts property. */
    public void addScript (String stype)
    {
        if (_scripts == null) {
            _scripts = new LinkedList ();
        }
        _scripts.add (stype);
    }
    
    /** Adds a String to the Entities property.  This property is a
     *  SortedSet, so duplicates are not added, and the resulting set
     *  can be iterated in alphabetical order. */
    public void addEntity (String entity)
    {
        if (_entities == null) {
            _entities = new TreeSet ();
        }
        _entities.add (entity);
    }
    
    /** Returns the UTF8BlockMarker for the metadata. */
    public Utf8BlockMarker getUtf8BlockMarker ()
    {
        return utf8BM;
    }
    
    /** Returns the contents of the TITLE element. */
    public String getTitle ()
    {
        return _title;
    }
    
    public String getCharset() {
        return _charset;
    }
    
    /** Converts the metadata to a Property. */
    public Property toProperty (TextMDMetadata _textMD)
    {
        List propList = new LinkedList ();
        Property val = new Property ("HTMLMetadata",
                                            PropertyType.PROPERTY,
                                            PropertyArity.LIST,
                                            propList);
        if (_lang != null) {
            propList.add (new Property ("PrimaryLanguage",
                    PropertyType.STRING,
                    _lang));
            if (_textMD != null) {
                _textMD.setLanguage(_lang);
            }
        }
        if (_languages != null) {
            propList.add (new Property ("OtherLanguages",
                    PropertyType.STRING,
                    PropertyArity.SET,
                    _languages));
        }
        if (_title != null) {
            propList.add (new Property ("Title",
                    PropertyType.STRING,
                    _title));
        }
        if (_meta != null) {
            // We're guaranteed that if _meta isn't null, it's non-empty.
            propList.add (new Property ("MetaTags",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _meta));
        }
        if (_frames != null) {
            propList.add (new Property ("Frames",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _frames));
        }
        if (_links != null) {
            propList.add (new Property ("Links",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    _links));
        }
        if (_scripts != null) {
            propList.add (new Property ("Scripts",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    _scripts));
        }
        if (_images != null) {
            propList.add (new Property("Images",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _images));
        }
        if (_citations != null) {
            propList.add (new Property("Citations",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    _citations));
        }
        if (_defs != null) {
            propList.add (new Property ("DefinedTerms",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    _defs));
        }
        if (_abbrs != null) {
            propList.add (new Property ("Abbreviations",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _abbrs));
        }
        if (_entities != null) {
            propList.add (new Property ("Entities",
                    PropertyType.STRING,
                    PropertyArity.SET,
                    _entities));
        }
        if (utf8BM != null) {
            Property p = utf8BM.getBlocksUsedProperty("UnicodeEntityBlocks");
            if (p != null) {
                propList.add (p);
            }
        }
        if (_textMD != null) {
             propList.add (new Property ("TextMDMetadata",
                     PropertyType.TEXTMDMETADATA, 
                     PropertyArity.SCALAR, 
                     _textMD));
        }
        
	if (propList.isEmpty ()) {
	    return null;
	}

        return val;
    }
    
    /** Sets a "property under construction".  This is generally
     *  called when an XML element is found, and the PCDATA must
     *  be incorporated into the property.
     */
    public void setPropUnderConstruction (Property p)
    {
        _propUnderConstruction = p;
    }
    
    /** Returns the "property under construction." */
    public Property getPropUnderConstruction ()
    {
        return _propUnderConstruction;
    }
    
    /** Adds PCDATA text to the property under construction.
     *  This may not all be provided in one lump, so it
     *  has to allow for multiple chunks. */
    public void addToPropUnderConstruction 
            (char[] ch, int start, int length)
    {
        if (_propUnderConstruction != null) {
            String argStr = new String (ch, start, length);
            String name = _propUnderConstruction.getName ();
            Object val = _propUnderConstruction.getValue ();
            if ("abbr".equals (name)) {
                // Theoretically, this can come in more than one
                // chunk, but a long abbreviation is moronic if
                // not oxymoronic.
                List propList = (List) _propUnderConstruction.getValue();
                Property abProp = new Property ("abbr",
                        PropertyType.STRING,
                        argStr);
                propList.add(0, abProp);
            }
            else if ("title".equals (name) ||
                     "dfn".equals (name)) {
                // For these properties, we just need to maintain
                // the String.  But to keep the design consistent and
                // simple, we maintain the Property and then just pull
                // out the String at the end.
                // A Property is immutable.  Rather than risk obscure
                // consequences from changing this assumption, we append
                // the text to a new Property.
                _propUnderConstruction = new Property (name,
                        PropertyType.STRING,
                        (String) val + argStr);
            }
        }
    }
    
    /** Finishes any property under construction.  This is called
     *  when an end element is encountered. */
    public void finishPropUnderConstruction ()
    {
        if (_propUnderConstruction != null) {
            String name = _propUnderConstruction.getName ();
            if ("abbr".equals(name)) {
                addAbbr (_propUnderConstruction);
            }
            else if ("title".equals (name)) {
                _title = (String) _propUnderConstruction.getValue ();
            }
            _propUnderConstruction = null;
        }
    }
}
