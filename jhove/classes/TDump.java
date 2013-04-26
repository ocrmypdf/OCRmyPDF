/**********************************************************************
 * TDump - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2004 by JSTOR and the President and Fellows of Harvard College
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

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.tiff.*;
import java.io.*;
import java.util.*;

/**
 * Dump contents of TIFF file in human-readable format.
 */
public class TDump
    extends Dump
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** Count of IFDs. */
    private static int _nIFDs;
    /** Sorted associative map of tags. */
    private static Map _tags;

    /******************************************************************
     * MAIN ENTRY POINT.
     ******************************************************************/

    /**
     * Main entry point.
     * @param args Command line arguments
     */
    public static void main (String [] args)
    {
	if (args.length < 1) {
	    System.err.println ("usage: java TDump [-bs] file");
	    System.exit (-1);
	}

	String tiff = null;
	boolean nobyte = false;
	boolean nosub  = false;
	for (int i=0; i<args.length; i++) {
	    if (args[i].equals ("-b")) {
		nobyte = true;
	    }
	    else if (args[i].equals ("-s")) {
		nosub = true;
	    }
	    else if (tiff == null) {
		tiff = args[i];
	    }
	}

	/* Accumlate all tag definitions in a sorted map. */

	_tags = new TreeMap ();

	int err = 0;
	try {

	    /* Read TIFF header. */

	    RandomAccessFile file = new RandomAccessFile (tiff, "r");
	    boolean bigEndian = true;
	    int b1 = ModuleBase.readUnsignedByte (file);
	    int b2 = ModuleBase.readUnsignedByte (file);
	    if (b1 == 0x49 && b2 == b1) {
		bigEndian = false;
	    }
	    int magic = ModuleBase.readUnsignedShort (file, bigEndian);
	    long offset = ModuleBase.readUnsignedInt (file, bigEndian);
	    _tags.put ("00000000", "\"" + ((char) b1) + ((char) b2) + "\" (" +
		       (bigEndian ? "big" : "little") + " endian) " + magic +
		       " LONG @" + offset);

	    /* Read IFDs. */

	    _nIFDs = 0;
	    while ((offset = readIFD (file, bigEndian, offset, nobyte,
				      nosub)) > 0) {
	    }
	    file.close ();
	}
	catch (Exception e) {
	    e.printStackTrace (System.out);
	    err = -2;
	}
	finally {

	    /* Display all tags in offset-sorted order. */

	    Iterator iter = _tags.keySet ().iterator ();
	    while (iter.hasNext ()) {
		String os = (String) iter.next ();
		System.out.println (os + ": " + (String) _tags.get (os));
	    }
	    if (err != 0) {
		System.exit (err);
	    }
	}
    }

    /**
     * Read IFDs.
     * @param file      Open TIFF file
     * @param bigEndian True if big-endian
     * @param offset    Byte offset of IFD
     * @param nobyte    If true, only display the first 8 bytes of data of
     *                  type BYTE
     * @param nosub     If true, do not parse subIFDs
     */
    private static long readIFD (RandomAccessFile file, boolean bigEndian,
				 long offset, boolean nobyte, boolean nosub)
	throws Exception
    {
	int nIFD = ++_nIFDs;
	List subIFDs = new ArrayList ();
	List stripByteCounts = new ArrayList ();
	List stripOffsets    = new ArrayList ();

	file.seek (offset);
	int nEntries = ModuleBase.readUnsignedShort (file, bigEndian);
	_tags.put (leading (offset, 8) + offset, "IFD " + nIFD + " with " +
	       nEntries + " entries");

	String name = null;
	for (int i=0; i<nEntries; i++) {
	    long os = offset + 2 + i*12;
	    file.seek (os);
	    int  tag   = ModuleBase.readUnsignedShort (file, bigEndian);
	    int  type  = ModuleBase.readUnsignedShort (file, bigEndian);
	    long count = ModuleBase.readUnsignedInt   (file, bigEndian);

	    StringBuffer buffer = new StringBuffer (tag + " (" +
						    TiffTags.tagName(tag) +
						    ") " + IFD.TYPE[type] +
						    " " + count);
	    if (type == IFD.ASCII) {
		if (count > 4) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		StringBuffer ascii = new StringBuffer ();
		for (int j=0; j<count-1; j++) {
		    ascii.append ((char) ModuleBase.readUnsignedByte (file));
		}
		buffer.append (" = \"" + ascii.toString () + "\"");
	    }
	    else if (type == IFD.BYTE ||
		     type == IFD.UNDEFINED) {
		if (count > 4) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		long ct = count;
		if (nobyte && count > 8) {
		    ct = 8;
		}
		for (int j=0; j<ct; j++) {
		    long by = ModuleBase.readUnsignedByte (file);
		    buffer.append (" " + by);
		}
		if (nobyte && count > 8) {
		    buffer.append (" ...");
		}
	    }
	    else if (type == IFD.DOUBLE) {
		long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		file.seek (vo);

		buffer.append (" @" + vo + " =");
		for (int j=0; j<count; j++) {
		    double db = ModuleBase.readDouble (file, bigEndian);
		    buffer.append (" " + db);
		}
	    }
	    else if (type == IFD.FLOAT) {
		if (count > 1) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		for (int j=0; j<count; j++) {
		    float fl = ModuleBase.readFloat (file, bigEndian);
		    buffer.append (" " + fl);
		}
	    }
	    else if (type == IFD.LONG || type == IFD.IFD) {
		if (count > 1) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo + " = ");
		}
		else if (tag == 330   ||   /* Sub IFD */
			 tag == 34665 ||   /* EXIF IFD */
			 tag == 34853 ||   /* EXIF GPS IFD */
			 tag == 40965) {   /* EXIF Interoperability IFD */
		    buffer.append (" @");
		}
		else {
		    buffer.append (" = ");
		}
		for (int j=0; j<count; j++) {
		    long in = ModuleBase.readUnsignedInt (file, bigEndian);
		    if (j > 0) {
			buffer.append (" ");
		    }
		    buffer.append (in);

		    if (tag == 330   ||   /* Sub IFD */
			tag == 34665 ||   /* EXIF IFD */
			tag == 34853 ||   /* EXIF GPS IFD */
			tag == 40965) {   /* EXIF Interoperability IFD */
			subIFDs.add (new Long (in));
		    }
		    else if (tag == 273) {
			stripOffsets.add (new Long (in));
		    }
		    else if (tag == 279) {
			stripByteCounts.add (new Long (in));
		    }
		}
	    }
	    else if (type == IFD.RATIONAL) {
		long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		file.seek (vo);

		buffer.append (" @" + vo + " =");
		for (int j=0; j<count; j++) {
		    long numer = ModuleBase.readUnsignedInt (file, bigEndian);
		    long denom = ModuleBase.readUnsignedInt (file, bigEndian);
		    buffer.append (" " + numer + "/" + denom);
		}
	    }
	    else if (type == IFD.SBYTE) {
		if (count > 4) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		for (int j=0; j<count; j++) {
		    long by = ModuleBase.readSignedByte (file);
		    buffer.append (" " + by);
		}
	    }
	    else if (type == IFD.SHORT) {
		if (count > 2) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		for (int j=0; j<count; j++) {
		    int sh = ModuleBase.readUnsignedShort (file, bigEndian);
		    buffer.append (" " + sh);

		    if (tag == 273) {
			stripOffsets.add (new Long ((long) sh));
		    }
		    else if (tag == 279) {
			stripByteCounts.add (new Long ((long) sh));
		    }

		}
	    }
	    else if (type == IFD.SLONG) {
		if (count > 1) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		for (int j=0; j<count; j++) {
		    int in = ModuleBase.readSignedInt (file, bigEndian);
		    buffer.append (" " + in);
		}
	    }
	    else if (type == IFD.SRATIONAL) {
		long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		file.seek (vo);

		buffer.append (" @" + vo + " =");
		for (int j=0; j<count; j++) {
		    long numer = ModuleBase.readSignedInt (file, bigEndian);
		    long denom = ModuleBase.readSignedInt (file, bigEndian);
		    buffer.append (" " + numer + "/" + denom);
		}
	    }
	    else if (type == IFD.SSHORT) {
		if (count > 2) {
		    long vo = ModuleBase.readUnsignedInt (file, bigEndian);
		    file.seek (vo);

		    buffer.append (" @" + vo);
		}
		buffer.append (" =");
		for (int j=0; j<count; j++) {
		    int sh = ModuleBase.readSignedShort (file, bigEndian);
		    buffer.append (" " + sh);
		}
	    }
	    _tags.put (leading (os, 8) + os, buffer.toString ());
	}

	if (!nosub) {
	    for (int i=0; i<subIFDs.size (); i++) {
		long os = ((Long) subIFDs.get (i)).longValue ();
		while ((os = readIFD (file, bigEndian, os, nobyte, nosub)) > 0) {
		}
	    }
	}

	long os = offset + 2 + nEntries*12;
	file.seek (os);
	long next = ModuleBase.readUnsignedInt (file, bigEndian);
	_tags.put (leading (os, 8) + os, "NextIFDOffset LONG @" + next);

	int len = stripOffsets.size ();
	if (len > 0) {
	    for (int j=0; j<len; j++) {
		long start = ((Long) stripOffsets.get (j)).longValue ();
		long count = ((Long) stripByteCounts.get (j)).longValue ();
		long finish= start + count - 1;
		_tags.put (leading (start, 8) + start, "(Image " + nIFD +
			   ",strip " + (j+1) + ") IMAGEDATA " + count +
			   ": ... " + leading (finish, 8) + finish);
	    }
	}

	return next;
    }
}
