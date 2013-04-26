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
import edu.harvard.hul.ois.jhove.module.aiff.*;
import java.io.*;

/**
 * Dump contents of AIFF file in human-readable format.
 * @author Gary McGath
 */
public class ADump extends Dump {

    /* Fixed value for first 4 bytes */
    private static final int[] sigByte =
       { 0X46, 0X4F, 0X52, 0X4D };
    private static final boolean ENDIAN = true;     /* bigEndian */

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
            System.err.println ("usage: java ADump file");
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
            }
            os += 4;
            long ckSize = ModuleBase.readUnsignedInt (stream, ENDIAN);
            
            // Read the file type
            StringBuffer formType = new StringBuffer (4);
            for (int i=0; i<4; i++) {
                int ch = ModuleBase.readUnsignedByte(stream);
                formType.append((char) ch);
            }
	    System.out.println ("00000000: FORM " + ckSize + ": " + formType);

	    boolean aiff_c = false;
	    if (formType.toString ().equals ("AIFC")) {
		aiff_c = true;
	    }

            StringBuffer sbuf = new StringBuffer ();
            boolean endOfFile = false;
            while (!endOfFile) {
                // Read chunks
                try {
                    sbuf.setLength(0);
                    // Read chunk name.
                    for (int i=0; i<4; i++) {
                        int ch = ModuleBase.readUnsignedByte(stream);
                        sbuf.append((char) ch);
                    }
                    String ckID = sbuf.toString ();
                    // Read size (excluding chunk name and size fields)
		    ckSize = ModuleBase.readUnsignedInt (stream, ENDIAN);
                    System.out.print (leading (os, 8) + os + ": " + ckID +
				      " " + ckSize);
		    long alreadyRead = 0;
		    if (ckID.equals ("AESD")) {
			int [] aes = new int[24];
			for (int i=0; i<24; i++) {
			    aes[i] = ModuleBase.readUnsignedByte (stream);
			    
			}
			System.out.print (": " + aes[0]);
			for (int i=1; i<24; i++) {
			    System.out.print ("," + aes[i]);
			}
			alreadyRead = 24;
		    }
		    else if (ckID.equals ("ANNO") ||
			     ckID.equals ("AUTH") ||
			     ckID.equals ("(c) ") ||
			     ckID.equals ("NAME")) {
			sbuf.setLength (0);
			for (int i=0; i<ckSize; i++) {
			    int ch = ModuleBase.readUnsignedByte (stream);
			    sbuf.append ((char) ch);
			}
			System.out.print (": \"" + sbuf.toString () + "\"");
			alreadyRead = ckSize;
		    }
		    else if (ckID.equals ("APPL")) {
			sbuf.setLength (0);
			for (int i=0; i<4; i++) {
			    int ch = ModuleBase.readUnsignedByte (stream);
			    sbuf.append ((char) ch);
			}
			System.out.print (": " + sbuf.toString ());
			alreadyRead = 4;
		    }
		    else if (ckID.equals ("COMM")) {
			int numChannels = ModuleBase.readSignedShort (stream,
								      ENDIAN);
			long numSampleFrames =
			    ModuleBase.readUnsignedInt (stream, ENDIAN);
			int sampleSize = ModuleBase.readSignedShort (stream,
								     ENDIAN);
			byte [] buf = new byte[10];
			for (int i=0; i<10; i++) {
			    buf[i] = (byte) ModuleBase.readSignedByte (stream);
			}
			ExtDouble xd = new ExtDouble (buf);
			double sampleRate = xd.toDouble ();

			System.out.print (": " + numChannels + " " +
					  numSampleFrames + " " + sampleSize +
					  " " + sampleRate);
			alreadyRead = 18;

			if (aiff_c) {
			    sbuf.setLength (0);
			    for (int i=0; i<4; i++) {
				int ch = ModuleBase.readUnsignedByte (stream,
								      null);
				sbuf.append ((char) ch);
			    }
			    System.out.print (" " + sbuf.toString ());

			    int count = ModuleBase.readUnsignedByte (stream,
								     null);
			    alreadyRead = 23;
			    sbuf.setLength (0);
			    for (int i=0; i<count; i++) {
				int ch = ModuleBase.readUnsignedByte (stream,
								      null);
				sbuf.append ((char) ch);

				alreadyRead++;
			    }
			    System.out.print (" \"" + sbuf.toString () + "\"");
			}

		    }
		    else if (ckID.equals ("COMT")) {
			int numComments = ModuleBase.readUnsignedShort (stream,
									ENDIAN,
									null);
			System.out.print (": " + numComments);
			alreadyRead = 2;
		    }
		    else if (ckID.equals ("FVER")) {
			long timestamp = ModuleBase.readUnsignedInt (stream,
								     ENDIAN,
								     null);
			System.out.print (": " + timestamp);
			alreadyRead = 4;
		    }
		    else if (ckID.equals ("INST")) {
			int baseNote = ModuleBase.readSignedByte (stream);
			int detune = ModuleBase.readSignedByte (stream);
			int lowNote = ModuleBase.readSignedByte (stream);
			int highNote = ModuleBase.readSignedByte (stream);
			int lowVelocity = ModuleBase.readSignedByte (stream);
			int highVelocity = ModuleBase.readSignedByte (stream);
			int gain = ModuleBase.readSignedShort (stream, ENDIAN);

			System.out.print (": " + baseNote + " " + detune +
					  " " + lowNote + "," + highNote +
					  " " + lowVelocity + "," +
					  highVelocity + " " + gain);
			alreadyRead = 8;
		    }
		    else if (ckID.equals ("MARK")) {
			int numMarkers = ModuleBase.readUnsignedShort (stream,
								       ENDIAN);
			System.out.print (": " + numMarkers);
			alreadyRead = 2;
		    }
		    else if (ckID.equals ("SSND")) {
			long offset = ModuleBase.readUnsignedInt (stream,
								  ENDIAN);
			long blockSize = ModuleBase.readUnsignedInt (stream,
								     ENDIAN);
			System.out.print (": " + offset + " " + blockSize);
			alreadyRead = 8;
		    }
		    System.out.println ();

                    // Actual number of bytes to skip must be even.
                    long actSize = ckSize;
                    if ((actSize & 1) != 0) {
                        actSize++;
                    }
		    actSize -= alreadyRead;
                    stream.skipBytes ((int) actSize);
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
}
