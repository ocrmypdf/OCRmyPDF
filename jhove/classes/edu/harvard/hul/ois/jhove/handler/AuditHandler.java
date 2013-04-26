/**********************************************************************
 * Audit output handler
 * Copyright 2004 by the President and Fellows of Harvard College
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

package edu.harvard.hul.ois.jhove.handler;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.handler.audit.*;
import java.util.*;

/**
 * JHOVE audit output handler, derived from the standard JHOVE XML
 * handler.  It is expected that this class will be used as the parent for
 * other, more interesting output handlers.  Subclasses should override the
 * implementations of the Impl methods, e.g., endDirectoryImpl ().
 * @see <a href="http://hul.harvard.edu/jhove/using.html#xml-hul">JHOVE
 * XML output handler</a>
 */
public class AuditHandler
    extends XmlHandler
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** Audit output handler name. */
    private static final String NAME = "Audit";

    /** Audit output handler release ID. */
    private static final String RELEASE = "1.1";

    /** Audit output handler release date. */
    private static final int [] DATE = {2005, 04, 22};

    /** Audit output handler informative note. */
    private static final String NOTE =
        "This output handler is derived from the standard JHOVE XML output " +
        "handler.  It is intended to be used as the parent class for other, " +
	"more interesting handlers.";

    /** Audit output handler rights statement. */
    private static final String RIGHTS =
        "Copyright 2004-2005 by the President and Fellows of Harvard College. " +
        "Released under the GNU LGPL license";

    /*****************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Home directory of the audit. */
    protected String _home;

    /** Number of files processed by MIME type. */
    protected Map _mimeType;

    /** State map. */
    protected Map _stateMap;

    /** State stack. */
    protected Stack _stateStack;

    /** Initial time. */
    protected long _t0;

    /** Number of files audited. */
    protected int _nAudit;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Instantiate a <tt>AudiHandler</tt> object.
     */
    public AuditHandler ()
    {
        super (NAME, RELEASE, DATE, NOTE, RIGHTS);

	/* Define the standard output handler properties. */

        _name    = NAME;
        _release = RELEASE;
        Calendar calendar = new GregorianCalendar ();
        calendar.set (DATE[0], DATE[1]-1, DATE[2]);
        _date    = calendar.getTime ();
        _note    = NOTE;
        _rights  = RIGHTS;

	/* Initialize the handler. */

	_mimeType   = new TreeMap ();
	_stateMap   = new TreeMap ();
	_stateStack = new Stack ();
	_nAudit     = 0;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     * Callback indicating a directory is finished being processed.
     * Prop the state stack and place the current directory file count
     * into the directory hash.
     */
    public final void endDirectory ()
    {
	AuditState state = (AuditState) _stateStack.pop ();
	_stateMap.put (state.getDirectory (), state);

	endDirectoryImpl (state);
    }

    /**
     * Local extension to the standard callback indicating a directory is
     * finished being processed.
     * @param state Audit handler state
     */
    public void endDirectoryImpl (AuditState state)
    {
    }

    /**
     * Determine whether or not to process the file.
     * @param filepath File pathname 
     */
    public final boolean okToProcess (String filepath)
    {
	AuditState state = (AuditState) _stateStack.peek ();

	boolean ok = okToProcessImpl (filepath, state);
	if (!ok) {
	    state.setNotProcessed (state.getNotProcessed () + 1);
	}

	return ok;
    }

    /**
     * Local extension to standard callback that determines whether or not
     * to process the file.
     * @param filepath File pathname 
     * @param state Audit handler state
     */
    public boolean okToProcessImpl (String filepath, AuditState state)
    {
	return true;
    }

    /**
     *  Outputs the information contained in a RepInfo object
     * @param info Object representation information
     */
    public void show (RepInfo info)
    {
	AuditState state = (AuditState) _stateStack.peek ();

	/* If the file is not found, then no module is assigned in the
	 * RepInfo object.
	 */
	if (info.getModule () == null) {
	    state.setNotFound (state.getNotFound () + 1);

	    _writer.println ("<!-- file not found or not readable: " +
			     info.getUri () + " -->");
	}
	else {
	    String mime = info.getMimeType ();
	    AuditCount count = (AuditCount) _mimeType.get (mime);
	    if (count == null) {
		count = new AuditCount ();
	    }

	    int valid = info.getValid ();
	    if (valid == RepInfo.TRUE) {
		state.setValid (state.getValid () + 1);
		count.setValid (count.getValid () + 1);
	    }
	    else {
		state.setWellFormed (state.getWellFormed () + 1);
		count.setWellFormed (count.getWellFormed () + 1);
	    }
	    _mimeType.put (mime, count);
	}

	showImpl (info, state);
    }

    /**
     * Local extension to the standard callback that outputs the
     * information contained in a RepInfo object
     * @param info Object representation information
     * @param state Audit handler state
     */
    public void showImpl (RepInfo info, AuditState state)
    {
	String status = null;
	String mime = info.getMimeType ();
	if (mime != null) {
	    if (info.getWellFormed () == RepInfo.TRUE) {
		if (info.getValid () == RepInfo.TRUE) {
		    status = "valid";
		}
		else {
		    status = "well-formed";
		}
	    }
	    else {
		status = "not well-formed";
	    }
	}
	else {
	    status = "not found";
	}

	/* Retrieve the MD5 checksum, if available. */

	String md5 = null;
	List list = info.getChecksum ();
	int len = list.size ();
	for (int i=0; i<len; i++) {
	    Checksum checksum = (Checksum) list.get (i);
	    if (checksum.getType ().equals (ChecksumType.MD5)) {
		md5 = checksum.getValue ();
		break;
	    }
	}
	 
	if (_nAudit == 0) {
	    String margin = getIndent (++_level);

	    String [][] attrs = { {"home", _home} };
	    _writer.println (margin + elementStart ("audit", attrs));
	}

	String margn2 = getIndent (_level) + " ";

	String uri = info.getUri ();

	/* Change the URI to a relative path by removing the home
	 * directory prefix.
	 */
	int n = uri.indexOf (_home);
	if (n == 0) {
	    uri = uri.substring (_home.length () + 1);
	}
	String [][] attrs = { {"mime", mime }, {"status", status},
			      {"md5", md5} };
	_writer.println (margn2 + element ("file", attrs, uri));
	_nAudit++;
    }

    /**
     * Do the final output.  This should be in a suitable format for
     * including multiple files between the header and the footer, and
     * the XML of the header and footer must balance out.
     */
    public void showFooter ()
    {
	AuditState state = (AuditState) _stateStack.pop ();
	if (state.getTotal () > 0 || state.getNotFound () > 0) {
	    _stateMap.put (state.getDirectory (), state);
	}

	showFooterImpl (state);
	//	super.showFooter ();

	_writer.println ("<!-- Summary by MIME type:");
	int nTotal      = 0;
	int nValid      = 0;
	int nWellFormed = 0;
	Set keys = _mimeType.keySet ();
	Iterator iter = keys.iterator ();
	while (iter.hasNext ()) {
	    String mime = (String) iter.next ();
	    AuditCount count = (AuditCount) _mimeType.get (mime);
	    int total      = count.getTotal ();
	    int valid      = count.getValid ();
	    int wellFormed = count.getWellFormed ();

	    _writer.println (mime + ": " + total + " (" + valid + "," +
			     wellFormed + ")");

	    nTotal      += total;
	    nValid      += valid;
	    nWellFormed += wellFormed;
	}
	_writer.println ("Total: " + nTotal + " (" + nValid + "," +
			 nWellFormed + ")");
	_writer.println ("-->");

	_writer.println ("<!-- Summary by directory:");
	nTotal        = 0;
	nValid        = 0;
	nWellFormed   = 0;
	int nNotFound = 0;
	int nNotProcessed = 0;
	keys = _stateMap.keySet ();
	iter = keys.iterator ();
	while (iter.hasNext ()) {
	    String directory = (String) iter.next ();
	    state = (AuditState) _stateMap.get (directory);

	    int total        = state.getTotal ();
	    int valid        = state.getValid ();
	    int wellFormed   = state.getWellFormed ();
	    int notFound     = state.getNotFound ();
	    int notProcessed = state.getNotProcessed ();
	    _writer.println (directory + ": " + total + " (" + valid + "," +
			     wellFormed + ") + " + notProcessed + "," +
			     notFound);

	    nTotal        += total;
	    nValid        += valid;
	    nWellFormed   += wellFormed;
	    nNotFound     += notFound;
	    nNotProcessed += notProcessed;
	}
	_writer.println ("Total: " + nTotal + " (" + nValid + "," +
			 nWellFormed + ") + " + nNotProcessed + "," +
			 nNotFound);
	_writer.println ("-->");

	/* Update the elapsed time. */
	long dt = (System.currentTimeMillis () - _t0 + 999) / 1000;

	long ss = dt % 60;
	long dm = dt / 60;
	long mm = dm % 60;
	long hh = dm / 60;

	_writer.println ("<!-- Elapsed time: " + hh + ":" +
			 (mm > 9 ? "" : "0") + mm + ":" +
			 (ss > 9 ? "" : "0") + ss + " -->");
        _writer.flush ();
    }

    /**
     * Local extension to the standard callback that does the final output.
     * This should be in a suitable format for
     * including multiple files between the header and the footer, and
     * the XML of the header and footer must balance out.
     * @param state Audit handler state
     */
    public void showFooterImpl (AuditState state)
    {
	if (_nAudit > 0) {
	    String margin = getIndent (_level--);
	    _writer.println (margin + elementEnd ("audit"));
	}
	super.showFooter ();
    }

    /**
     * Do the initial output.  This should be in a suitable format for
     * including multiple files between the header and the footer, and
     * the XML of the header and footer must balance out.
     */
    public void showHeader ()
    {
        /* Initialize the handler. */

        _mimeType   = new TreeMap ();
        _stateMap   = new TreeMap ();
        _stateStack = new Stack ();
        _nAudit     = 0;

        _t0 = System.currentTimeMillis ();

	/* Instantiate a state object and initialize with the values
	 * of the global configuration file.
	 */

        AuditState state = showHeaderImpl (".");
        _stateStack.push (state);
        _home = state.getDirectory ();
    }

    /**
     * Local extension to the standard callback that does the initial output.
     * This should be in a suitable format for including multiple files
     * between the header and the footer, and the XML of the header and footer
     * must balance out.
     * @param directory Current directory filepath
     */
    public AuditState showHeaderImpl (String directory)
    {
	super.showHeader ();

	return new AuditState (directory);
    }

    /**
     * Callback indicating a new directory is being processed.
     *
     * Additional state information can be added to the AuditState object
     * in the showHeaderImpl() method before it is pushed onto the stack.
     */
    public void startDirectory (String directory)
    {
	try {
	    AuditState state = (AuditState)
		((AuditState) _stateStack.peek ()).clone (directory);

	    startDirectoryImpl (state);
	    _stateStack.push (state);
	}
	catch (CloneNotSupportedException e) {
	    e.printStackTrace (System.err);
	    System.exit (-1);
	}
    }

    /**
     * Local extension to the standard callback indicating a new directory
     * is being processed.
     * @param state Audit handler state
     */
    public void startDirectoryImpl (AuditState state)
    {
    }
}
