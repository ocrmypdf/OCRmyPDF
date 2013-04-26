/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.*;
import java.util.*;

/**
 *  Tokenizer for PDF files.  
 *  This is used in conjunction with the Parser, which assembled
 *  Tokens into higher-level constructs.
 */
public abstract class Tokenizer
{
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
    private static final int POUND_SIGN = 0x23;
    private static final int PERCENT_SIGN = 0x25;
    private static final int OPEN_PARENTHESIS = 0x28;
    private static final int CLOSE_PARENTHESIS = 0x29;
    private static final int PLUS = 0x2B;
    private static final int MINUS = 0x2D;
    private static final int PERIOD = 0x2E;
    private static final int SLASH = 0x2F;
    private static final int LESS_THAN = 0x3C;
    private static final int GREATER_THAN = 0x3E;
    private static final int OPEN_BRACKET = 0x5B;
    private static final int BACKSLASH = 0x5C;
    private static final int CLOSE_BRACKET = 0x5D;
    private static final int a = 0x61;
    private static final int d = 0x64;
    private static final int e = 0x65;
    private static final int m = 0x6D;
    private static final int n = 0x6E;
    private static final int r = 0x72;
    private static final int s = 0x73;
    private static final int t = 0x74;
    //private static final int FE = 0xFE;
    //private static final int FF = 0xFF;

    //private static final String CRLF = "" + CR + LF;

    /** Delimiter character codes. */
    private static final int DELIMITER [] = {
        PERCENT_SIGN, OPEN_PARENTHESIS, CLOSE_PARENTHESIS, SLASH, LESS_THAN,
        GREATER_THAN, OPEN_BRACKET, CLOSE_BRACKET,
        0x7B,  /* { */
        0x7D   /* } */
    };

    /** Whitespace character codes. */
    private static final int WHITESPACE [] = {
        0x00,  /* NUL */
        0x09,  /* HT */
        LF,    /* LF */
        0x0C,  /* FORMFEED */
        CR,    /* CR */
        0x20   /* SP */
    };

    /** Source from which to read bytes. */
    protected RandomAccessFile _file;

    /** Character code of current character. */
    protected int _ch;

    /** If true, use the look-ahead character, rather than reading from
        the file. */
    private boolean _lookAhead;

    /** Current offset into file for reporting purposes. */
    private long _offset;

    /* Current parse state. */
    private State _state;

    /* White space string. */
    private String _wsString;
    
    /* PDF/A compliance flag. */
    private boolean _pdfACompliant;

    /* Encryption flag. */
    private boolean _encrypted;
    
    /* Set of language codes used in UTF strings. */
    private Set _languageCodes;
    
    /* Level of nesting of parentheses in a literal; zero is the base 
       level. */
    private int _parenLevel;

    /** Scan mode. If true do not attempt to parse non-whitespace delimited
     * tokens, e.g., literal and hexadecimal strings. */
    private boolean _scanMode;

    /** 
     *  Constructor.
     */
    public Tokenizer ()
    {
        _state = State.WHITESPACE;
        _wsString = "";
        _lookAhead = false;
        _ch = 0;
        _offset = 0;
        _languageCodes = new TreeSet ();
        _pdfACompliant = true;
	_scanMode = false;
    }

    /**
     *  Parses out and returns a token from the input file.
     *  If it hits the end of the file, returns null.  
     *  Other parsing problems cause an exception to be thrown.
     *  When an exception is thrown, the state is changed to
     *  WHITESPACE, so the parser can get back in sync more easily.
     */
    public Token getNext ()
        throws IOException, PdfException
    {
	return getNext (0L);
    }

