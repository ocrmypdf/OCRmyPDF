/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;
import java.text.*;
import java.io.EOFException;
import java.io.IOException;

/**
 *  Class for Tokens which represent PDF strings.  The class maintains
 *  a field for determining whether the string is encoded as PDF encoding
 *  or UTF-16.  This is determined in the course of analyzing the
 *  characters for the token.
 */
public class Literal
    extends StringValuedToken
{
    /** True if literal is in PDFDocEncoding; false if UTF-16. */
    private boolean _pdfDocEncoding;

    /** Used for accumulating a hex string */
    private StringBuffer rawHex;
    
    /** Used for accomodating the literal */
    private StringBuffer buffer;

    /** Indicates if a character for the first half of a hex byte
        has already been buffered */
    private boolean haveHi;

    /** The high half-byte character */
    private int hi;
    
    /** First byte of a UTF-16 character. */
    int b1;

    /** First digit of a hexadecimal string value. */
    //int h1;

    /** The state of the tokenization.  Only the subset of States which
        pertain to Literals are used here. */
    private State _state;
    
    /** True if no discrepancies with PDF/A requirements have been found,
        false if there is a discrepancy in this literal. */
    private boolean _pdfACompliant;
    
    /** Depth of parenthesis nesting. */
    private int _parenLevel;

    /** Mapping between PDFDocEncoding and Unicode code points. */
    public static char [] PDFDOCENCODING = {
       '\u0000','\u0001','\u0002','\u0003','\u0004','\u0005','\u0006','\u0007',
       '\b'    ,'\t'    ,'\n'    ,'\u000b','\f'    ,'\r'    ,'\u000e','\u000f',
       '\u0010','\u0011','\u0012','\u0013','\u0014','\u0015','\u0016','\u0017',
       '\u02d8','\u02c7','\u02c6','\u02d9','\u02dd','\u02db','\u02da','\u02dc',
       '\u0020','\u0021','\"'    ,'\u0023','\u0024','\u0025','\u0026','\'',
       '\u0028','\u0029','\u002a','\u002b','\u002c','\u002d','\u002e','\u002f',
       '\u0030','\u0031','\u0032','\u0033','\u0034','\u0035','\u0036','\u0037',
       '\u0038','\u0039','\u003a','\u003b','\u003c','\u003d','\u003e','\u003f',
       '\u0040','\u0041','\u0042','\u0043','\u0044','\u0045','\u0046','\u0047',
       '\u0048','\u0049','\u004a','\u004b','\u004c','\u004d','\u004e','\u004f',
       '\u0050','\u0051','\u0052','\u0053','\u0054','\u0055','\u0056','\u0057',
       '\u0058','\u0059','\u005a','\u005b','\\'    ,'\u005d','\u005e','\u005f',
       '\u0060','\u0061','\u0062','\u0063','\u0064','\u0065','\u0066','\u0067',
       '\u0068','\u0069','\u006a','\u006b','\u006c','\u006d','\u006e','\u006f',
       '\u0070','\u0071','\u0072','\u0073','\u0074','\u0075','\u0076','\u0077',
       '\u0078','\u0079','\u007a','\u007b','\u007c','\u007d','\u007e','\u007f',
       '\u2022','\u2020','\u2021','\u2026','\u2003','\u2002','\u0192','\u2044',
       '\u2039','\u203a','\u2212','\u2030','\u201e','\u201c','\u201d','\u2018',
       '\u2019','\u201a','\u2122','\ufb01','\ufb02','\u0141','\u0152','\u0160',
       '\u0178','\u017d','\u0131','\u0142','\u0153','\u0161','\u017e','\u009f',
       '\u20ac','\u00a1','\u00a2','\u00a3','\u00a4','\u00a5','\u00a6','\u00a7',
       '\u00a8','\u00a9','\u00aa','\u00ab','\u00ac','\u00ad','\u00ae','\u00af',
       '\u00b0','\u00b1','\u00b2','\u00b3','\u00b4','\u00b5','\u00b6','\u00b7',
       '\u00b8','\u00b9','\u00ba','\u00bb','\u00bc','\u00bd','\u00be','\u00bf',
       '\u00c0','\u00c1','\u00c2','\u00c3','\u00c4','\u00c5','\u00c6','\u00c7',
       '\u00c8','\u00c9','\u00ca','\u00cb','\u00cc','\u00cd','\u00ce','\u00cf',
       '\u00d0','\u00d1','\u00d2','\u00d3','\u00d4','\u00d5','\u00d6','\u00d7',
       '\u00d8','\u00d9','\u00da','\u00db','\u00dc','\u00dd','\u00de','\u00df',
       '\u00e0','\u00e1','\u00e2','\u00e3','\u00e4','\u00e5','\u00e6','\u00e7',
       '\u00e8','\u00e9','\u00ea','\u00eb','\u00ec','\u00ed','\u00ef','\u00ef',
       '\u00f0','\u00f1','\u00f2','\u00f3','\u00f4','\u00f5','\u00f6','\u00f7',
       '\u00f8','\u00f9','\u00fa','\u00fb','\u00fc','\u00fd','\u00fe','\u00ff'
    };


    private static final int CR = 0x0D;
    private static final int LF = 0x0A;
    private static final int BS = 0x08;
    private static final int HT = 0x09;
    private static final int FORMFEED = 0x0C;
    private static final int ESC = 0X1B;
    private static final int OPEN_PARENTHESIS = 0x28;
    private static final int CLOSE_PARENTHESIS = 0x29;
    private static final int BACKSLASH = 0x5C;
    private static final int FE = 0xFE;
    private static final int FF = 0xFF;

    /** Creates an instance of a string literal */
    public Literal ()
    {
        super ();
        _pdfDocEncoding = true;
        rawHex = new StringBuffer ();
        buffer = new StringBuffer ();
        haveHi = false;
    }

    /**
     *  Append a hex character.  This is used only for hex literals
     *  (those that start with '<'). 
     *
     *  @param  ch	The integer 8-bit code for a hex character
     */
    public void appendHex (int ch) throws PdfException
    {
        if (_rawBytes == null) {
            _rawBytes = new Vector (32);
        }
        if (haveHi) {
            _rawBytes.add(new Integer (hexToInt (hi, ch)));
            haveHi = false;
        }
        else {
            hi = ch;
            haveHi = true;
        }
    }
    
    /**
     *  Process the incoming characters into a string literal.  
     *  This is used for literals delimited
     *  by parentheses, as opposed to hex strings.
     *
     *  @param  tok   The tokenizer, passed to give access to its getChar
     *               function.
     *  @return      <code>true</code> if the character was processed
     *               normally, <code>false</code> if a terminating
     *               parenthesis was reached.
     */
    public long processLiteral (Tokenizer tok) throws IOException
    {
        /** Variable for UTF-16 chars. */
        int utfch = 0;
        /** First byte of a UTF-16 character. */
        int b1 = 0x00;
        /*  Character read from tokenizer. */
        int ch;
        _parenLevel = 0;
        _rawBytes = new Vector (32);
        _state = State.LITERAL;

	long offset = 0;
        for (;;) {
            ch = tok.readChar ();
            // If we get -1, then we've hit an EOF without proper termination of
            // the literal. Throw an exception.
            if (ch < 0) {
                throw new EOFException ("Unterminated literal in PDF file");
            }
            offset++;
            _rawBytes.add (new Integer (ch));

            if (_state == State.LITERAL) {
                // We are still in a state of flux, determining the encoding
                if (ch == FE) {
                    _state = State.LITERAL_FE;
                }
                else if (ch == CLOSE_PARENTHESIS && --_parenLevel < 0) {
                    // We have an empty string
                    setPDFDocEncoding (true);
                    setValue(buffer.toString());
                    return offset;
                }
                else if (ch == BACKSLASH) {
                    ch = readBackslashSequence (false, tok);
                    if (ch == 0) {
                        continue;  // invalid character, ignore
                    }
                    else if (ch == FE) {
                        _state = State.LITERAL_FE;
                    }
                    else {
                        // any other char is treated nonspecially
                        setPDFDocEncoding (true);
                        buffer.append (PDFDOCENCODING[ch]);
                    }
                }
                else {
                    // We now know we're in 8-bit PDF encoding.
                    // Append the character to the buffer.
                    if (ch == OPEN_PARENTHESIS) {
                        // Count open parens to be matched by close parens.
                        // Backslash-quoted parens won't get here.
                        ++_parenLevel;
                    }
                    _state = State.LITERAL_PDF;
                    setPDFDocEncoding (true);
                    buffer.append (PDFDOCENCODING[ch]);
                }
            }
            else if (_state == (State.LITERAL_FE)) {
                if (ch == FF) {
                    _state = State.LITERAL_UTF16_1;
                    setPDFDocEncoding (false);
                }
                else if (ch == BACKSLASH) {
                    ch = readBackslashSequence (false, tok);
                    if (ch == 0) {
                        continue;  // invalid character, ignore
                    }
                    if (ch == FF) {
                        _state = State.LITERAL_UTF16_1;
                        setPDFDocEncoding (false);
                    }
                    else {
                        // any other char is treated nonspecially
                        setPDFDocEncoding (true);
                        // The FE is just an FE, put it in the buffer
                        buffer.append (PDFDOCENCODING[FE]);
                        buffer.append (PDFDOCENCODING[ch]);
                    }
                }
                else {
                    _state = State.LITERAL_PDF;
                    setPDFDocEncoding (true);
                    // The FE is just an FE, put it in the buffer
                    buffer.append (PDFDOCENCODING[FE]);
                    buffer.append (PDFDOCENCODING[ch]);
                }
            }
            else if (_state == (State.LITERAL_PDF)) {
                if (ch == CLOSE_PARENTHESIS && --_parenLevel < 0) {
                    setValue(buffer.toString());
                    return offset;
                }
                else if (ch == BACKSLASH) {
                    ch = readBackslashSequence (false, tok);
                    if (ch == 0) {
                        continue;  // invalid character, ignore
                    }
                    else {
                        // any other char is treated nonspecially
                        buffer.append (PDFDOCENCODING[ch]);
                    }
                }
                else {
                    buffer.append (PDFDOCENCODING[ch]);
                }
            }
            else if (_state == (State.LITERAL_UTF16_1)) {
                // First byte of a UTF16 character.  But a close
                // paren or backslash is a single-byte character.
                // Parens within the string are double-byte characters,
                // so we don't have to worry about them.
                if (ch == CLOSE_PARENTHESIS) {
                    setValue(buffer.toString());
                    return offset;
                }
                else if (ch == BACKSLASH) {
                    utfch = readBackslashSequence (true, tok);
                    if (utfch == 0) {
                        continue;  // invalid character, ignore
                    }
                }
                else {
                    _state = State.LITERAL_UTF16_2;
                    b1 = ch;
                }
            }
            else if (_state == (State.LITERAL_UTF16_2)) {
                // Second byte of a UTF16 character.
                utfch = 256 * b1 + ch;
                _state = State.LITERAL_UTF16_1;
                // an ESC may appear at any point to signify
                // a language code.  Remove the language code
                // from the stream and save it in a list of codes.
                if (utfch == ESC) {
                    readUTFLanguageCode (tok);
                }
                else {
		    /* It turns out that a backslash may be double-byte,
		     * rather than the assumed single.byte.  The following
		     * allows for this. Suggested by Justin Litman, Library
		     * of Congress, 2006-03-17.
		     */
		    if (utfch == BACKSLASH) {
			utfch = readBackslashSequence (false, tok);
			if (utfch == 0) {
			    continue;   /* Invalid character, ignore. */
			}
		    }
                    buffer.append ((char) utfch);
                }
            }
        }
    }



    /**
     *  Convert the raw hex data.  Two buffers are saved: _rawBytes
     *  for the untranslated hex-encoded data, and _value for the
     *  PDF or UTF encoded string.
     */
    public void convertHex () throws PdfException
    {
        boolean utf = false;
        StringBuffer buffer = new StringBuffer ();
        // If a high byte is left hanging, complete it with a '0'
        if (haveHi) {
            _rawBytes.add (new Integer (hexToInt (hi, '0')));
        }
        if (_rawBytes.size () >= 2 && rawByte (0) == 0XFE &&
                        rawByte(1) == 0XFF) {
            utf = true;
        }
        if (utf) {
            // Gather pairs of bytes into characters without conversion
            for (int i = 2; i < _rawBytes.size(); i += 2) {
                buffer.append 
                    ((char) (rawByte (i) * 256 + rawByte (i + 1)));
            }
        }
        else {
            // Convert single bytes to PDF encoded characters.
            for (int i = 0; i < _rawBytes.size (); i++) {
                buffer.append (Tokenizer.PDFDOCENCODING[rawByte (i)]);
            }
        }
        _value = buffer.toString ();
    }
    
    private static int hexToInt (int c1, int c2) throws PdfException
    {
        return 16 * hexValue (c1) + hexValue (c2);
    }

    private static int hexValue (int h) throws PdfException
    {
        int d = 0;
        if (0x30 <= h && h <= 0x39) {
            // digit 0-9
            d = h - 0x30;
        }
        else if (0x41 <= h && h <= 0x46) {
            // letter A-F
            d = h - 0x37;
        }
        else if (0x61 <= h && h <= 0x66) {
            // letter a-f
            d = h - 0x57;
        }
        else {
            throw new PdfMalformedException ("Invalid character in hex string");
        }
        return d;
    }


    /* Extract a byte from _rawBytes. In order to allow for byte-short
       situations, any byte off the end is returned as 0. */
    private int rawByte (int idx)
    {
        if (idx >= _rawBytes.size ()) {
            return 0;
        }
        return ((Integer) _rawBytes.elementAt (idx)).intValue();
    }


    /**
     *  Returns <code>true</code> if this string is in PDFDocEncoding,
     *  false if UTF-16.
     */
    public boolean isPDFDocEncoding ()
    {
        return _pdfDocEncoding;
    }

    /**
     *  Sets the value of pDFDocEncoding.
     */
    public void setPDFDocEncoding (boolean pdfDocEncoding)
    {
        _pdfDocEncoding = pdfDocEncoding;
    }

    /**
     *  Returns <code>true</code> if the string value is a parsable date.
     *  Conforms to the ASN.1 date format: D:YYYYMMDDHHmmSSOHH'mm'
     *  where everything before and after YYYY is optional.
     *  If we take this literally, the format is frighteningly ambiguous
     *  (imagine, for instance, leaving out hours but not minutes and
     *  seconds), so the checking is a bit loose.
     */
    public boolean isDate ()
    {
        return parseDate () != null;
    }

    /**
     *  Parse the string value to a date. PDF dates conform to
     *  the ASN.1 date format.  This consists of
     *  D:YYYYMMDDHHmmSSOHH'mm'
     *  where everything before and after YYYY is optional.
     *  Adobe doesn't actually say so, but I'm assuming that if a
     *  field is included, everything to its left must be included,
     *  e.g., you can't have seconds but leave out minutes.
     */
    public Date parseDate ()
    {
        int year = 0;
        int month = 0;
        int day = 0;
        int hour = 0;
        int minute = 0;
        int second = 0;
        char timezonechar = '?';    // +, -, or Z
        int timezonehour = 0;
        int timezoneminute = 0;
        Calendar cal = null;

        String str = getValue ();
        if (str == null) {
	    return null;
	}
	str = str.trim ();
	if (str.length() < 4) {
            return null;
        }
        int datestate = 0;
        int charidx = 0;
        try {
          wloop:
          while (charidx < str.length ()) {
            // We parse the date using a simple state machine,
            // with a state for each date component.
            switch (datestate) {
                case 0:  // starting state, may start with "D:"
                if ("D:".equals (str.substring (charidx, charidx + 2))) {
                    charidx += 2;
                }
                datestate = 1;  // advance regardless
                break;

                case 1:  // expecting year
                year = Integer.parseInt (str.substring (charidx, charidx + 4));
                charidx += 4;
                datestate = 2;
                break;
                
                case 2:  // expecting month
                month = Integer.parseInt (str.substring (charidx, charidx+2));
                charidx += 2;
                datestate = 3;
                break;
                
                case 3:  // expecting day of month
                day = Integer.parseInt (str.substring (charidx, charidx + 2));
                if (day < 1 || day > 31) {
                    return null;
                }
                charidx += 2;
                datestate = 4;
                break;
                
                case 4:  // expecting hour (00-23)
                hour = Integer.parseInt (str.substring (charidx, charidx + 2));
                charidx += 2;
                datestate = 5;
                break;
                
                case 5:  // expecting minute (00-59)
                minute = Integer.parseInt (str.substring (charidx, charidx+2));
                charidx += 2;
                datestate = 6;
                break;
                
                case 6:  // expecting second (00-59)
                second = Integer.parseInt (str.substring (charidx, charidx+2));
                charidx += 2;
                datestate = 7;
                break;
                
                case 7:  // expecting time zone ('+', '-', or 'Z')
                timezonechar = str.charAt (charidx);
                if (timezonechar != 'Z' && timezonechar != '+' &&
		    timezonechar != '-') {
                    return null;
		}
                charidx++;
                datestate = 8;
                break;
                
                case 8:  // expecting time zone hour.
                // ignore if timezonechar is 'Z'
                if (timezonechar == '+' || timezonechar == '-') {
                    timezonehour = Integer.parseInt (str.substring (charidx,
							    charidx + 2));
                    if (timezonechar == '-') {
                        timezonehour = -timezonehour;   
                    }
		    // Time zone hour must have trailing quote
		    if (!str.substring (charidx+2, charidx+3).equals ("'")) {
			return null;
		    }
		    charidx += 3;
                }
                datestate = 9;
                break;
                
                case 9:  // expecting time zone minute -- in single quotes
                // ignore if timezonechar is 'Z'
                if (timezonechar == '+' || timezonechar == '-') {
                    if (str.charAt (charidx) == '\'') {
                        timezoneminute =
			    Integer.parseInt (str.substring (charidx,
							     charidx + 2));
                    }
                    if (timezonechar == '-') {
                        timezoneminute = -timezoneminute;
                    }
		    // Time zone minute must have trailing quote
		    if (!str.substring (charidx+2, charidx+3).equals ("'")) {
			return null;
		    }
                }
                break wloop;              
            }
          }
        }
        // Previously, we assumed that a parsing exception meant the
        // end of the date.  This is too permissive; an exception means
	// that the date is not well-formed.
        catch (Exception e) {
	    return null;
        }
        if (datestate < 2) {
            return null;    // not enough fields
        }
        else {
            // First we must construct the time zone string, then use
            // it to make a TimeZone object.
            if (timezonechar != '?') {
                String tzStr = "GMT";
                if (timezonechar == 'Z') {
                    tzStr += "+0000";
                }
                else {
                    tzStr += timezonechar;
                    NumberFormat nfmt = NumberFormat.getInstance ();
                    nfmt.setMinimumIntegerDigits (2);
                    nfmt.setMaximumIntegerDigits (2);
                    tzStr += nfmt.format (timezonehour);
                    tzStr += nfmt.format (timezoneminute);
                }
                TimeZone tz = TimeZone.getTimeZone (tzStr);
                
                // Use that TimeZone to create a Calendar with our date.
                // Note that Java months are 0-based.
                cal = Calendar.getInstance (tz);
            }
            else {
                // time zone is unspecified
                cal = Calendar.getInstance ();
            }
            cal.set (year, month - 1, day, hour, minute, second);
            return cal.getTime ();
        }
    }


    /** 
     *  Returns <code>true</code> if this token doesn't violate any
     *  PDF/A rules, <code>false</code> if it does.
     */
    public boolean isPDFACompliant ()
    {
        return _pdfACompliant;
    }
    
    
/*    private void beginBackslashState ()
    {
        octalBufLen = 0;
        backslashFlag = true;
    }
*/



    /** After a backslash, read characters into an escape
        sequence.  If we don't find a valid escape sequence,
        return 0.
     */
    private int readBackslashSequence (boolean utf16, Tokenizer tok) 
                throws IOException 
    {
        int ch = tok.readChar1 (utf16);
        if (ch >= 0X30 && ch <= 0X37) {
            int num = ch - 0X30;
            // Read octal sequence.  We may get 1, 2, or 3 characters.
            // If we get a non-numeric character, we're done and we
            // put it back.
            for (int i = 0; i < 2; i++) {
                int ch1 = tok.readChar1 (utf16);
                if (ch1 >= 0X30 && ch1 <= 0X37) {
                    num = num * 8 + (ch1 - 0X30);
                }
                else {
                    //_fileBufferOffset--;   // put it back
                    tok.backupChar ();       // add this function to Tokenizer****
                    _pdfACompliant = false;  // octal sequences must be 3 chars in PDF/A
                    return num;
                }
            }
            return num;
        }
        switch (ch) {
            case 0X6E:   // n
                return LF;
            case 0X72:   // r
                return CR;
            case 0X74:   // t
                return HT;
            case 0X68:   // h
                return BS;
            case 0X66:   // f
                return FORMFEED;
            case OPEN_PARENTHESIS:
                return OPEN_PARENTHESIS;
            case CLOSE_PARENTHESIS:
                return CLOSE_PARENTHESIS;
            case BACKSLASH:
                return BACKSLASH;
            default:
                return 0;
        }
    }


    /** We have just read an ESC in a UTF string. 
        Save all character up to and exclusive of the next ESC
        as a language code. 
     */
    private void readUTFLanguageCode (Tokenizer tok) throws IOException
    {
        StringBuffer sb = new StringBuffer ();
        for (;;) {
            int ch = tok.readChar1(true);
            if (ch == ESC) {
                break;
            }
            sb.append ((char) ch);
        }
        tok.addLanguageCode (sb.toString ());   // ****add this to Tokenizer
        //_languageCodes.add (sb.toString ());
    }

    /** If we're in the backslash substate (backslashFlag = true), then call
        this to process characters.  It will accumulate octal digits into
        octalBuf and process other escaped characters.  If the accumulation
        produces a character, it will return that character code, otherwise
        it will return 0 to indicate no character is available yet.
        
        Althought the backslash itself is a byte, even in a 16-bit
        string, the characters which follow it are 16-bit characters,
        not bytes.  So we call this only after applying UTF-16 encoding
        where applicable.
     */
     
    /* DEPRECATED for the current millisecond */
/*    private int backslashProcess (int ch) 
    {
        if (ch >= 0X30 && ch <= 0X37) {
            int num = ch - 0X30;
            // An octal sequence may have 1, 2, or 3 characters.
            // If we get a non-numeric character, we're done and
            // return the character, and put the character we
            // just received into a holding buffer.  
            octalBuf[octalBufLen++] = num;
            if (octalBufLen == 3) {
                return octalBufValue ();
            }
            for (int i = 0; i < 2; i++) {
                int ch1 = readChar1 (utf16);
                if (ch1 >= 0X30 && ch1 <= 0X37) {
                    num = num * 8 + (ch1 - 0X30);
                }
                else {
                    holdChar = ch;
                    _pdfACompliant = false;  // octal sequences must be 3 chars in PDF/A
                    return num;
                }
            }
            return num;
        }
        
        // If no octal characters have been seen yet, look for an
        // escaped character.
        if (octalBufLen == 0) {
            switch (ch) {
                case 0X6E:   // n
                    return LF;
                case 0X72:   // r
                    return CR;
                case 0X74:   // t
                    return HT;
                case 0X68:   // h
                    return BS;
                case 0X66:   // f
                    return FORMFEED;
                case OPEN_PARENTHESIS:
                    return OPEN_PARENTHESIS;
                case CLOSE_PARENTHESIS:
                    return CLOSE_PARENTHESIS;
                case BACKSLASH:
                    return BACKSLASH;
                default:
                    // illegal escape -- dump the character
                    return 0;
            }
            else {
                // We have one or two buffered octal characters,
                // but this isn't one.  Put the current character
                // in a holding buffer, and return the octal value.
                holdCh = ch;
                return octalBufValue ();
            }
        }
    }
 */       
}


