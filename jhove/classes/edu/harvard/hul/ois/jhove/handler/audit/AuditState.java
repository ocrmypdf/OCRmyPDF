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

package edu.harvard.hul.ois.jhove.handler.audit;

import java.io.*;

/**
 * State object for the JHOVE Audit output handler.
 */
public class AuditState
    extends AuditCount
    implements Cloneable
{
    /******************************************************************
     * PROTECTED INSTANCE FIELDS.
     ******************************************************************/

    /** Directory pathname. */
    protected String _directory;

    /** Number of files not found. */
    protected int _notFound;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     * Instantiate a <tt>AuditState</tt> object.
     */
    public AuditState (String directory)
    {
	super ();
	init (directory);
    }

    /**
     *  Initializes to a specified directory and clears counters. 
     */
    protected void init (String directory)
    {
	try {
	    File file = new File (directory);
	    _directory = file.getCanonicalPath ();
	}
	catch (Exception e) {
	    _directory = directory;
	}

	_notFound   = 0;
	_valid      = 0;
	_wellFormed = 0;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     * Creates and returns a copy of this object.
     */
    public Object clone (String directory)
	throws CloneNotSupportedException
    {
	AuditState state = (AuditState) super.clone ();
	state.init (directory);

	return state;
    }

    /******************************************************************
     * Accessor methods.
     ******************************************************************/

    /** Returns the directory path. */
    public String getDirectory ()
    {
	return _directory;
    }

    /** Returns the number of files not found. */
    public int getNotFound ()
    {
	return _notFound;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /** Sets the directory path. */
    public void setDirectory (String directory)
    {
	try {
	    File file = new File (directory);
	    _directory = file.getCanonicalPath ();
	}
	catch (Exception e) {
	    _directory = directory;
	}
    }

    /** Sets the count of files not found. */
    public void setNotFound (int notFound)
    {
	_notFound = notFound;
    }
}