    /**
     *  Parses out and returns a token from the input file.
     *  If it hits the end of the file, returns null.  
     *  Other parsing problems cause an exception to be thrown.
     *  When an exception is thrown, the state is changed to
     *  WHITESPACE, so the parser can get back in sync more easily.
     * @param max Maximum allowable size of the token
     */
    public Token getNext (long max)
        throws IOException, PdfException
    {
        String tokErr = "Lexical error";
        Token token = null;
        StringBuffer buffer = null;
        //StringBuffer bkslBuffer = null;
        _state = State.WHITESPACE;
        _wsString = "";
        /** Numeric sign. */
        boolean negative = false;
        /** Floating value. */
        double realValue = 0.0;
        /** Integer value. */
        long intValue = 0;
        /** Numeric fractional positional unit. */
        double denom = 10.0;
        /** Stream length. */
        long length = 0L;
        /** Last character seen in stream but one. */
        int prelastch = 0;
        /** Last character seen in stream. */
        int lastch = 0;
        /** First byte of a UTF-16 character. */
        //int b1 = 0x00;
        /** First digit of a hexadecimal string value. */
        //int h1 = 0x00;
        /** Variable for UTF-16 chars. */
        //int utfch = 0;
        /** Line break flag for the beginning of a data stream. */
        boolean sawLineBreak = false;
        /** Carriage return flag for the beginning of a data stream. */
        boolean sawCR = false;

	long startOffset = _offset;
        try {
            while (true) {
		if (max > 0L) {
		    if (_offset - startOffset > max) {

			/* The token has exceeded the specified maximum size.*/

			if (token != null &&
			    token instanceof StringValuedToken &&
			    buffer != null) {
			    ((StringValuedToken) token).setValue (
							  buffer.toString ());
			}
			else {
			    token = null;
			}
			return token;
		    }
		}

                if (!_lookAhead) {
                    _ch = readChar ();
                    if (_ch < 0) {
                        _state = State.WHITESPACE;
                        throw new PdfMalformedException("Unexpected EOF",
							_offset);
                    }
                    _offset++;
                }
                else {
                    _lookAhead = false;
                }

                if (_state == (State.WHITESPACE)) {

                    // We are not in the middle of a token.
                    // Anything we read here starts a token
                    // or continues whitespace.

                    if (isWhitespace (_ch)) {
                        _wsString += (char) _ch;
                    }
                    else if (_ch == OPEN_BRACKET) {
                        _state = State.WHITESPACE;
                        _wsString = "";

                        return new ArrayStart ();
                    }
                    else if (_ch == CLOSE_BRACKET) {
                        _state = State.WHITESPACE;
                        _wsString = "";

                        return new ArrayEnd ();
                    }
                    else if (_ch == PERCENT_SIGN) {
                        _state = State.COMMENT;
                        buffer = new StringBuffer ();
                        token  = new Comment ();
                    }
                    else if (_ch == PLUS || _ch == MINUS) {
                        _state = State.NUMERIC;
                        intValue = 0;
                        negative = ((_ch == MINUS) ? true : false);
                        token = new Numeric ();
                    }
                    else if (_ch == PERIOD) {
                        _state = State.FRACTIONAL;
                        realValue = 0.0;
                        negative = false;
                        denom = 10.0;
                        token = new Numeric ();
                    }
                    else if (isNumeral (_ch)) {
                        _state = State.NUMERIC;
                        intValue = _ch - 48;
                        denom = 10.0;
                        token = new Numeric ();
                        //((Numeric) token).setReal (false);
                    }
                    else if (_ch == SLASH) {
                        _state = State.NAME;
                        buffer = new StringBuffer ();
                        token = new Name ();
                    }
                    else if (_ch == OPEN_PARENTHESIS) {
			if (!_scanMode) {
			    _state = State.LITERAL;
			    _parenLevel = 0;
			    token = new Literal ();
			    buffer = new StringBuffer ();
			}
		    }
                    else if (_ch == LESS_THAN) {
                        _state = State.LESS_THAN;
                    }
                    else if (_ch == GREATER_THAN) {
                        _state = State.GREATER_THAN;
                    }
                    else if (!isDelimiter (_ch)) {
                        _state = State.KEYWORD;
                        buffer = new StringBuffer ();
                        buffer.append ((char) _ch);
                        token = new Keyword ();
                    }
                    // end State.WHITESPACE
                }
                else if (_state == (State.COMMENT)) {
                    
                    // We are in a comment.  Only a line ender can
                    // get us out.

                    if (_ch == CR || _ch == LF) {
                        _state = State.WHITESPACE;
                        _wsString += (char) _ch;
                        ((StringValuedToken)token).setValue(buffer.toString());
                        if (!token.isPdfACompliant()) {
                            _pdfACompliant = false;
                        }
                        return token;
                    }
                    else {
                        buffer.append ((char) _ch);
                    }
                }
                else if (_state == (State.FRACTIONAL)) {

                    // We are reading a number and have encountered
                    // a decimal point.
                    if (isDelimiter (_ch) || isWhitespace (_ch)) {
                        _state = State.WHITESPACE;
                        _wsString = "" + (char) _ch;
                        if (negative) {
                            realValue = - realValue;
                        }
                        ((Numeric) token).setValue (realValue);

                        if (isDelimiter (_ch)) {
                            _lookAhead = true;
                        }

                        if (!token.isPdfACompliant()) {
                            _pdfACompliant = false;
                        }
                        return token;
                    }
                    else if (isNumeral (_ch)) {
                        realValue = realValue + ((_ch - 48)/denom);
                        denom *= 10.0;
                    }
                    else {
                        // invalid character in a number
                        _state = State.WHITESPACE;
                        _wsString = "";
                        throw new PdfMalformedException (tokErr, _offset);
		    }
                }
                else if (_state == (State.GREATER_THAN)) {
                    // ">" must be followed by another > as a dict end
                    if (_ch == GREATER_THAN) {
                        _state = State.WHITESPACE;
                        _wsString = "";
                        return new DictionaryEnd ();
                    }
                    else {
                        _state = State.WHITESPACE;
                        _wsString = "";
                        throw new PdfMalformedException (tokErr, _offset);
                    }
                }
                else if (_state == (State.HEXADECIMAL)) {
                    // We're in a hexadecimal string.  We will
                    // transition from this state to a state which
                    // indicates the encoding used.

                    if (_ch == GREATER_THAN) {
                        // A ">" terminates the string.
                        _state = State.WHITESPACE;
                        _wsString = "";
                        ((Literal) token).convertHex ();
                        //buffer.append (PDFDOCENCODING[hexToInt (h1, 0x30)]);
                        //((StringValuedToken)token).setValue(buffer.toString());

                        return token;
                    }
                    else if (!isWhitespace (_ch)) {
                        ((Literal) token).appendHex (_ch);
                    }
                }
                else if (_state == (State.KEYWORD)) {
                    if (isDelimiter (_ch) || isWhitespace (_ch)) {
                        if (isDelimiter (_ch)) {
                            _lookAhead = true;
                        }
                        if (buffer.toString ().equals ("stream")) {
                            // Streams can't be nested, so this is (or better be)
                            // a FileTokenizer.
                            _state = State.STREAM;
                            sawLineBreak = (_ch == LF);
                            sawCR = (_ch == CR);
                            token = new Stream ();
                            length = 0L;
                            lastch = 0;
                            prelastch = 0;
                            initStream ((Stream) token);
                        }
                        else {
                            _state = State.WHITESPACE;
                            _wsString = "" + (char) _ch;
                            ((StringValuedToken) token).setValue
                                                          (buffer.toString ());
                            if (!token.isPdfACompliant()) {
                                _pdfACompliant = false;
                            }
                            return token;
                        }
                    }
                    else {
                        buffer.append ((char) _ch);
                    }
                }
                else if (_state == (State.LESS_THAN)) {
                    // The last character was "<".  If followed
                    // by another "<", it's the opening token
                    // for a dictionary.  Otherwise it's the
                    // beginning of a hexadecimal character string.
                    if (_ch == LESS_THAN || _scanMode) {
                        _state = State.WHITESPACE;
                        _wsString = "";
                        return new DictionaryStart ();
                    }
                    else {
                        _state = State.HEXADECIMAL;
                        token = new Literal ();
                        buffer = new StringBuffer ();
                        ((Literal) token).appendHex (_ch);
                        //h1 = _ch;
                    }
                }
                else if (_state == (State.LITERAL)) {
                    backupChar ();
                    _offset += ((Literal) token).processLiteral (this) - 1;
                    _state = State.WHITESPACE;
                    _wsString = "";
                    return token;
                }
                else if (_state == (State.NAME)) {
                    if (_ch == POUND_SIGN) {
                        // The pound sign can be used as an escape in
                        // a name; it is followed by two hex characters.
                        int ch1 = readChar ();
                        int ch2 = readChar ();
                        _ch = (hexValue(ch1) << 8) +
                                hexValue (ch2);
                        // Will throw a PDFException if not hex
                    }
                    if (isDelimiter (_ch) || isWhitespace (_ch)) {
                        _state = State.WHITESPACE;
                        ((StringValuedToken)token).setValue(buffer.toString());
                    
                        if (isDelimiter (_ch)) {
                            _lookAhead = true;
                            _wsString = "";
                        }
                        else {
                            _wsString = "" + (char) _ch;
                        }

                        if (!token.isPdfACompliant()) {
                            _pdfACompliant = false;
                        }
                        return token;
                    }
                    else {
                        buffer.append ((char) _ch);
                    }
                }
                else if (_state == (State.NUMERIC)) {
                    if (_ch == PERIOD) {
                        _state = State.FRACTIONAL;
                        realValue = intValue;
                        //((Numeric) token).setReal (true);
                        denom = 10;
                    }
                    else if (isDelimiter (_ch) || isWhitespace (_ch) ||
                             !isNumeral (_ch)) {
                        if (negative) {
                            if (_state == State.FRACTIONAL) {
                                realValue = -realValue;
                            }
                            else {
                                intValue = -intValue;
                            }
                        }
                        if (_state == State.FRACTIONAL) {
                            ((Numeric) token).setValue (realValue);
                        }
                        else {
                            ((Numeric) token).setValue (intValue);
                        }
                        _state = State.WHITESPACE;

                        if (isDelimiter (_ch)) {
                            _lookAhead = true;
                            _wsString = "";
                        }
                        else {
                            _wsString = "" + (char) _ch;
                        }

                        if (!token.isPdfACompliant()) {
                            _pdfACompliant = false;
                        }
                        return token;
                    }
                    else {
                        if (_state == State.FRACTIONAL) {
                            realValue = realValue * 10 + _ch - 48;
                        }
                        else {
                            intValue = intValue * 10 + _ch - 48;
                        }
                    }
                }
                else if (_state == (State.STREAM)) {
                    if (_ch == e) {
                        _state = State.E;
                    }
                    else {
                        prelastch = lastch;
                        lastch = _ch;
                        setStreamOffset ((Stream) token);
                        // Check for a CR/LF or just LF at the start of the stream.
                        // Since we don't know at this point (not having parsed
                        // the dictionary) whether the data is external, and since
                        // the PDF spec says that everything between stream and
                        // endstream is ignored, we don't know if this requirement
                        // is enforceable here.  But PDF/A forbids external streams,
                        // so we can at least check compliance there.  In any case,
                        // we subtrace the length of the CR/LF from the purported
                        // stream length. 
                        if (length == 0 && !sawLineBreak) {
                            if (_ch == LF) {
                                sawLineBreak = true;
                                if (!sawCR) {
                                    _pdfACompliant = false;
                                }
                                ((Stream) token).setOffset (((Stream) token).getOffset () + 1);
                            }
                            else if (_ch == CR) {
                                sawCR = true;
                                ((Stream) token).setOffset (((Stream) token).getOffset () + 1);
                            }
                            else {
                                // Coming here indicates an error if the stream
                                // isn't external; but we don't know whether
                                // it is.
                                _pdfACompliant = false; 
                            }
                        }
                        else{
                            length++;
                        }
                    }
                }
                else if (_state == (State.E)) {
                    if (_ch == n) {
                        _state = State.EN;
                    }
                    else {
                        _state = State.STREAM;
                        length += 2;
                    }
                }
                else if (_state == (State.EN)) {
                    if (_ch == d) {
                        _state = State.END;
                    }
                    else {
                        _state = State.STREAM;
                        length += 3;
                    }
                }
                else if (_state == (State.END)) {
                    if (_ch == s) {
                        _state = State.ENDS;
                    }
                    else {
                        _state = State.STREAM;
                        length += 4;
                    }
                }
                else if (_state == (State.ENDS)) {
                    if (_ch == t) {
                        _state = State.ENDST;
                    }
                    else {
                        _state = State.STREAM;
                        length += 5;
                    }
                }
                else if (_state == (State.ENDST)) {
                    if (_ch == r) {
                        _state = State.ENDSTR;
                    }
                    else {
                        _state = State.STREAM;
                        length += 6;
                    }
                }
                else if (_state == (State.ENDSTR)) {
                    if (_ch == e) {
                        _state = State.ENDSTRE;
                    }
                    else {
                        _state = State.STREAM;
                        length += 7;
                    }
                }
                else if (_state == (State.ENDSTRE)) {
                    if (_ch == a) {
                        _state = State.ENDSTREA;
                    }
                    else {
                        _state = State.STREAM;
                        length += 8;
                    }
                }
                else if (_state == (State.ENDSTREA)) {
                    if (_ch == m) {
                        _state = State.ENDSTREAM;
                    }
                    else {
                        _state = State.STREAM;
                        length += 9;
                    }
                }
                else if (_state == (State.ENDSTREAM)) {
                    if (isDelimiter (_ch) || isWhitespace (_ch)) {
                        _state = State.WHITESPACE;
                        
                        /* The line break, if any, before endstream
                         * is not counted in the length. */
                        if (prelastch == CR && lastch == LF) {
                            length -= 2;
                        }
                        else if (lastch == LF || lastch == CR) {
                            length -= 1;
                        }
                        ((Stream) token).setLength (length);

                        if (isDelimiter (_ch)) {
                            _lookAhead = true;
                            _wsString = "";
                        }
                        else {
                            _wsString = "" + (char) _ch;
                        }

                        return token;
                    }
                    else {
                        _state = State.STREAM;
                    }
                }
            }
        }
        catch (EOFException e) {
            if (token != null &&
                token instanceof StringValuedToken &&
                buffer != null) {
                ((StringValuedToken) token).setValue (buffer.toString ());
            }
            else {
                token = null;
            }
        }

        return token;
    }

