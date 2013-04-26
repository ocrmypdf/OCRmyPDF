/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;
import java.text.*;
import java.util.*;
import java.util.logging.*;

/**
 *  Abstract base class for Jhove output handlers.
 *  Output handlers should normally subclass HandlerBase.
 */
public abstract class HandlerBase
    implements OutputHandler
{
    /******************************************************************
     * PUBLIC CLASS FIELDS.
     ******************************************************************/

    /**
     *  A DateFormat for representing a Date in yyyy-MM-dd 
     *  (e.g., 2003-07-31) format.
     */
    public static SynchronizedDateFormat date =
              new SynchronizedDateFormat ("yyyy-MM-dd");
    
    /**
     *  A DateFormat for representing a Date in yyyy-MM-dd HH:mm:ss z
     *  (e.g., 2003-07-31 15:31:12 EDT) format.
     */
    public static SynchronizedDateFormat dateTime =
              new SynchronizedDateFormat ("yyyy-MM-dd HH:mm:ss z");

    /**
     *  A DateFormat for representing a Date in ISO 8601
     *  (e.g., 2003-07-31T15:31:12-0400) format.
     *  We subclass SimpleDateFormat to make it thread-safe.
     */
    public static SynchronizedDateFormat iso8601 =
              new SynchronizedDateFormat ("yyyy-MM-dd'T'HH:mm:ssZ");

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /**  The application object */
    protected App _app;
    /**  The Jhove engine */
    protected JhoveBase _base;
    /**  Handler last modification date */
    protected Date _date;
    /**  Character encoding for writer */
    protected String _encoding;
    /** Initialization value. */
    protected String _init;
    /** List of default parameters. */
    protected List<String> _defaultParams;
    /**  JHOVE engine. */
    protected JhoveBase _je;
    /**  Indentation level */
    protected int _level;
    /**  Handler name */
    protected String _name;
    /**  Handler note */
    protected String _note;
    /**  Handler release description. */
    protected String _release;
    /** Handler-specific parameter. */
    protected String _param;
    /**  Copyright notice */
    protected String _rights;
    /**  Handler specification document list */
    protected List<Document> _specification;
    /**  Handler vendor */
    protected Agent _vendor;
    /**  Writer for doing output */
    protected PrintWriter _writer;
    /** Logger for a handler class. */
    protected Logger _logger;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *   Constructors of all subclasses of HandlerBase should call
     *   this as a <code>super</code> constructor.
     *
     *   @param name            Name of the handler
     *   @param release         Release identifier
     *   @param date            Last modification date of the handler code,
     *                          in the form of an array of three numbers.
     *                          <code>date[0]</code> is the year, 
     *                          <code>date[1]</code> the month, and
     *                          <code>date[2]</code> the day.
     *   @param note            Additional information about the handler
     *                          (may be null)
     *   @param rights          Copyright notice for the handler
     */
    protected HandlerBase (String name, String release, int [] date,
                           String note, String rights)
    {
        // Though we're actually in the jhove package, all the related
        // action logically belongs in the handler package, so we name
        // this logger accordingly.
        _logger = Logger.getLogger ("edu.harvard.hul.ois.jhove.handler");
        _logger.info ("Initializing " + name);
        _name    = name;
        _release = release;
	_encoding = "UTF-8";

        Calendar calendar = new GregorianCalendar ();
        calendar.set (date[0], date[1]-1, date[2]);
        _date = calendar.getTime ();

        _note   = note;
        _rights = rights;
        _specification = new ArrayList<Document> ();

        _level = -1;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Initialization methods.
     ******************************************************************/

    /**
     * Reset the handler. This needs to be called before each invocation.
     */
    public void reset () {
        _level = -1;
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
     * Per-instantiation initialization.
     * The default method does nothing.
     */
    public void init (String init)
        throws Exception
    {
	_init = init;
    }

    /**
     * Per-action initialization.
     * The default method does nothing.
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
     *  Return the last modification date of this OutputHandler, as a
     *  Java Date object
     */
    public final Date getDate ()
    {
        return _date;
    }

    /**
     *  Return the OutputHandler name
     */
    public final String getName ()
    {
        return _name;
    }

    /**
     *  Return the OutputHandler note
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
     *   Return the copyright information string
     */
    public final String getRights ()
    {
        return _rights;
    }

    /**
     *  Returns a list of <code>Document</code> objects (one for each 
     *  specification document).  The specification
     *  list is generated by the OutputHandler, and specifications cannot
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
     *  Returns this handler's encoding.
     */
    public String getEncoding ()
    {
	return _encoding;
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
     *  Assigns the JHOVE engine object to provide services to this handler
     */
    public final void setBase (JhoveBase je)
    {
        _je = je;
    }

    /**
     *  Assigns the encoding to be used by this OutputHandler
     */
    public void setEncoding (String encoding)
    {
	_encoding = encoding;
    }

    /**
     *  Assigns a PrintWriter to do output for this OutputHandler
     */
    public final void setWriter (PrintWriter writer)
    {
        _writer = writer;
    }

    /******************************************************************
     * Serialization methods.
     ******************************************************************/

    /**
     * Callback allowing post-parse, pre-show analysis of object
     * representation information.
     * @param info Object representation information
     */
    public void analyze (RepInfo info)
    {
	/* Do nothing, which is sufficient for most handlers. */
    }

    /**
     * Callback indicating a directory is finished being processed.
     */
    public void endDirectory ()
    {
	/* Do nothing, which is sufficient for most handlers. */
    }

    /**
     * Callback to give the handler the opportunity to decide whether or
     * not to process a file.  Most handlers will always return true.
     * @param filepath File pathname
     */
    public boolean okToProcess (String filepath)
    {
	return true;
    }

    /**
     *  Outputs information about a Module
     */
    public abstract void show (Module module);

    /**
     *  Outputs the information contained in a RepInfo object
     */
    public abstract void show (RepInfo info);

    /**
     *  Outputs information about the OutputHandler specified
     *  in the parameter 
     */
    public abstract void show (OutputHandler handler);

    /**
     *  Outputs minimal information about the application
     */
    public abstract void show ();

    /**
     *  Outputs detailed information about the application,
     *  including configuration, available modules and handlers,
     *  etc.
     */
    public abstract void show (App app);

    /**
     *  Do the initial output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. 
     */
    public abstract void showHeader ();

    /**
     *  Do the final output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. 
     */
    public abstract void showFooter ();
    
    /**
     *  Close the writer after all output has been done.
     */
    public void close ()
    {
        _writer.close ();
    }

    /**
     * Callback indicating a new directory is being processed.
     * @param directory Directory path
     */
    public void startDirectory (String directory)
    {
	/* Do nothing, which is sufficient for most handlers. */
    }

    /******************************************************************
     * PRIVATE CLASS METHODS.
     *
     * XML methods.
     ******************************************************************/

    /**
     * Return the XML DOCTYPE instruction.
     * @param root Root element of the DTD
     * @param uri  URI of the DTD
     */
    protected static String doctype (String root, String uri)
    {
	return doctype (root, null, uri);
    }

    /**
     * Return the XML DOCTYPE instruction.
     * @param root Root element of the DTD
     * @param name Public name of the DTD
     * @param uri  URI of the DTD
     */
    protected static String doctype (String root, String name, String uri)
    {
	StringBuffer s = new StringBuffer ("<!DOCTYPE " + root);
	if (name != null) {
	    s.append (" PUBLIC \"" + name + "\" \"");
	}
	else {
	    s.append (" SYSTEM \"");
	}
	s.append (uri + "\">");

	return s.toString ();
    }

    /**
     * Returns, as a String, an empty XML.
     *
     * @param tag XML tag
     */
    protected static String element (String tag)
    {
        return "<" + tag + "/>";
    }

    /**
     *  Returns, as a String, an XML element with a given tag and content
     *
     *  @param tag      An XML tag
     *  @param content  Content string.  Characters requiring
     *                  conversion to entitites will be converted.
     */
    protected static String element (String tag, String content)
    {
        return elementStart (tag) + encodeContent (content) + elementEnd (tag);
    }

    /**
     *  Returns, as a String,
     *  an XML element with a given tag and attributes
     *
     *  @param tag      An XML tag
     *  @param attrs    An array of String[2] elements, where for each
     *                  element, attrs[i][0] is the attribute key and
     *                  attrs[i][1] is the attribute value.
     *                  Null values are skipped.
     */
    protected static String element (String tag, String [][] attrs)
    {
        StringBuffer buffer = new StringBuffer ("<");
        buffer.append (tag);
        for (int i=0; i<attrs.length; i++) {
			if (attrs[i][0] != null && attrs[i][1] != null) {
				buffer.append (" ");
				buffer.append (attrs[i][0]);
				buffer.append ("=\"");
				buffer.append (encodeValue (attrs[i][1]));
				buffer.append ("\"");
			}
        }
        buffer.append ("/>");

        return buffer.toString ();
    }

    /**
     *  Returns, as a String,
     *  an XML element with a given tag, content and attributes
     *
     *  @param tag      An XML tag
     *  @param content  Content string.  Characters requiring
     *                  conversion to entitites will be converted.
     *  @param attrs    An array of String[2] elements, where for each
     *                  element, attrs[i][0] is the attribute key and
     *                  attrs[i][1] is the attribute value.
     *                  Null values are skipped.
     *
     */
    protected static String element (String tag, String [][] attrs,
                                     String content)
    {
        StringBuffer buffer = new StringBuffer ("<");
        buffer.append (tag);
        for (int i=0; i<attrs.length; i++) {
			if (attrs[i][0] != null && attrs[i][1] != null) {
				buffer.append (" ");
				buffer.append (attrs[i][0]);
				buffer.append ("=\"");
				buffer.append (encodeValue (attrs[i][1]));
				buffer.append ("\"");
			}
        }
        buffer.append (">");
        buffer.append (encodeContent (content));
        buffer.append (elementEnd (tag));

        return buffer.toString ();
    }

    /**
     *   Returns, as a String, the closing tag of an element.  
     *   No checking is done that opening and closing tags match.
     *
     *  @param tag      An XML tag
     */
    protected static String elementEnd (String tag)
    {
        return "</" + tag + ">";
    }

    /**
     *  Returns, as a String, the opening tag of an element.
     *
     *  @param tag      An XML tag
     */
    protected static String elementStart (String tag)
    {
        return "<" + tag + ">";
    }

    /**
     *   Returns, as a String, the opening tag of an element with
     *   specified attributes.
     *
     *  @param tag      An XML tag
     *  @param attrs    An array of String[2] elements, where for each
     *                  element, attrs[i][0] is the attribute key and
     *                  attrs[i][1] is the attribute value.
     */
    protected static String elementStart (String tag, String [][] attrs)
    {
        StringBuffer buffer = new StringBuffer ("<");
        buffer.append (tag);
        for (int i=0; i<attrs.length; i++) {
            buffer.append (" ");
            buffer.append (attrs[i][0]);
            buffer.append ("=\"");
            buffer.append (encodeValue (attrs[i][1]));
            buffer.append ("\"");
        }
        buffer.append (">");

        return buffer.toString ();
    }

    /**
     *   Encodes a content String in XML-clean form, converting characters
     *   to entities as necessary and removing control characters disallowed
     *   by XML.  The null string will be converted to an empty string.
     */
    private static String encodeContent (String content)
    {
        if (content == null) {
            content = "";
        }
        StringBuffer buffer = new StringBuffer (content);

	/* Remove disallowed control characters from the content string. */
        int n = buffer.length ();
	for (int i=0; i<n; i++) {
	    char ch = buffer.charAt (i);
	    if ((0x00 <= ch && ch <= 0x08) || (0x0b <= ch && ch <= 0x0c) ||
		(0x0e <= ch && ch <= 0x1f) ||  0x7f == ch) {
		buffer.deleteCharAt (i--);
		n--;
	    }
	}
	n = 0;
        while ((n = buffer.indexOf ("&", n)) > -1) {
            buffer.insert (n+1, "amp;");
            n +=5;
        }
        n = 0;
        while ((n = buffer.indexOf ("<", n)) > -1) {
            buffer.replace (n, n+1, "&lt;");
            n += 4;
        }
        n = 0;
        while ((n = buffer.indexOf (">", n)) > -1) {
            buffer.replace (n, n+1, "&gt;");
            n += 4;
        }

        return buffer.toString ();
    }

    /**
     *   Encodes an attribute value String in XML-clean form, 
     *   converting quote characters to entities and removing control
     *   characters disallowed by XML.
     */
    private static String encodeValue (String value)
    {
        StringBuffer buffer = new StringBuffer (value);

	/* Remove disallowed control characters from the value string. */
        int n = buffer.length ();
	for (int i=0; i<n; i++) {
	    char ch = buffer.charAt (i);
	    if ((0x00 <= ch && ch <= 0x08) || (0x0b <= ch && ch <= 0x0c) ||
		(0x0e <= ch && ch <= 0x1f) ||  0x7f == ch) {
		buffer.deleteCharAt (i--);
		n--;
	    }
	}
	    // [CC], escape &, < and > characters which are disallowed in xml
        n = 0;
        while ((n = buffer.indexOf ("&", n)) > -1) {
            buffer.insert (n+1, "amp;");
            n +=5;
        }
     	n = 0;
        while ((n = buffer.indexOf ("<", n)) > -1) {
            buffer.replace (n, n+1, "&lt;");
            n += 4;
        }
        n = 0;
        while ((n = buffer.indexOf (">", n)) > -1) {
            buffer.replace (n, n+1, "&gt;");
            n += 4;
        }
		n = 0;
        while ((n = buffer.indexOf ("\"", n)) > -1) {
            // [LP] fix for invalid escaping, "" quotes were accidentally left in place.
            buffer.replace (n, n+1, "&quot;");
            n +=7;
        }

        return buffer.toString ();
    }

    /**
     *  Return a canonical XML declaration with default encoding.
     */
    protected static String xmlDecl ()
    {
        return "<?xml version=\"1.0\"?>";
    }

    /**
     *  Return a canonical XML declaration with specified encoding.
     */
    protected static String xmlDecl (String encoding)
    {
        return "<?xml version=\"1.0\" encoding=\"" +
                encoding +
                "\"?>";
    }

    /******************************************************************
     * Nesting level methods.
     ******************************************************************/

    /**
     *   Returns a String containing a number of spaces equal
     *   to the current indent level.
     */
    protected static String getIndent (int level)
    {
        StringBuffer s = new StringBuffer ();
        for (int i=0; i<level; i++) {
            s.append (" ");
        }

        return s.toString ();
    }

    /******************************************************************
     * Array methods.
     ******************************************************************/

    /**
     * Return String representation of an integer array.
     */
    protected static String integerArray (int [] iarray)
    {
    	return integerArray (iarray, ' ');
    }
    
    /**
     * Return String representation of an integer array with
     * specified separator.
     */
    protected static String integerArray (int [] iarray, char separator)
    {
        StringBuffer buffer = new StringBuffer ();
        for (int i=0; i<iarray.length; i++) {
            if (i > 0) {
                buffer.append (separator);
            }
            buffer.append (Integer.toString (iarray[i]));
        }
        return buffer.toString ();
    }

    /**
     * Return String representation of an array of long with
     * space separator.
     */
    protected static String longArray (long [] larray)
    {
        StringBuffer buffer = new StringBuffer ();
        for (int i=0; i<larray.length; i++) {
            if (i > 0) {
                buffer.append (" ");
            }
            buffer.append (Long.toString (larray[i]));
        }
        return buffer.toString ();
    }

    /**
     * Return String representation of an array of Rational, each evaluated
     * as a double, with space separator.
     */
    protected static String rationalArray (Rational [] rarray)
    {
        StringBuffer buffer = new StringBuffer ();
        for (int i=0; i<rarray.length; i++) {
            if (i > 0) {
                buffer.append (" ");
            }
            buffer.append (rarray[i].toDouble ());
        }
        return buffer.toString ();
    }


    /**
     * Return String representation of an array of Rational, each as
     * two integers, with space separator.
     */
    protected static String rationalArray10 (Rational [] rarray)
    {
	StringBuffer buffer = new StringBuffer ();
	for (int i=0; i<rarray.length; i++) {
	    if (i > 0) {
		buffer.append (" ");
	    }
	    buffer.append (rarray[i].getNumerator ());
	    buffer.append (" ");
	    buffer.append (rarray[i].getNumerator ());
	}
	return buffer.toString ();
    }

    /**
     * Return String representation of an array of double.
     */
    protected static String doubleArray (double [] darray)
    {
        StringBuffer buffer = new StringBuffer ();
        for (int i=0; i<darray.length; i++) {
            if (i > 0) {
                buffer.append (" ");
            }
            buffer.append (Double.toString (darray[i]));
        }
        return buffer.toString ();
    }


    /* Text formatting methods. */
    /* Convert a date to the dateTime format used by the
     * XML schema.  This is ISO 8610 with a colon between
     * the hour and minute fields of the time zone.  Unfortunately,
     * SimpleDateFormat generates the time zone without the
     * colon; this also conforms to 8601, but doesn't conform
     * to the schema, so we have to diddle it.
     */
    protected String toDateTime (Date date)
    {
        String isoStr = iso8601.format (date);
	// We can't directly use a SimpleDateFormat, because
	// the 'z' field gives us the colonless time zone.
        int len = isoStr.length ();
	// Add the colon before the last two characters.
        return isoStr.substring (0, len - 2) +
		":" +
		isoStr.substring (len - 2);
    }
    
    /** A DateFormat class to address an issue of thread safety. */
    public static class SynchronizedDateFormat extends SimpleDateFormat
        {
            public SynchronizedDateFormat(String pattern) {
                super(pattern);
            }
            public synchronized StringBuffer format(Date date,
                                    StringBuffer toAppendTo, FieldPosition pos) {
                return super.format(date, toAppendTo, pos);
            }
      }

}
