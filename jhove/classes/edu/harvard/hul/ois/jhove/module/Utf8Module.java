/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2007 by JSTOR and the President and Fellows of Harvard College
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

package edu.harvard.hul.ois.jhove.module;

import edu.harvard.hul.ois.jhove.*;

import java.io.*;
import java.util.*;

/**
 *  Module for analysis of content as a UTF-8 stream.
 */
public class Utf8Module
    extends ModuleBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "UTF8-hul";
    private static final String RELEASE = "1.5";
    private static final int [] DATE = {2011, 2, 3};
    private static final String [] FORMAT = {"UTF-8"};
    private static final String COVERAGE = "Unicode 6.0.0";
    private static final String [] MIMETYPE = {"text/plain; charset=UTF-8"};
    private static final String WELLFORMED = "An UTF-8 object is well-formed "+
	"if each character is correctly encoded as a one-to-four byte " +
	"sequence, as defined in the specifications";
    private static final String VALIDITY = null;
    private static final String REPINFO = "Additional representation " +
	"information includes: number of characters and Unicode 6.0.0 code " +
	"blocks";
    private static final String NOTE = null;
    private static final String RIGHTS = "Copyright 2003-2011 by JSTOR and " +
	"the President and Fellows of Harvard College. " +
	"Released under the GNU Lesser General Public License.";

    private static final String [] POSITION = {"second", "third", "fourth"};
    private static final int CR = 0x0d;
    private static final int LF = 0x0a;

    /* Mnemonics for control characters (0-1F) */
    private static final String controlCharMnemonics[] = {
	"NUL (0x00)", "SOH (0x01)", "STX (0x02)", "ETX (0x03)", 
	"EOT (0x04)", "ENQ (0x05)", "ACK (0x06)", "BEL (0x07)",
	"BS (0x08)",  "TAB (0x09)", "LF (0x0A)",  "VT (0x0B)",
	"FF (0x0C)",  "CR (0x0D)",  "SO (0x0E)",  "SI (0x0F)",
	"DLE (0x10)", "DC1 (0x11)", "DC2 (0x12)", "DC3 (0x13)",
	"DC4 (0x14)", "NAK (0x15)", "SYN (0x16)", "ETB (0x17)",
	"CAN (0x18)", "EM (0x19)",  "SUB (0x1A)", "ESC (0x1B)",
	"FS (0x1C)",  "GS (0x1D)",  "RS (0x1E)",  "US (0x1F)"
    };

    /******************************************************************
     *PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /* Input stream wrapper which handles checksums */
    protected ChecksumInputStream _cstream;
    
    /* Data input stream wrapped around _cstream */
    protected DataInputStream _dstream;

    protected boolean _lineEndCR;
    protected boolean _lineEndLF;
    protected boolean _lineEndCRLF;
    protected int _prevChar;
    protected Map _controlCharMap;
    protected int initialBytes[];
    protected Utf8BlockMarker blockMarker;

    /* Flag to know if the property TextMDMetadata is to be added */
    protected boolean _withTextMD = false;
    /* Hold the information needed to generate a textMD metadata fragment */
    protected TextMDMetadata _textMD;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a Utf8Module.
     */
    public Utf8Module ()
    {
	super (NAME, RELEASE, DATE, FORMAT, COVERAGE, MIMETYPE, WELLFORMED,
	       VALIDITY, REPINFO, NOTE, RIGHTS, false);

	Agent agent = new Agent ("Harvard University Library",
				 AgentType.EDUCATIONAL);
	agent.setAddress ("Office for Information Systems, " +
			  "90 Mt. Auburn St., " +
			  "Cambridge, MA 02138");
	agent.setTelephone ("+1 (617) 495-3724");
	agent.setEmail("jhove-support@hulmail.harvard.edu");
	_vendor = agent;

	Document doc = new Document ("The Unicode Standard, Version 6.0",
				     DocumentType.BOOK);
	agent = new Agent ("The Unicode Consortium", AgentType.NONPROFIT);
	agent.setWeb ("http://www.unicode.org/versions/Unicode6.0.0/");
	agent.setAddress ("Mountain View, California");
	doc.setAuthor (agent);
	agent = new Agent ("Addison-Wesley", AgentType.COMMERCIAL);
	agent.setAddress ("Boston, Massachusetts");
	doc.setPublisher (agent);
	doc.setDate ("2011");
	doc.setIdentifier (new Identifier ("978-1-936213-01-6", 
			IdentifierType.ISBN));
	_specification.add (doc);

	doc = new Document ("Information technology -- Universal " +
			    "Multiple-Octet Coded Character Set (UCS) -- " +
			    "Part 1: Architecture and Basic Multilingual " +
			    "Plane. Appendix R, Amendment 2",
			    DocumentType.STANDARD);
	agent = new Agent ("ISO", AgentType.STANDARD);
	agent.setAddress ("1, rue de Varembe, Casa postale 56, " +
             "CH-1211, Geneva 20, Switzerland");
	agent.setTelephone ("+41 22 749 01 11");
	agent.setFax ("+41 22 733 34 30");
	agent.setEmail ("iso@iso.ch");
	agent.setWeb ("http://www.iso.org/");
	doc.setPublisher (agent);
	doc.setDate ("1991");
	doc.setIdentifier (new Identifier ("ISO/IEC 10646-1 Amendment 2",
					   IdentifierType.ISO));
	_specification.add (doc);

	doc = new Document ("UTF-8, a transformation format of ISO 10646",
			    DocumentType.RFC);
	agent = new Agent ("F. Yergeau", AgentType.OTHER);
	doc.setAuthor (agent);
	agent = new Agent ("IETF", AgentType.NONPROFIT);
	agent.setWeb ("http://www.ietf.org/");
	doc.setPublisher (agent);
	doc.setDate ("1998-01");
	doc.setIdentifier (new Identifier ("RFC 2279", IdentifierType.RFC));
	doc.setIdentifier (new Identifier ("http://www.ietf.org/rfc/rfc2279.txt",
					   IdentifierType.URL));
	_specification.add (doc);

    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Parsing methods.
     ******************************************************************/

    /**
     *   Parse the content of a stream digital object and store the
     *   results in RepInfo.
     * 
     *   @param stream    An InputStream, positioned at its beginning,
     *                    which is generated from the object to be parsed.
     *                    If multiple calls to <code>parse</code> are made 
     *                    on the basis of a nonzero value being returned,
     *                    a new InputStream must be provided each time.
     * 
     *   @param info      A fresh (on the first call) RepInfo object 
     *                    which will be modified
     *                    to reflect the results of the parsing
     *                    If multiple calls to <code>parse</code> are made 
     *                    on the basis of a nonzero value being returned, 
     *                    the same RepInfo object should be passed with each
     *                    call.
     *
     *   @param parseIndex  Must be 0 in first call to <code>parse</code>.  If
     *                    <code>parse</code> returns a nonzero value, it must be
     *                    called again with <code>parseIndex</code> 
     *                    equal to that return value.
     *
     */
    public final int parse (InputStream stream, RepInfo info, int parseIndex)
	throws IOException
    {
        // Test if textMD is to be generated
        if (_defaultParams != null) {
            Iterator iter = _defaultParams.iterator ();
            while (iter.hasNext ()) {
                String param = (String) iter.next ();
                if (param.toLowerCase ().equals ("withtextmd=true")) {
                    _withTextMD = true;
                }
            }
        }
       
        initParse ();
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        initialBytes = new int[4];
        
        // No line end types have been discovered.
        _lineEndCR = false;
        _lineEndLF = false;
        _lineEndCRLF = false;
        _prevChar = 0;
        _controlCharMap = new HashMap ();
        _textMD = new TextMDMetadata();

        boolean printableChars = false;
    
        info.setNote ("Additional representation information includes " +
    		      "the line endings: CR, LF, or CRLF");
        _nByte = 0;
        long nChar = 0;
        /* We may have already done the checksums while converting a
           temporary file. */
        Checksummer ckSummer = null;
        if (_je != null && _je.getChecksumFlag () &&
            info.getChecksum ().size () == 0) {
            ckSummer = new Checksummer ();
            _cstream = new ChecksumInputStream (stream, ckSummer);
            _dstream = getBufferedDataStream (_cstream, _je != null ?
                            _je.getBufferSize () : 0);
        }
        else {
            _dstream = getBufferedDataStream (stream, _je != null ?
                            _je.getBufferSize () : 0);
        }
        blockMarker = new Utf8BlockMarker();
        
        boolean eof = false;
        while (!eof) {
            try {
                boolean isMark = false;
                int [] b = new int[4];
                int ch = -1;

		/* Byte values must be valid UTF-8 encodings:                */
		/* Unicode value         Byte 1   Byte 2   Byte 3   Byte 4   */
		/* 000000000xxxxxxx      0xxxxxxx                            */
		/* 00000yyyyyxxxxxx      110yyyyy 10xxxxxx                   */
		/* zzzzyyyyyyxxxxxx      1110zzzz 10yyyyyy 10yyyyyy          */
		/* uuuuuzzzzyyyyyyxxxxxx 11110uuu 10uuzzzz 10yyyyyy 10xxxxxx */

                b[0] = readUnsignedByte (_dstream, this);
                if (_nByte < 4) {
                    isMark = checkMark (b[0], info);
                    if (info.getWellFormed () == RepInfo.FALSE) {
                        return 0;
                    }
                    if (isMark) {
                        nChar = 0;
                    }
                }

		int nBytes = 1;
		if (0xc0 <= b[0] && b[0] <= 0xdf) {
		    nBytes = 2;
		}
		else if (0xe0 <= b[0] && b[0] <= 0xef) {
		    nBytes = 3;
		}
		else if (0xf0 <= b[0] && b[0] <= 0xf7) {
		    nBytes = 4;
		}
		else if ((0x80 <= b[0] && b[0] <= 0xbf) ||
			 (0xf8 <= b[0] && b[0] <= 0xff)){
		    ErrorMessage error =
			new ErrorMessage ("Not valid first byte of UTF-8 " +
					  "encoding",
                                          "Value = " + ((char) b[0]) +
					  " (0x" + Integer.toHexString (b[0]) +
					  ")", _nByte);
		    info.setMessage (error);
		    info.setWellFormed (false);
		    return 0;
		}

		for (int i=1; i<nBytes; i++) {
		    b[i] = readUnsignedByte (_dstream, this);
                    if (_nByte < 4) {
                        isMark = checkMark (b[i], info);
                    }
                    if (info.getWellFormed () == RepInfo.FALSE) {
                        return 0;
                    }
                    
		    if (0x80 > b[i] || b[i] > 0xbf) {
			ErrorMessage error =
			    new ErrorMessage ("Not valid " + POSITION[i-1] +
					      " byte of UTF-8 endcoding",
					      "Value = " + ((char) b[i]) + " (0x" +
					      Integer.toHexString (b[i]) + ")",
                                              _nByte);
			info.setMessage (error);
			info.setWellFormed (false);
			return 0;
		    }
		}

		if (nBytes == 1) {
		    ch = b[0];
		}
		else if (nBytes == 2) {
		    ch = ((b[0]&0x1f)<<6) + (b[1]&0x3f);
		}
		else if (nBytes == 3) {
		    ch = ((b[0]&0x0f)<<12) + ((b[1]&0x3f)<<6) + (b[2]&0x3f);
		}
		else if (nBytes == 4) {
		    ch = ((b[0]&0x07)<<18) + ((b[1]&0x3f)<<12) +
			 ((b[2]&0x3f)<<6) + (b[3]&0x3f);
		}

                if (!isMark) {
                    blockMarker.markBlock(ch);
                }

		/* Track what control characters are used. */
		if (ch < 0X20 && ch != 0X0D && ch != 0X0A) {
		    _controlCharMap.put (new Integer (ch), 
					 controlCharMnemonics [ch]);
		}
		else if (ch == 0X7F) {
		    _controlCharMap.put (new Integer (ch), "DEL (0x7F)");
		}

		/* Character values U+000..U+001f,U+007f aren't printable. */
		if (ch > 0x001f && ch != 0x7f) {
		    printableChars = true;
		}

		/* Determine the line ending type(s). */
		checkLineEnd(ch);
		_prevChar = ch;

		nChar++;
	    }
	    catch (EOFException e) {
		eof = true;
                /* Catch line endings at very end. */
                checkLineEnd(0);
	    }
	}

	/* Object is well-formed UTF-8. */

        if (ckSummer != null) {
            info.setSize (_cstream.getNBytes ());
            info.setChecksum (new Checksum (ckSummer.getCRC32 (), 
					    ChecksumType.CRC32));
            String value = ckSummer.getMD5 ();
            if (value != null) {
                info.setChecksum (new Checksum (value, ChecksumType.MD5));
            }
	        if ((value = ckSummer.getSHA1 ()) != null) {
	            info.setChecksum (new Checksum (value, ChecksumType.SHA1));
	        }
	    }

	    /* Only non-zero-length files are well-formed UTF-8.
	     */
	    if (_nByte == 0) {
	        info.setMessage (new ErrorMessage ("Zero-length file"));
	        info.setWellFormed (RepInfo.FALSE);
            return 0;
        }

        /* Add the textMD information */
        _textMD.setCharset(TextMDMetadata.CHARSET_UTF8);
        _textMD.setByte_order(
            _bigEndian?TextMDMetadata.BYTE_ORDER_BIG:TextMDMetadata.BYTE_ORDER_LITTLE);
        _textMD.setByte_size("8");
        _textMD.setCharacter_size("variable");

        /* Create a metadata property for the module-specific
         * info. (4-Feb-04) */
        List metadataList = new ArrayList (4);
        info.setProperty (new Property ("UTF8Metadata",
                 PropertyType.PROPERTY,
                 PropertyArity.LIST,
                 metadataList));

        Property property = new Property ("Characters", PropertyType.LONG,
					  new Long (nChar));
        metadataList.add (property);

        property = blockMarker.getBlocksUsedProperty("UnicodeBlocks");
        if (property != null) {
            metadataList.add (property);
        }

        /* Set property reporting line ending type */
        if (_lineEndCR || _lineEndLF || _lineEndCRLF) {
            ArrayList propArray = new ArrayList(3);
            if (_lineEndCR) {
                propArray.add("CR");
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_CR);
            }
            if (_lineEndLF) {
                propArray.add("LF");
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_LF);
            }
            if (_lineEndCRLF) {
                propArray.add("CRLF");
                _textMD.setLinebreak(TextMDMetadata.LINEBREAK_CRLF);
            }
            property = new Property ("LineEndings", PropertyType.STRING,
                      PropertyArity.LIST, propArray);
            metadataList.add (property);
        }
        /* Set property reporting control characters used */
        if (!_controlCharMap.isEmpty ()) {
            LinkedList propList = new LinkedList ();
            String mnem;
            for (int i = 0; i < 0X20; i++) {
                mnem = (String) _controlCharMap.get (new Integer (i));
                if (mnem != null) {
                    propList.add (mnem);
                }
            }
	    /* need to check separately for DEL */
	    mnem = (String) _controlCharMap.get (new Integer (0X7F));
	    if (mnem != null) {
            propList.add (mnem);
	    }
	    property = new Property ("ControlCharacters", PropertyType.STRING,
				     PropertyArity.LIST, propList);
	    metadataList.add (property);
	}
	
	if (_withTextMD) {
            property = new Property ("TextMDMetadata",
                    PropertyType.TEXTMDMETADATA, PropertyArity.SCALAR, _textMD);
            metadataList.add (property);
	}
	
	if (!printableChars) {
	    info.setMessage (new InfoMessage ("No printable characters"));
	}

        return 0;
    }

    
    /**
     *  Check if the digital object conforms to this Module's
     *  internal signature information.
     *  Try to read the BOM if it's present, and check the beginning of the file.
     *
     *   @param file      A File object for the object being parsed
     *   @param stream    An InputStream, positioned at its beginning,
     *                    which is generated from the object to be parsed
     *   @param info      A fresh RepInfo object which will be modified
     *                    to reflect the results of the test
     */
    public void checkSignatures (File file,
                InputStream stream, 
                RepInfo info) 
        throws IOException
    {
        info.setFormat (_format[0]);
        info.setMimeType (_mimeType[0]);
        info.setModule (this);
        initialBytes = new int[4];
        JhoveBase jb = getBase();
        int sigBytes = jb.getSigBytes();
        int bytesRead = 0;
        blockMarker = new Utf8BlockMarker();
        boolean eof = false;
        _nByte = 0;
        long nChar = 0;
        DataInputStream dstream = new DataInputStream (stream);
        while (!eof && bytesRead < sigBytes) {
                boolean isMark = false;
                int [] b = new int[4];
                //int ch = -1;
                try {
                    b[0] = readUnsignedByte (dstream, this);
                    ++bytesRead;
                    if (_nByte < 4) {
                        isMark = checkMark (b[0], info);
                        if (info.getWellFormed () == RepInfo.FALSE) {
                            return;
                        }
                        if (isMark) {
                            nChar = 0;
                        }
                    }
                    int nBytes = 1;
                    if (0xc0 <= b[0] && b[0] <= 0xdf) {
                        nBytes = 2;
                    }
                    else if (0xe0 <= b[0] && b[0] <= 0xef) {
                        nBytes = 3;
                    }
                    else if (0xf0 <= b[0] && b[0] <= 0xf7) {
                        nBytes = 4;
                    }
                    else if ((0x80 <= b[0] && b[0] <= 0xbf) ||
                         (0xf8 <= b[0] && b[0] <= 0xff)){
                        info.setWellFormed (false);
                        return ;
                    }
                    for (int i=1; i<nBytes; i++) {
                        b[i] = readUnsignedByte (dstream, this);
                                if (_nByte < 4) {
                                    isMark = checkMark (b[i], info);
                                }
                                if (info.getWellFormed () == RepInfo.FALSE) {
                                    return;
                                }
                                
                        if (0x80 > b[i] || b[i] > 0xbf) {
                            // Not a valid UTF-8 character
                            info.setWellFormed (false);
                            return;
                        }
                    }
    
                }
                catch (EOFException e) {
                    eof = true;
                }
        }
        if (bytesRead > 0) {
            info.setSigMatch(_name);
        }
        else {
            // Don't match an empty file
            info.setWellFormed (false);
        }
    }

    /******************************************************************
     * PRIVATE INSTANCE METHODS.
     ******************************************************************/

    /** Accumulate information about line endings.
     * @param ch Current character
     */
    protected void checkLineEnd (int ch)
    {
	if (ch == LF) {
	    if (_prevChar == CR) {
		_lineEndCRLF = true;
	    }
	    else {
		_lineEndLF = true;
	    }
	}
	else if (_prevChar == CR) {
	    _lineEndCR = true;
	}
    }
    
    protected boolean checkMark (int byt, RepInfo info)
    {
        ErrorMessage msg;
        initialBytes[(int) _nByte - 1] = byt;
        if (_nByte == 3) {
            // Check for UTF-8 byte order mark in 1st 3 bytes
            if (initialBytes[0] == 0XEF &&
                    initialBytes[1] == 0XBB &&
                    initialBytes[2] == 0XBF) {
                InfoMessage im = new InfoMessage
                    ("UTF-8 Byte Order Mark signature is present", 0);
                info.setMessage (im);
                // If we've found a non-character header, clear
                // all usage blocks
                blockMarker.reset ();
                return true;
            }

            if (initialBytes[0] == 0XFF &&
                    initialBytes[1] == 0XFE) {
                if (initialBytes[2] == 0 &&
                        initialBytes[3] == 0) {
                    msg = new ErrorMessage
                        ("UCS-4 little-endian encoding, not UTF-8");
                }
                else {
                    msg = new ErrorMessage
                        ("UTF-16 little-endian encoding, not UTF-8");
                }
                info.setMessage (msg);
                info.setWellFormed (false);
                return false;
            }
            else if (initialBytes[0] == 0XFE &&
                        initialBytes[1] == 0XFF) {
                msg = new ErrorMessage
                    ("UTF-16 big-endian encoding, not UTF-8");
                info.setMessage (msg);
                info.setWellFormed (false);
                return false;
            }
        }
        return false;
    }
}