    /**
     *  Return the current offset into the file.
     */
    public long getOffset ()
    {
        return _offset;
    }

    /**
     *  Return the set of language codes. Members of the set are Strings.
     */
    public Set getLanguageCodes ()
    {
        return _languageCodes;
    }
    
    
    /**
     *  Tell this object that the file is or isn't encrypted.
     */
    public void setEncrypted (boolean encrypted)
    {
        _encrypted = encrypted;
    }

    /**
     *   Returns the value of the pdfACompliant flag, which indicates that
     *   the tokenizer hasn't detected non-compliance.  A value of <code>true</code>
     *   is no guarantee that the file is compliant.
     */
    public boolean getPDFACompliant ()
    {
        return _pdfACompliant;
    }
    
    /**
     *   Set the value of the pdfACompliant flag.  This may be used to
     *   clear previous detection of noncompliance.
     */
    public void setPDFACompliant (boolean pdfACompliant)
    {
        _pdfACompliant = pdfACompliant;
    }
    
    /**
     *   Returns the value of the last white space string read by the
     *   tokenizer.  Repositioning clears the white space string.
     */
    public String getWSString () 
    {
        return _wsString;
    }

    /**
     *  Set the Tokenizer to a new position in the file.
     *
     *  @param  offset  The offset in bytes from the start of the file.
     */
    public abstract void seek (long offset)
        throws IOException, PdfException;
    
    
    /** Reset after a seek. */
    protected void seekReset (long offset)
    {
        _state = State.WHITESPACE;
        _wsString = "";
        _lookAhead = false;
        _ch = 0;
        /* Don't panic, _offset is used only for reporting purposes */
        _offset = offset - 1;
    }
    
    
    /** Get a character from the file or stream, using a buffer */
    public abstract int readChar () throws IOException;
 

