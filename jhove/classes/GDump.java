/**********************************************************************
 * GDump - JSTOR/Harvard Object Validation Environment
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
 * Dump contents of GIF file in human-readable format.
 */
public class GDump
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
	    System.err.println ("usage: java GDump file");
	    System.exit (-1);
	}

	try {
	    FileInputStream file = new FileInputStream (args[0]);
	    BufferedInputStream buffer = new BufferedInputStream (file);
	    DataInputStream stream = new DataInputStream (buffer);
	    boolean bigEndian = false;

	    String signature = readChars (stream, 3);
	    String version   = readChars (stream, 3);
	    System.out.println ("00000000: \"" + signature + version + "\"");

	    int width  = ModuleBase.readUnsignedShort(stream, bigEndian, null);
	    int height = ModuleBase.readUnsignedShort(stream, bigEndian, null);
	    int packedFields    = stream.readUnsignedByte ();
	    int backgroundColor = stream.readUnsignedByte ();
	    int aspectRatio     = stream.readUnsignedByte ();
	    System.out.println ("00000006: LogicalScreenDescriptor: " +
				width + "x" + height + " 0x" +
				leading (packedFields, 2) +
				Integer.toHexString (packedFields) + " " +
				backgroundColor + " " + aspectRatio);
	    long os = 13;

	    boolean globalColorTable     = (packedFields & 0x80) != 0;
	    int     globalColorTableSize =  packedFields & 0x07;

	    if (globalColorTable) {
		System.out.println (leading (os, 8) + os +
				    ": GlobalColorTable:");
		os = colorTable (stream, os, globalColorTableSize);
	    }

	    for (int op = 0; (op = stream.readUnsignedByte ()) != -1;) {
		if (op == 0x00) {
		    System.out.println (leading (os, 8) + os + 
					": BlockTerminator");
		    os++;
		}
		else if (op == 0x2c) {
		    int imageLeft   = ModuleBase.readUnsignedShort (stream,
								    bigEndian,
								    null);
		    int imageTop    = ModuleBase.readUnsignedShort (stream,
								    bigEndian,
								    null);
		    int imageWidth  = ModuleBase.readUnsignedShort (stream,
								    bigEndian,
								    null);
		    int imageHeight = ModuleBase.readUnsignedShort (stream,
								    bigEndian,
								    null);
		    packedFields = stream.readUnsignedByte ();
		    System.out.println (leading (os, 8) + os +
					": ImageDescriptor: " + imageLeft +
					"," + imageTop + " " + imageWidth +
					"x" + imageHeight + " 0x" +
					leading (packedFields, 2) +
					Integer.toHexString (packedFields));
		    os += 10;

		    boolean localColorTable     = (packedFields & 0x80) != 0;
		    int     localColorTableSize =  packedFields & 0x07;

		    if (localColorTable) {
			System.out.println (leading (os, 8) + os +
					    ": LocalColorTable:");
			os = colorTable (stream, os, localColorTableSize);
		    }

		    int size = stream.readUnsignedByte ();
		    System.out.println (leading (os, 8) + os +
					": ImageData: " + size);
		    os = subBlocks (stream, ++os);
		}
		else if (op == 0x21) {
		    int label = stream.readUnsignedByte ();

		    if (label == 0x01) {
			int blockSize = stream.readUnsignedByte ();
			int gridLeft  = ModuleBase.readUnsignedShort(stream,
								     bigEndian,
								     null);
			int gridTop   = ModuleBase.readUnsignedShort(stream,
								     bigEndian,
								     null);
			int gridWidth = ModuleBase.readUnsignedShort(stream,
								     bigEndian,
								     null);
			int gridHeight= ModuleBase.readUnsignedShort(stream,
								     bigEndian,
								     null);
			int cellWidth  = stream.readUnsignedByte ();
			int cellHeight = stream.readUnsignedByte ();
			int foreground = stream.readUnsignedByte ();
			int background = stream.readUnsignedByte ();
			System.out.println (leading (os, 8) + os + 
					    ": PlainTextExtension: " +
					    blockSize + " " + gridLeft + "," +
					    gridTop + " " + gridWidth + "x" +
					    gridHeight + " " + cellWidth +
					    "x" + cellHeight + " " +
					    foreground + "," + background);
			os += 15;
			os = subBlocks (stream, os);
		    }
		    else if (label == 0xf9) {
			int blockSize = stream.readUnsignedByte ();
			packedFields  = stream.readUnsignedByte ();
			int delayTime = ModuleBase.readUnsignedShort(stream,
								     bigEndian,
								     null);
			int colorIndex= stream.readUnsignedByte ();
			System.out.println (leading (os, 8) + os +
					    ": GraphicControlExtension: " +
					    blockSize + " 0x" +
					    leading (packedFields, 2) +
					    packedFields + " " + delayTime +
					    " " + colorIndex);
			os += 7;
		    }
		    else if (label == 0xfe) {
			System.out.println (leading (os, 8) + os + 
					    ": CommentExtension: \"" +
					    "\"");
			os += 2;
			os = subBlocks (stream, os);
		    }
		    else if (label == 0xff) {
			int blockSize = stream.readUnsignedByte ();
			String appId  = readChars (stream, 8);
			int [] authCode = new int [3];
			authCode[0]   = stream.readUnsignedByte ();
			authCode[1]   = stream.readUnsignedByte ();
			authCode[2]   = stream.readUnsignedByte ();
			System.out.println (leading (os, 8) + os + 
					    ": ApplicationExtension: " +
					    blockSize + " \"" + appId +
					    "\" " + authCode[0] + "," +
					    authCode[1] + "," + authCode[2]);
			os += 14;
			os = subBlocks (stream, os);
		    }
		    else {
			String hex = Integer.toHexString (label);
			System.out.println (leading (os-1, 8) + (os-1) +
					    ": Unknown extension block: 0x" +
					    leading (hex, 2) + hex);
			os += 2;
		    }
		}
		else if (op == 0x3b) {
		    System.out.println (leading (os, 8) + os +
					": Trailer: 0x3b");
		    os++;
		    break;
		}
		else {
		    String hex = Integer.toHexString (op);
		    System.out.println (leading (os, 8) + os +
					": Unknown block: 0x" +
					leading (hex, 2) +  hex);
		    os++;
		}
	    }
	    stream.close ();
	}
	catch (Exception e) {
	    e.printStackTrace (System.err);
	    System.exit (-2);
	}
    }

    /**
     * Read and display a color table.
     * @param stream Data input stream
     * @param os     Current byte offset
     * @param size   Color table size
     * @return Updated byte offset
     */
    private static long colorTable (DataInputStream stream, long os, int size)
	throws IOException
    {
	int n = 2<<size;
	for (int i=0; i<n; i++) {
	    long r = stream.readUnsignedByte ();
	    long g = stream.readUnsignedByte ();
	    long b = stream.readUnsignedByte ();
	    System.out.println (leading (os, 8) + os + ": " +
				leading (i, 3, ' ') + i + ": " +
				leading (r, 3, ' ') + r + "," +
				leading (g, 3, ' ') + g + "," +
				leading (b, 3, ' ') + b);
	    os += 3;
	}
	return os;
    }

    /**
     * Read and display a sequence of sub-blocks.
     * @param stream Data input stream
     * @param os     Current byte offset
     * @return Updated byte offset
     */
    private static long subBlocks (DataInputStream stream, long os)
	throws IOException
    {
	int size;

	while ((size = stream.readUnsignedByte ()) != 0) {
	    System.out.println (leading (os, 8) + os + ": SubBlock: " + size);
	    os += 1;
	    for (int i=0; i<size; i++) {
		stream.readUnsignedByte ();
		os += 1;
	    }
	}
	System.out.println (leading (os, 8) + os +  ": BlockTerminator");
	return os + 1;
    }
}
