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
import java.util.*;

/**
 * Dump contents of JPEG2000 file in human-readable format.
 */
public class J2Dump extends Dump {

    /* Fixed value for first 12 bytes */
    private static final int[] sigByte =
        {
            0X00,
            0X00,
            0X00,
            0X0C,
            0X6A,
            0X50,
            0X20,
            0X20,
            0X0D,
            0X0A,
            0X87,
            0X0A };

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
            System.err.println ("usage: java J2Dump file");
            System.exit (-1);
        }
        try {
            FileInputStream file = new FileInputStream (args[0]);
            BufferedInputStream buffer = new BufferedInputStream (file);
            DataInputStream stream = new DataInputStream (buffer);
            J2Dump dump = new J2Dump ();   // Just to access contained classes
            long os = 0;
            boolean bigEndian = true;
            int i;
            for (i = 0; i < 12; i++) {
                int ch;
                ch = stream.readUnsignedByte();
                if (ch != sigByte[i]) {
                    System.out.println ("No JPEG 2000 header");
                    System.exit (-2);
                }
            }
            os += 12;
            
            boolean endOfFile = false;
            Stack boxStack = new Stack ();
            while (!endOfFile) {
                //If there are boxes on the stack, see if there's space
                //left in the top one.
                Box boxtop;
                for (;;) {
                    boxtop = null;
                    if (boxStack.isEmpty ()) {
                        break;
                    }
                    boxtop = (Box) boxStack.peek ();
                    if (boxtop.bytesLeft > 0) {
                        break;
                    }
                    else {
                        boxStack.pop ();
                    }
                }
                
                // Read the header of a JP2 box
                Box box = dump.new Box (stream);
                try {
                    box.read ();
                }
                catch (EOFException e) {
                    endOfFile = true;
                    break;
                }
                os += box.length - box.bytesLeft;
                
                // If it's contained in a superbox, subtract
                // this box from its remaining length
                if (boxtop != null) {
                    boxtop.bytesLeft -= box.length;
                }
                System.out.println (leading (os, 8) + os + ": " + 
                    stackPrefix (boxStack) + box.type + " " + box.length);
                if (box.isSuperbox ()) {
                    boxStack.push (box);
                }
                else {
                    os += box.bytesLeft;
                    stream.skipBytes((int) box.bytesLeft);
                }
                
                // A "length" of 0 means the box occupies the rest of the file.
                if (box.length == 0) {
                    endOfFile = true;
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace (System.err);
            System.exit (-2);
        }
    }


    /* Constructs a qualifying prefix to indicate nested boxes. */
    private static String stackPrefix (Stack boxStack)
    {
        StringBuffer retval = new StringBuffer ();
        // In defiance of gravity, we rummage through the stack
        // of boxes starting at the bottom.
        for (int i = 0; i < boxStack.size(); i++) {
            Box box = (Box) boxStack.elementAt (i);
            // Remove trailing spaces from types for better readability
            retval.append (box.type.trim() + "/");
        }
        return retval.toString ();
    }



    /** Local class for defining JPEG2000 boxes. */
    class Box {
        public String type;
        public long length;
        public long bytesLeft;
        public boolean hasBoxes;
        DataInputStream dstream;
        
        public Box (DataInputStream stream)
        {
            this.dstream = stream;
        }
        
        
        /** Reads a box header and sets up for reading contents. */
        public void read () throws IOException
        {
            length = ModuleBase.readUnsignedInt (dstream, ENDIAN, null);
            long headerLength = 8;
            type = read4Chars ();
            // If the length field is 1, there is an 8-byte extended
            // length field.
            if (length == 1) {
                length = ModuleBase.readSignedLong(dstream, true, null);
                headerLength = 16;
            }
            bytesLeft = length - headerLength;
        }


        /* Reads a 4-character name */
        private String read4Chars() throws IOException {
            StringBuffer sbuf = new StringBuffer(4);
            for (int i = 0; i < 4; i++) {
                int ch = ModuleBase.readUnsignedByte(dstream, null);
                sbuf.append((char) ch);
            }
            return sbuf.toString();
        }

        /** Returns true if this box contains other boxes.
         *  At present, we don't deal with the insides of boxes
         *  that contain both data and boxes (e.g., cref). */
        public boolean isSuperbox ()
        {
            // If it's a known superbox type, we return true.
            // If we've left any out, that will merely make us
            // lose the subboxes of that type.
            String [] supertypes = { "asoc", "cgrp", "comp", "drep",
                "ftbl", "jp2h", "jpch",
                "jplh", "res ", "uuid" };
            for (int i = 0; i < supertypes.length; i++) {
                if (supertypes[i].equals (type)) {
                    return true;
                }
            }
            return false;
        }
    }


}
