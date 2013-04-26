/**********************************************************************
 * JDump - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2005 by the President and Fellows of Harvard College
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

/**
 * Dump contents of WAVE file in human-readable format.
 *
 * @author Gary McGath
 *
 */
public class WDump extends Dump {

    /* Fixed value for first 4 bytes */
    private static final int[] sigByte =
       { 0X52, 0X49, 0X46, 0X46 };

    private static final boolean ENDIAN = false;     /* little endian */

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
            System.err.println ("usage: java WDump file");
            System.exit (-1);
        }
        try {
            FileInputStream file = new FileInputStream (args[0]);
            BufferedInputStream buffer = new BufferedInputStream (file);
            DataInputStream stream = new DataInputStream (buffer);
            ADump dump = new ADump ();   // Just to access contained classes
            long os = 0;
            for (int i=0; i<4; i++) {
                int ch;
                ch = stream.readUnsignedByte();
                if (ch != sigByte[i]) {
                    System.out.println ("No AIFF FORM header");
                    System.exit (-2);
                }
		os++;
            }
            long ckSize = ModuleBase.readUnsignedInt (stream, ENDIAN);
	    os += 4;
            
            // Read the file type
            String formType = read4Chars (stream);
	    os += 4;

	    System.out.println ("00000000: RIFF " + ckSize + ": " + formType);

            boolean endOfFile = false;
            while (!endOfFile) {
                // Read chunks
                try {
                    // Read chunk name.
                    String ckID = read4Chars (stream);
                    // Read size (excluding chunk name and size fields)
		    ckSize = ModuleBase.readUnsignedInt (stream, ENDIAN);
                    System.out.print (leading (os, 8) + os + ": " + ckID +
				      " " + ckSize);
		    long alreadyRead = 0;
		    if (ckID.equals ("fact")) {
			long sampleLength =
			    ModuleBase.readUnsignedInt (stream, ENDIAN);
			System.out.print (": " + sampleLength);
			alreadyRead = 4;
		    }
		    else if (ckID.equals ("fmt ")) {
			int formatTag = ModuleBase.readUnsignedShort (stream,
								      ENDIAN);
			int channels = ModuleBase.readUnsignedShort (stream,
								     ENDIAN);
			long samplesPerSec =
			    ModuleBase.readUnsignedInt (stream, ENDIAN);
			long avgBytesPerSec =
			    ModuleBase.readUnsignedInt (stream, ENDIAN);
			int blockAlign = ModuleBase.readUnsignedShort (stream,
								       ENDIAN);
			String hex = Integer.toHexString (formatTag);
			System.out.print (": 0x" + leading (hex, 4) + hex +
					  " " + channels + " " +
					  samplesPerSec + " " +
					  avgBytesPerSec + " " + blockAlign);
			alreadyRead = 14;
			if (ckSize > 14) {
			    int bitsPerSample =
				ModuleBase.readUnsignedShort (stream, ENDIAN);
			    System.out.print (" " + bitsPerSample);
			    alreadyRead = 16;
			    if (ckSize > 16) {
				int size =
				    ModuleBase.readUnsignedShort (stream,
								  ENDIAN);
				System.out.print (" " + size);
				alreadyRead = 18;
				if (size == 22) {
				    int validBitsPerSample =
					ModuleBase.readUnsignedShort (stream,
								      ENDIAN);
				    long channelMask =
					ModuleBase.readUnsignedInt (stream,
								    ENDIAN);
				    hex = Long.toHexString (channelMask);
				    System.out.print (" " +
						      validBitsPerSample +
						      " 0x" +
						      leading (hex, 8) + hex +
						      " 0x");
				    for (int i=0; i<4; i++) {
					long guid =
					    ModuleBase.readUnsignedInt (
								  stream,
								  ENDIAN);
					hex = Long.toHexString (guid);
					System.out.print (leading (hex, 8) +
							  hex);
				    }
				    alreadyRead = 40;
				}
			    }
			}
		    }
		    System.out.println ();

                    if (ckID.equals ("list") || ckID.equals ("LIST")) {
                        readNestedChunks (ckID, stream, ckSize, os + 8);
                    }
                    else {
                        stream.skipBytes ((int) (ckSize - alreadyRead));
                    }
                    os += ckSize + 8;
                }
                catch (EOFException e) {
                    endOfFile = true;
                }
            }
        }
        catch (Exception e) {
        }
    }
    
    /* The "list" and "LIST" chunks (which are two distinct chunk types)
       hold nested chunks. */
    private static void readNestedChunks 
            (String ckID, DataInputStream stream, long ckSize, long os)
            throws IOException
    {
        String listType = read4Chars (stream);
        System.out.println ("List type = " + listType);
        while (ckSize > 0) {
            String subCkID = read4Chars (stream);
            long subCkSize = ModuleBase.readUnsignedInt (stream, ENDIAN, null);
            System.out.println (leading (os, 8) + os + ": " +
                    ckID + "/" + subCkID + " " + subCkSize);
            stream.skipBytes ((int) subCkSize);
            os += subCkSize + 8;
            ckSize -= subCkSize + 8;
        }
    }
    
    private static String read4Chars (DataInputStream stream) 
            throws IOException
    {
        StringBuffer sbuf = new StringBuffer(4);
        for (int i = 0; i < 4; i++) {
            int ch = ModuleBase.readUnsignedByte(stream, null);
            sbuf.append((char) ch);
        }
        return sbuf.toString ();
    }
}