    /** Read a character in one-byte or 2-byte format, as
        requested */
    public int readChar1 (boolean utf16) throws IOException
    {
        if (utf16) {
            int ch1 = readChar ();
            int ch2 = readChar ();
            return (ch1 << 8) | ch2;
        }
        else {
            return readChar ();
        }
    }
    
    /**
     *   Back up a byte so it will be read again.
     */
    public abstract void backupChar ();
    
    /** 
      *  Add a string to the language codes 
      */
    public void addLanguageCode (String langCode) 
    {
        _languageCodes.add (langCode);
    }



    /******************************************************************
     * PRIVATE CLASS METHODS.
     ******************************************************************/

    /*private static int hexToInt (int h1, int h2) throws PdfException
    {
        return 16*hexValue (h1) + hexValue (h2);
    } */

    private static int hexValue (int h) throws PdfException
    {
        int d = 0;
        if (0x30 <= h && h <= 0x39) {
            d = h - 0x30;
        }
        else if (0x41 <= h && h <= 0x46) {
            d = h - 0x37;
        }
        else if (0x61 <= h && h <= 0x66) {
            d = h - 0x57;
        }
        else {
            throw new PdfMalformedException ("Invalid character in hex string", 
                                0);
        }

        return d;
    }

    /** Return true if ch is a character which isn't white space
        but delimits a token. */
    private static boolean isDelimiter (int ch)
    {
        boolean delimeter = false;

        for (int i=0; i<DELIMITER.length; i++) {
            if (ch == DELIMITER[i]) {
                delimeter = true;
                break;
            }
        }

        return delimeter;
    }

