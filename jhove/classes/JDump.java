/**********************************************************************
 * JDump - JSTOR/Harvard Object Validation Environment
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

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
//import java.util.*;

/**
 * Dump contents of JPEG file in human-readable format.
 */
public class JDump
    extends Dump
{
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
	    System.err.println ("usage: java JDump file");
	    System.exit (-1);
	}

	try {
	    FileInputStream file = new FileInputStream (args[0]);
	    BufferedInputStream buffer = new BufferedInputStream (file);
	    DataInputStream stream = new DataInputStream (buffer);
	    boolean bigEndian = true;

	    long os = 0;

	    boolean endOfImage = false;
	    boolean readingECS = false;
	    boolean haveCode   = false;;
	    int nECS = 0;
	    int code = 0;
	    while (!endOfImage) {
		if (!readingECS) {
		    if (!haveCode) {
			code = stream.readUnsignedByte ();
			for (int i=0;
			     (code = stream.readUnsignedByte ()) == 0xff;
			     i++) {
			    System.out.println (leading (os, 8) + os +
						": fill 0xff");
			    os++;
			}
		    }
		}
		else {
		    boolean ff = false;
		    int length = 0;
		    while (true) {
			code = stream.readUnsignedByte ();
			length++;
			if (code == 0xff) {
			    ff = true;
			}
			else if (ff) {
			    if (code != 0x00) {
				length -= 2;
				break;
			    }
			    else {
				ff = false;
			    }
			}
		    }
		    System.out.println (leading (os, 8) + os + ": ECS" +
					nECS + " " + length + " ...");
		    os += length;
		    nECS++;
		    readingECS = false;
		    haveCode   = true;
		    continue;
		}

		if (code == 0x01) {
		    System.out.println (leading (os, 8) + os + ": TEM");
		}
		else if ((code >= 0xc0 && code <= 0xc3) ||
			 (code >= 0xc5 && code <= 0xc7) ||
			 (code >= 0xc9 && code <= 0xcb) ||
			 (code >= 0xcd && code <= 0xcf)) {
		    int n = code - 0xc0;
/****************** int length = markerSegment (stream, bigEndian); */
		    int length = ModuleBase.readUnsignedShort (stream,
							       bigEndian,
							       null);
		    int P  = stream.readUnsignedByte ();
		    int Y  = ModuleBase.readUnsignedShort (stream, bigEndian,
							  null);
		    int X  = ModuleBase.readUnsignedShort (stream, bigEndian,
							   null);
		    int Nf = stream.readUnsignedByte ();
		    int [] Ci  = new int [Nf];
		    int [] Hi  = new int [Nf];
		    int [] Vi  = new int [Nf];
		    int [] Tqi = new int [Nf];
		    for (int i=0; i<Nf; i++) {
			Ci[i]  = stream.readUnsignedByte ();
			Hi[i]  = stream.readUnsignedByte ();
			Tqi[i] = stream.readUnsignedByte ();
		    }
		    System.out.print (leading (os, 8) + os + ": SOF" + n +
				      " " + length + ": " + P + " " + X +
				      "x" + Y + " " + Nf + ":");
		    for (int i=0; i<Nf; i++) {
			System.out.print (" " + Ci[i] + "," + Hi[i] + "," +
					  Tqi[i]);
		    }
		    System.out.println ();
		    os += length;
		}
		else if (code == 0xc4) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DHT" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xc8) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": JPG" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xcc) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DAC" + " " +
					length + " ...");
		    os += length;
		}
		else if (code >= 0xd0 && code <= 0xd7) {
		    int m = code - 0xd0;
		    System.out.println (leading (os, 8) + os + ": RST" + m);

		    readingECS = true;
		}
		else if (code == 0xd8) {
		    System.out.println (leading (os, 8) + os + ": SOI");
		}
		else if (code == 0xd9) {
		    System.out.println (leading (os, 8) + os + ": EOI");
		    endOfImage = true;
		    break;
		}
		else if (code == 0xda) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": SOS" + " " +
					length + " ...");
		    os += length;

		    readingECS = true;
		}
		else if (code == 0xdb) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DQT" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xdc) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DNL" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xdd) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DRI" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xde) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DHP" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xdf) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": EXP" + " " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xe0) {
		    int length = ModuleBase.readUnsignedShort (stream,
							       bigEndian,
							       null);
		    String id  = readChars (stream, 5);
		    if (id.equals ("JFIF\0")) {
			int major  = stream.readUnsignedByte ();
			int minor  = stream.readUnsignedByte ();
			int units  = stream.readUnsignedByte ();
			int xDensity = ModuleBase.readUnsignedShort (stream,
								     bigEndian,
								     null);
			int yDensity = ModuleBase.readUnsignedShort (stream,
								     bigEndian,
								     null);
			int xThumbnail = stream.readUnsignedByte ();
			int yThumbnail = stream.readUnsignedByte ();
			System.out.print (leading (os, 8) + os + ": APP0 " +
					  "\"" + id + "\" " + major + "." +
					  minor + " " + units + " " +
					  xDensity + "x" + yDensity + " "
					  + xThumbnail + "x" + yThumbnail);
			int n = length - 16;
			if (n > 0) {
			    for (int i=0; i<n; i++) {
				stream.readUnsignedByte ();
			    }
			    System.out.print (" " + n + " ...");
			}
			System.out.println ();
		    }
		    else if (id.equals ("JFXX\0")) {
			int ext = stream.readUnsignedByte ();
			String hex = Integer.toHexString (ext);
			System.out.print (leading (os, 8) + os + ": APP0 " +
					  "0x" + leading (hex, 2) + hex);
			int n = length-3;
			if (n > 0) {
			    for (int i=0; i<n; i++) {
				stream.readUnsignedByte ();
			    }
			    System.out.print (" " + n + " ...");
			}
			System.out.println ();
		    }
		    else {
			System.out.println (leading (os, 8) + os + ": APP0 " +
					    length + " ...");
			for (int i=2; i<length; i++) {
			    stream.readUnsignedByte ();
			}
		    }
		    os += length;
		}
		else if (code >= 0xe1 && code <= 0xef) {
		    int n = code - 0xe0;
		    /*
    		    int length = markerSegment (stream, bigEndian);
		    */
		    int length = ModuleBase.readUnsignedShort (stream,
							       bigEndian,
							       null);
		    if ((n == 1 || n == 2) && length >= 8) {
			String id = readChars (stream, 4);
			int NULL    = stream.readUnsignedByte ();
			int padding = stream.readUnsignedByte ();
			if (id.equals ("Exif") || id.equals ("FPXR")) {
			    System.out.println (leading (os, 8) + os +
						": APP" + n + " \"" + id +
						"\" " + NULL + " " + padding +
						" " + (length-8) + ": ...");
			}
			else {
			    System.out.println (leading (os, 8) + os +
						": APP" + n + " " + length +
						" ...");
			}
			for (int i=8; i<length; i++) {
			    stream.readUnsignedByte ();
			}
		    }
		    else {
			System.out.println (leading (os, 8) + os + ": APP" +
					    n +	" " + length + " ...");
			for (int i=2; i<length; i++) {
			    stream.readUnsignedByte ();
			}
		    }
		    os += length;
		}
		else if (code == 0xf0) {
		    int length = ModuleBase.readUnsignedShort (stream,
							       bigEndian,
							       null);
		    int v   = stream.readUnsignedByte ();
		    int rev = stream.readUnsignedByte ();
		    System.out.print (leading (os, 8) + os + ": VER " + 
					v + "." + rev);
		    int n = length - 4;
		    if (n > 0) {
			int [] cap = new int [n];
			for (int i=0; i<n; i++) {
			    cap[i] = stream.readUnsignedByte ();
			    System.out.print (((i==0) ? " " : ",") + cap[i]);
			}
		    }
		    System.out.println ();
		    os += length;
		}
		else if (code == 0xf1) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DTI " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xf2) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DTT " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xf3) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": SRF " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xf4) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": SRS " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xf5) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DCR " +
					length + " ...");
		    os += length;
		}
		else if (code == 0xf6) {
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": DQS " +
					length + " ...");
		    os += length;
		}
		else if (code >= 0xf7 && code <= 0xfd) {
		    int n = code - 0xf0;
		    int length = markerSegment (stream, bigEndian);
		    System.out.println (leading (os, 8) + os + ": JPG" + n +
					" " + length + " ...");
		    os += length;
		}
		else if (code == 0xfe) {
		    int length = ModuleBase.readUnsignedShort (stream,
							       bigEndian,
							       null);
		    String comment = readChars (stream, length-2);
		    System.out.println (leading (os, 8) + os + ": COM \"" +
					comment + "\"");
		    os += length;
		}
		else {
		    int length = markerSegment (stream, bigEndian);
		    String hex = Integer.toHexString (code);
		    System.out.println (leading (os, 8) + os + ": RES (0x" +
					leading (hex, 2) + hex + ") " +
					length + " ...");
		}
		os += 2;
	    }

	    stream.close ();
	}
	catch (Exception e) {
	    e.printStackTrace (System.err);
	    System.exit (-2);
	}
    }

    /**
     * Read marker segment data
     * @param stream    Data input stream
     * @param bigEndian True if big-endian
     * @return Length of marker segment
     */
    private static int markerSegment (DataInputStream stream,
				      boolean bigEndian)
	throws IOException
    {
	int length = ModuleBase.readUnsignedShort (stream,
						   bigEndian,
						   null);
	for (int i=2; i<length; i++) {
	    stream.readUnsignedByte ();
	}
	return length;
    }
}
