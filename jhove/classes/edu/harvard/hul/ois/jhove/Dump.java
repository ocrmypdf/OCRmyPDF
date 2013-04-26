/**********************************************************************
 * JHOVE - JSTOR/Harvard Object Validation Environment
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

package edu.harvard.hul.ois.jhove;

import java.io.*;

/**
 * Common methods for dump utilities.
 */
public class Dump
{
    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/
    public Dump ()
    {
    }

    /******************************************************************
     * PUBLIC CLASS METHODS.
     ******************************************************************/

    /**
     * Return leading characters to pad out the byte offset to field width.
     * @param os Byte offset
     * @param width Field width
     * @return String of leading zeros 
     */
    protected static String leading (int os, int width)
    {
	return leading (os, width, '0');
    }

    /**
     * Return leading characters to pad out the byte offset to field width.
     * @param os Byte offset
     * @param width Field width
     * @return String of leading zeros 
     */
    protected static String leading (long os, int width)
    {
	return leading (os, width, '0');
    }

    /**
     * Return leading characters to pad out the byte offset to field width.
     * @param os    Byte offset
     * @param width Field width
     * @param pad   Padding character
     * @return String of leading characters 
     */
    protected static String leading (int os, int width, char pad)
    {
	return leading ((long) os, width, pad);
    }

    /**
     * Return leading characters to pad out the byte offset to field width.
     * @param os    Byte offset
     * @param width Field width
     * @param pad   Padding character
     * @return String of leading characters 
     */
    protected static String leading (long os, int width, char pad)
    {
	String ss = Long.toString (os);
	StringBuffer buffer = new StringBuffer ();
	for (int j=0; j<width-ss.length (); j++) {
	    buffer.append (pad);
	}
	return buffer.toString ();
    }

    /**
     * Return leading characters to pad out the string to field width.
     * @param s     String
     * @param width Field width
     * @return String of leading characters 
     */
    protected static String leading (String s, int width)
    {
	return leading (s, width, '0');
    }

    /**
     * Return leading characters to pad out the string to field width.
     * @param s     String
     * @param width Field width
     * @param pad   Padding character
     * @return String of leading characters 
     */
    protected static String leading (String s, int width, char pad)
    {
	StringBuffer buffer = new StringBuffer ();
	for (int j=0; j<width-s.length (); j++) {
	    buffer.append (pad);
	}
	return buffer.toString ();
    }

    /**
     * Read and display a sequence of characters.
     * @param stream Data input stream
     * @param length Number of characters
     * @return Character string
     */
    protected static String readChars (DataInputStream stream, int length)
	throws IOException
    {
	byte [] buffer = new byte [length];
	for (int i=0; i<length; i++) {
	    buffer[i] = stream.readByte ();
	}
	return new String (buffer);
    }
}
