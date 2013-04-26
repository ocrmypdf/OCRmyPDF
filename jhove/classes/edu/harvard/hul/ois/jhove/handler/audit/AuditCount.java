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

//import java.io.*;

/**
 * Count object for the JHOVE Audit output handler.
 */
public class AuditCount
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Number of files not processed. */
    protected int _notProcessed;

    /** Number of valid files. */
    protected int _valid;

    /** Number of well-formed files. */
    protected int _wellFormed;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     * Instantiate a <tt>AuditCount</tt> object.
     */
    public AuditCount ()
    {
	_notProcessed = 0;
	_valid        = 0;
	_wellFormed   = 0;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Accessor methods.
     ******************************************************************/

    /** Returns the total number of files not processed. */
    public int getNotProcessed ()
    {
	return _notProcessed;
    }

    /** Returns the total number of valid or well-formed
        files. */
    public int getTotal ()
    {
	return _valid + _wellFormed;
    }

    /** Returns the total number of valid files. */
    public int getValid ()
    {
	return _valid;
    }

    /** Returns the total number of well-formed files. */
    public int getWellFormed ()
    {
	return _wellFormed;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /** Sets the count of files that are not processed. */
    public void setNotProcessed (int notProcessed)
    {
	_notProcessed = notProcessed;
    }

    /** Sets the count of valid files. */
    public void setValid (int valid)
    {
	_valid = valid;
    }

    /** Sets the count of well-formed files. */
    public void setWellFormed (int wellFormed)
    {
	_wellFormed = wellFormed;
    }
}
