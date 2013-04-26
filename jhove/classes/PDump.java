/**********************************************************************
 * PDump - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
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
import edu.harvard.hul.ois.jhove.module.pdf.*;
import java.io.*;

/**
 * Dump contents of PDF file in human-readable format.
 */
public class PDump
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
	    System.err.println ("usage: java PDump file");
	    System.exit (-1);
	}

	try {
	    RandomAccessFile file = new RandomAccessFile (args[0], "r");
	    Tokenizer tokenizer = new FileTokenizer (file);
	    Token token = null;
	    long offset = 0;
	    while ((token = tokenizer.getNext ()) != null) {
		System.out.print (leading (offset, 8) + offset + ": ");
		if (token instanceof ArrayEnd) {
		    System.out.println ("ArrayEnd");
		}
		else if (token instanceof ArrayStart) {
		    System.out.println ("ArrayStart");
		}
		else if (token instanceof Comment) {
		    System.out.println ("Comment \"" +
					((Comment) token).getValue () + "\"");
		}
		else if (token instanceof DictionaryEnd) {
		    System.out.println ("DictionaryEnd");
		}
		else if (token instanceof DictionaryStart) {
		    System.out.println ("DictionaryStart");
		}
//		else if (token instanceof Hexadecimal) {
//		    System.out.println ("Hexadecimal[" +
//					(((Hexadecimal) token).isPDFDocEncoding () ?
//					  "PDF" : "UTF-16") + "] \"" +
//					((Hexadecimal) token).getValue () +
//					"\"");
//		}
		else if (token instanceof Keyword) {
		    System.out.println ("Keyword \"" +
					((Keyword) token).getValue () + "\"");
		}
		else if (token instanceof Literal) {
		    System.out.println ("Literal[" +
					(((Literal)token).isPDFDocEncoding () ?
					 "PDF" : "UTF-16") + "] \"" +
					((Literal) token).getValue () + "\"");
		}
		else if (token instanceof Name) {
		    System.out.println ("Name \"" +
					((Name) token).getValue () + "\"");
		}
		else if (token instanceof Numeric) {
		    Numeric numeric = (Numeric) token;
		    if (numeric.isReal ()) {
			System.out.println ("Numeric " + numeric.getValue ());
		    }
		    else {
			System.out.println ("Numeric " +
					    numeric.getIntegerValue ());
		    }
		}
		else if (token instanceof Stream) {
		    System.out.println ("Stream " +
					((Stream) token).getLength ());
		}
		else {
		    System.out.println (token);
		}
		offset = tokenizer.getOffset ();
	    }
	}
	catch (Exception e) {
	    e.printStackTrace (System.err);
	    System.exit (-2);
	}
    }
}