    /* private static boolean isHexadecimal (int ch)
    {
        if (isNumeral (ch) && ((0x41 <= ch && ch <= 0x46) ||
                               (0x61 <= ch && ch <= 0x66))) {
            return true;
        }

        return false;
    } */

    private static boolean isNumeral (int ch)
    {
        if (0x30 <= ch && ch <= 0x39) {
            return true;
        }

        return false;
    }

    /* private static boolean isRegular (int ch)
    {
        return !isDelimiter (ch) && !isWhitespace (ch);
    } */

    private static boolean isWhitespace (int ch)
    {
        boolean whitespace = false;

        for (int i=0; i<WHITESPACE.length; i++) {
            if (ch == WHITESPACE[i]) {
                whitespace = true;
                break;
            }
        }

        return whitespace;
    }

    /**
     * If true, do not attempt to parse non-whitespace delimited tokens, e.g.,
     * literal and hexadecimal strings.
     * @param flag Scan mode flag
     */
    public void scanMode (boolean flag)
    {
	_scanMode = flag;
    }

    /** Initialization code for Stream object. This is meaningful
     *  only for the FileTokenizer subclass. */
    protected abstract void initStream (Stream token)
        throws IOException, PdfException;


    /** Sets the offset of a Stream to the current file position.
     *  Only the file-based tokenizer can do this, which is why this
     *  overrides the Tokenizer method. 
     */
    protected abstract void setStreamOffset (Stream token) 
        throws IOException, PdfException;
}
