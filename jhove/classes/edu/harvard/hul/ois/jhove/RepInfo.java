/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.util.*;

/**
 *  This class encapsulates representation information, as defined 
 *  by ISO/IEC 14721, about a content stream.
 *
 *  @see <a href="http://wwwclassic.ccsds.org/documents/pdf/CCSDS-650.0-B-1.pdf">ISO/IEC
 *       14721 (PDF)</a>
 */
public class RepInfo implements Cloneable
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** List of checksums. */
    private List<Checksum> _checksum;

    /** Consistency flag. */
    private boolean _consistent;

    /** Validity flag.  A ternary variable which can have a value
     *  of TRUE, FALSE, or UNDETERMINED. */
    private int _valid;
    
    /** Values for _valid */
    public final static int
        TRUE = 1,
        FALSE = 0,
        UNDETERMINED = -1;

    /** Creation date. */
    private Date _created;

    /** External representation information. */
    private RepInfo _external;

    /** Format identifier. */
    private String _format;

    /** Modification date. */
    private Date _lastModified;

    /** List of diagnostic and informative messages. */
    private List<Message> _message;

    /** MIME media type. */
    private String _mimeType;

    /** The module used to populate this representation information. */
    private Module _module;

    /** List of conforming format profiles. */
    private List<String> _profile;
    
    /** List of modules for which signature matches. */
    private List<String> _sigMatch;

    /** Associative map of module-specific representation information. */
    private Map<String, Property> _property;

    /** Object size. */
    private long _size;

    /** Object file pathname or URI. */
    private String _uri;
    
    /** Flag indicating _uri is a URL if true. */
    private boolean _urlFlag;

    /** Well-formed flag. A ternary variable which can have a value
     *  of TRUE, FALSE, or UNDETERMINED. */
    private int _wellFormed;

    /** Version of format which applies. */
    private String _version;

    /** Note. */
    private String _note;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a RepInfo with a URI reference
     *
     *  @param uri   Object file pathname or URI
     */
    public RepInfo (String uri)
    {
	init (uri);
    }

    /**
     *  Creates a RepInfo with a URI reference and an external RepInfo.
     * 
     *  By default, urlFlag is <code>false</code>.
     *
     *  @param uri       Object file pathname or URI
     *  @param external  External representation information
     */
    public RepInfo (String uri, RepInfo external)
    {
	init (uri);
	_external = external;
    }

    private void init (String uri)
    {
        _uri = uri;
        _size = -1;
        _wellFormed = TRUE;
        _consistent = true;
        _urlFlag = false;
        _valid = TRUE;
        
        _checksum = new ArrayList<Checksum> ();
        _message  = new ArrayList<Message> ();
        _profile  = new ArrayList<String> ();
        _property = new TreeMap<String, Property> ();
        _sigMatch = new ArrayList<String> ();
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Clones the RepInfo one level deep, making fresh copies
     *  of the checksum, message, profile, signature match, 
     *  and property fields.
     *  The external RepInfo (if any) is not cloned, but
     *  is attached directly to the clone.
     */
    public Object clone () 
    {
	RepInfo newri;
	try {
	    newri = (RepInfo) super.clone ();
	}
	catch (CloneNotSupportedException e) {
	    return null;   // should never happen
	}

        newri._checksum = new ArrayList<Checksum> (_checksum);
        newri._message = new ArrayList<Message>(_message);
        newri._profile = new ArrayList<String> (_profile);
        newri._sigMatch = new ArrayList<String> (_sigMatch);
        newri._property = new TreeMap<String, Property> (_property);
        
        return (Object) newri;
    }

    /**
     *  Copies all the information out of the parameter object.
     *  This is a "shallow" copy; it is assumed that the parameter
     *  object is a temporary one that will not be further modified.
     */
    public void copy (RepInfo info)
    {
        _checksum = info._checksum;
        _consistent = info._consistent;
        _created = info._created;
        _external = info._external;
        _format = info._format;
        _lastModified = info._lastModified;
        _message = info._message;
        _mimeType = info._mimeType;
        _profile = info._profile;
        _property = info._property;
        _size = info._size;
        _uri = info._uri;
        _urlFlag = info._urlFlag;
        _wellFormed = info._wellFormed;
        _valid = info._valid;
        _version = info._version;
        _note = info._note;
        _module = info._module;
        _sigMatch = info._sigMatch;
    }

    /******************************************************************
     *
     * Accessor methods.
     ******************************************************************/

    /**
     *   Returns this object's list of Checksums
     */
    public List<Checksum> getChecksum ()
    {
        return _checksum;
    }

    /**
     *   Returns the creation date stored in this object. A creation
     *   date is not automatically generated, but must be explicitly
     *   stored.
     **/
    public Date getCreated ()
    {
        return _created;
    }

    /**
     *   Return the format identifier
     */
    public String getFormat ()
    {
        return _format;
    }

    /**
     *   Returns the last modified date stored in this object. A
     *   date is not automatically generated, but must be explicitly
     *   stored.
     **/
    public Date getLastModified ()
    {
        return _lastModified;
    }

    /**
     *  Returns the message list stored in this object
     */
    public List<Message> getMessage ()
    {
        return _message;
    }

    /**
     *  Returns the MIME type string stored in this object
     */
    public String getMimeType ()
    {
        return _mimeType;
    }

    /**
     * Return the module.
     */
    public Module getModule ()
    {
        return _module;
    }

    /**
     *  Returns the list of profiles (Strings) stored in this object
     */
    public List<String> getProfile ()
    {
        return _profile;
    }

    /**
     *  Returns the Property map stored in this object.  The
     *  Property map contains key-value pairs whose key is a 
     *  <code>String</code> and whose value is a <code>Property</code>.
     */
    public Map<String, Property> getProperty ()
    {
        return _property;
    }

    /**
     *  Returns a named Property from the Property map
     *
     *  @param name  The name of the Property.
     */
    public Property getProperty (String name)
    {
        Property property = null;
        if (_property.size () > 0) {
            property = (Property) _property.get (name);
        }

	return property;
    }

    /**
     *  Returns the size property stored in this object.
     */
    public long getSize ()
    {
        return _size;
    }

    /**
     *  Returns the URI property stored in this object.
     */
    public String getUri ()
    {
        return _uri;
    }

    /**
     *  Returns a flag which, if <code>true</code>, indicates
     *  the object is a URL.
     */
    public boolean getURLFlag ()
    {
        return _urlFlag;
    }

    /**
     *  Returns the value of the consistency flag.
     */
    public boolean isConsistent ()
    {
        return _consistent;
    }

    /**
     *  Returns the value of the well-formed flag.
     *  Can return TRUE, FALSE, or UNDETERMINED.
     */
    public int getWellFormed ()
    {
        return _wellFormed;
    }

    /**
     *  Returns the value of the validity flag.
     *  Can return TRUE, FALSE, or UNDETERMINED.
     */
    public int getValid ()
    {
        return _valid;
    }

    /**
     *  Returns the version property stored in this object
     */
    public String getVersion ()
    {
	return _version;
    }

    /**
     *  Returns the note property stored in this object
     */
    public String getNote ()
    {
	return _note;
    }
    
    /**
     *  Returns the list of matching signatures.  
     *  JhoveBase will make this value persistent across
     *  module invocations for a given document, so the list
     *  returned will reflect all modules that have looked
     *  at the document so far.
     */
    public List<String> getSigMatch ()
    {
        return _sigMatch;
    }

    /**
     * Return property by name, regardless of its position in the
     * property hierarchy.
     * @param name Property name
     * @return Named property (or null)
     */
    public Property getByName (String name)
    {
        Property prop = null;

        Collection<Property> coll = _property.values ();
        Iterator<Property> iter = coll.iterator ();
        while (iter.hasNext ()) {
            prop = (Property) iter.next ();
            if ((prop = prop.getByName (name)) != null) {
                break;
            }
        }

        return prop;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /**
     *  Append a Checksum object to the checksum list.
     */
    public void setChecksum (Checksum checksum)
    {
        _checksum.add (checksum);
    }

    /**
     *  Set the value of the consistency flag
     */
    public void setConsistent (boolean consistent)
    {
	_consistent = consistent;
    }

    /**
     *  Set the creation date
     */
    public void setCreated (Date created)
    {
	_created = created;
    }

    /**
     *  Set the format identifier
     */
    public void setFormat (String format)
    {
	_format = format;
    }

    /**
     *  Set the last modified date
     */
    public void setLastModified (Date lastModified)
    {
        _lastModified = lastModified;
    }

    /**
     *  Append a Message object to the message list
     */
    public void setMessage (Message message)
    {
        _message.add (message);
    }

    /**
     *  Set the MIME type string
     */
    public void setMimeType (String mimeType)
    {
        _mimeType = mimeType;
    }

    /**
     * Add the module.
     */
    public void setModule (Module module)
    {
        _module = module;
    }

    /**
     *  Append a profile String to the profile list
     */
    public void setProfile (String profile)
    {
        _profile.add (profile);
    }

    /**
     *   Add a Property to the property map.  The name of the Property
     *   becomes its key in the map.
     */
    public void setProperty (Property property)
    {
        _property.put (property.getName (), property);
    }

    /**
     *  Set the size property
     */
    public void setSize (long size)
    {
        _size = size;
    }
    
    /**
     *  Set the flag to indicate whether this is a URL (true)
     *  or a file (false)
     */
    public void setURLFlag (boolean flag)
    {
        _urlFlag = flag;
    }

    /**
     *  Set the well-formed flag
     * 
     *  @param wellFormed    Boolean argument that maps to
     *                  an integer value:
     *                  true maps to TRUE, and false to FALSE.
     */
    public void setWellFormed (boolean wellFormed) 
    {
        _wellFormed = wellFormed ? TRUE : FALSE;
        if (!wellFormed) {
            _consistent = false;
            _valid = FALSE;
        }
    }

    /**
     *  Set the wellFormed flag.
     *  Setting wellFormed to false forces the consistent and
     *  valid flags to be false as well.
     */
    public void setWellFormed (int wellFormed)
    {
        _wellFormed = wellFormed;
	if (wellFormed == FALSE) {
	    _consistent = false;
	    _valid = FALSE;
	}
        if (wellFormed == UNDETERMINED) {
            _valid = UNDETERMINED;
        }
    }

    /**
     *  Set the validity flag
     * 
     *  @param valid    Boolean argument that maps to
     *                  an integer value:
     *                  true maps to TRUE, and false to FALSE.
     */
    public void setValid (boolean valid) 
    {
        _valid = valid ? TRUE : FALSE;
    }

    /**
     *  Set the validity flag
     * 
     *  @param valid    Permitted values are TRUE, FALSE, AND
     *                  UNDETERMINED.  The effect of using 
     *                  other values is undefined.
     */
    public void setValid (int valid) 
    {
        _valid = valid;
    }

    /**
     *  Set the version string
     */
    public void setVersion (String version) 
    {
        _version = version;
    }

    /**
     *  Set the note string
     */
    public void setNote (String note)
    {
	_note = note;
    }
    
    /** Adds the name of a module, signifying that the document
     *  signature matched the module's requirements.
     *  JhoveBase will make this value persistent across
     *  module invocations for a given document.
     */
    public void setSigMatch (String modname)
    {
        _sigMatch.add (modname);
    }
    
    /** Adds a list of module names, signifying that the document
     *  signature matched the module's requirements.
     *  Any previous list is lost.
     *  JhoveBase will make this value persistent across
     *  module invocations for a given document.
     */
    public void setSigMatch (List<String> modnames)
    {
        _sigMatch = modnames;
    }

    /******************************************************************
     * Serialization methods.
     ******************************************************************/

    /**
     *  Output the information in this object.  The format and 
     *  destination of the output are determined by the
     *  OutputHandler.
     */
    public void show (OutputHandler handler)
    {
	handler.analyze (this);
	handler.show    (this);
    }
}
