package edu.harvard.hul.ois.jhove;

import java.nio.charset.Charset;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Encapsulation of the textMD metadata for text files.
 * See http://www.loc.gov/standards/textMd for more information.
 *
 * @author Thomas Ledoux
 *
 */
public class TextMDMetadata {
	/**
	 * textMD namespace and version
	 */
	public static final String NAMESPACE = "info:lc/xmlns/textMD-v3";
    public static final String DEFAULT_LOCATION = 
        "http://www.loc.gov/standards/textMD/textMD-v3.01a.xsd";
	public static final String VERSION = "3.0";
	
	/**
     *  Uses enumerated values of 'big', 'little', and 'middle' endian. 
     */
	public static final String[] BYTE_ORDER = { 
		"big", "little", "middle" 
	};
    public static final int BYTE_ORDER_BIG = 0;
    public static final int BYTE_ORDER_LITTLE = 1;
    public static final int BYTE_ORDER_MIDDLE= 2;
    
    /**
     *  Uses enumerated values of 'CR', 'LF' and 'CR/LF' for the idenntification of the linebreak. 
     */
	public static final String[] LINEBREAK = { 
		"CR", "LF", "CR/LF" 
	};
    public static final int LINEBREAK_CR = 0;
    public static final int LINEBREAK_LF = 1;
    public static final int LINEBREAK_CRLF = 2;
   
    /**
     * Array of textMD charsets unknown by java.nio.charset.Charsets
     */
    protected static final String[] UNKNOWN_JAVA_CHARSET =
            new String[] { 
                    "ISO-10646-UTF-1", "ISO_646.basic:1983", "INVARIANT", "BS_4730", "NATS-SEFI",
                    "NATS-SEFI-ADD", "NATS-DANO", "NATS-DANO-ADD", "SEN_850200_B", "SEN_850200_C", "ISO-2022-CN-EXT",
                    "JIS_C6220-1969-jp", "JIS_C6220-1969-ro", "IT", "PT", "ES", "greek7-old", "latin-greek",
                    "DIN_66003", "NF_Z_62-010_(1973)", "latin-greek-1", "ISO_5427", "JIS_C6226-1978", "BS_viewdata",
                    "INIS", "INIS-8", "INIS-cyrillic", "ISO_5427:1981", "ISO_5428:1980", "GB_1988-80", "GB_2312-80",
                    "NS_4551-1", "NS_4551-2", "NF_Z_62-010", "videotex-suppl", "PT2", "ES2", "MSZ_7795.3", "greek7",
                    "ASMO_449", "iso-ir-90", "JIS_C6229-1984-a", "JIS_C6229-1984-b", "JIS_C6229-1984-b-add",
                    "JIS_C6229-1984-hand", "JIS_C6229-1984-hand-add", "JIS_C6229-1984-kana", "ISO_2033-1983",
                    "ANSI_X3.110-1983", "T.61-7bit", "ECMA-cyrillic", "CSA_Z243.4-1985-1", "CSA_Z243.4-1985-2",
                    "CSA_Z243.4-1985-gr", "ISO_8859-6-E", "ISO_8859-6-I", "T.101-G2", "ISO_8859-8-E", "ISO_8859-8-I",
                    "CSN_369103", "JUS_I.B1.002", "ISO_6937-2-add", "IEC_P27-1", "JUS_I.B1.003-serb",
                    "JUS_I.B1.003-mac", "greek-ccitt", "NC_NC00-10:81", "ISO_6937-2-25", "GOST_19768-74",
                    "ISO_8859-supp", "ISO_10367-box", "ISO-8859-10", "latin-lap", "DS_2089", "us-dk", "dk-us",
                    "KSC5636", "ISO-10646-UCS-4", "DEC-MCS", "hp-roman8", "macintosh", "IBM038", "IBM274", "IBM275",
                    "IBM281", "IBM290", "IBM423", "IBM851", "IBM880", "IBM891", "IBM903", "IBM904", "IBM905",
                    "EBCDIC-AT-DE", "EBCDIC-AT-DE-A", "EBCDIC-CA-FR", "EBCDIC-DK-NO", "EBCDIC-DK-NO-A", "EBCDIC-FI-SE",
                    "EBCDIC-FI-SE-A", "EBCDIC-FR", "EBCDIC-IT", "EBCDIC-PT", "EBCDIC-ES", "EBCDIC-ES-A", "EBCDIC-ES-S",
                    "EBCDIC-UK", "EBCDIC-US", "UNKNOWN-8BIT", "MNEMONIC", "MNEM", "VISCII", "VIQR", "IBM00924",
                    "UNICODE-1-1", "SCSU", "UTF-7", "CESU-8", "UNICODE-1-1-UTF-7", "ISO-8859-14", "ISO-8859-16",
                    "Extended_UNIX_Code_Fixed_Width_for_Japanese", "ISO-10646-UCS-Basic", "ISO-10646-Unicode-Latin1",
                    "ISO-10646-J-1", "ISO-Unicode-IBM-1268", "ISO-Unicode-IBM-1276", "ISO-Unicode-IBM-1264",
                    "ISO-Unicode-IBM-1265", "ISO-8859-1-Windows-3.0-Latin-1", "ISO-8859-1-Windows-3.1-Latin-1",
                    "ISO-8859-2-Windows-Latin-2", "ISO-8859-9-Windows-Latin-5", "Adobe-Standard-Encoding",
                    "Ventura-US", "Ventura-International", "PC8-Danish-Norwegian", "PC8-Turkish", "IBM-Symbols",
                    "HP-Legal", "HP-Pi-font", "HP-Math8", "Adobe-Symbol-Encoding", "HP-DeskTop", "Ventura-Math",
                    "Microsoft-Publishing", "HZ-GB-2312", };
    /**
     * Set of unknown charsets in Java
     */
    protected static Set setOfUnknownJavaCharset;
    
    /**
     * Map from ISO 639/2 T to ISO 639/2 B
     */
    protected static Map<String, String> fromISO_639_2_T2B;
    
	public static final String CHARSET_ASCII = "US-ASCII";
	public static final String CHARSET_UTF8 = "UTF-8";
	public static final String CHARSET_ISO8859_1 = "ISO-8859-1";

	/**
     * To represent the unknown
	 */ 
	public static final int NILL = -1;
	
    static {
        setOfUnknownJavaCharset = new HashSet(Arrays.asList(UNKNOWN_JAVA_CHARSET));
        
        // Map to transform from the terminology code to the bibliographic one 
        fromISO_639_2_T2B = new HashMap<String, String>();
        fromISO_639_2_T2B.put("sqi", "alb");
        fromISO_639_2_T2B.put("hye", "arm");
        fromISO_639_2_T2B.put("eus", "baq");
        fromISO_639_2_T2B.put("mya", "bur");
        fromISO_639_2_T2B.put("zho", "chi");
        fromISO_639_2_T2B.put("ces", "cze");
        fromISO_639_2_T2B.put("nld", "dut");
        fromISO_639_2_T2B.put("fra", "fre");
        fromISO_639_2_T2B.put("kat", "geo");
        fromISO_639_2_T2B.put("deu", "ger");
        fromISO_639_2_T2B.put("ell", "gre");
        fromISO_639_2_T2B.put("isl", "ice");
        fromISO_639_2_T2B.put("mkd", "mac");
        fromISO_639_2_T2B.put("mri", "mao");
        fromISO_639_2_T2B.put("msa", "may");
        fromISO_639_2_T2B.put("fas", "per");
        fromISO_639_2_T2B.put("ron", "rum");
        fromISO_639_2_T2B.put("slk", "slo");
        fromISO_639_2_T2B.put("bod", "tib");
        fromISO_639_2_T2B.put("cym", "wel");
    }
    
	/**
	charset
	    Usage: The character set employed by the text. Controlled vocab using IANA names for character sets.
	    Attributes: none.
	    Contains: none.
	    Contained by: character_info.
   */
	private String charset;

	/**
 	byte_order
	    Usage: Byte order, primarily useful for cases where it's not clear just by specifying an IANA character set. 
	    Uses enumerated values of big, little, and middle' endian.
	    Attributes: none.
	    Contains: none.
	    Contained by: character_info.
	*/
	private int byte_order = NILL;

	/**
	byte_size
	    Usage: The size of an individual byte within the expressed as a number of bits (as integer). This does not necessarily equal the character size, as a character may have more than one, or a variable number of bytes per character.
	    Attributes: none.
	    Contains: none.
	    Contained by: character_info.
	*/
	private String byte_size;
    
	/**
	character_size
	    Usage: The size of an individual character within the character set as a number of bytes of the size expressed in the byte_size. In the case of variable encodings, such as UTF-8 for Unicode, the character_size element should state "variable" and also identify the specific variable character set encoding in the encoding attribute.
	    Attributes: encoding.
	    Contains: none.
	    Contained by: character_info.
	 */
	private String character_size;
    
	/**
	linebreak
	    Usage: How line breaks are represented in current file (which may differ from how they were originally encoded). Either carriage return, line feed, or carriage return/line feed.
	    Attributes: none.
	    Contains: none.
	    Contained by: character_info. 
	 */
	private int linebreak = NILL;
	
	/**
    language
        Usage: Language(s) used in work. Use ISO 639-2 codes, which are enumerated in the schema as valid text values.
        Attributes: none.
        Contains: none.
        Contained by: textMD.
	 */
	private String language;
	
	/**
	markup_basis
	    Usage: The metalanguage used to create the markup language, such as SGML, XML, GML, etc.
	    Attributes: version.
	    Contains: none.
	    Contained by: textMD.
	*/
	private String markup_basis;
	/**	
	 version
	    Usage: Used to record the version number (as a string) for a given piece of software, a markup language, or a schema version.
	*/	
	private String markup_basis_version;
	
	/**
	markup_language
	    Usage: Markup language employed on the text (i.e., the specific schema or dtd). May be a URI for schema or dtd, but not mandatory.
	    Attributes: version.
	    Contains: none.
	    Contained by: textMD. 	
	*/
	private String markup_language;
    
	/**	
	 version
	    Usage: Used to record the version number (as a string) for a given piece of software, a markup language, or a schema version.
	*/	
	private String markup_language_version;
    
	/**
	 * @return the charset
	 */
	public String getCharset() {
		return charset;
	}
    
	/**
	 * @param charset the charset to set
	 */
	public void setCharset(String charset) {
		this.charset = toTextMDCharset(charset);
	}
    
	/**
	 * @return the byte_order
	 */
	public int getByte_order() {
		return byte_order;
	}
        public String getByte_orderString() {
            if (byte_order == NILL) {
                return BYTE_ORDER[BYTE_ORDER_BIG]; // default !!!
            }
            return BYTE_ORDER[byte_order];
    }
	
	/**
	 * @param byte_order the byte_order to set
	 */
	public void setByte_order(int byte_order) {
		this.byte_order = byte_order;
	}
    
	/**
	 * @return the byte_size
	 */
	public String getByte_size() {
		return byte_size;
	}
    
	/**
	 * @param byte_size the byte_size to set
	 */
	public void setByte_size(String byte_size) {
		this.byte_size = byte_size;
	}
    
	/**
	 * @return the character_size
	 */
	public String getCharacter_size() {
		return character_size;
	}
    
	/**
	 * @param character_size the character_size to set
	 */
	public void setCharacter_size(String character_size) {
		this.character_size = character_size;
	}
    
	/**
	 * @return the linebreak
	 */
	public int getLinebreak() {
		return linebreak;
	}
    
    /**
     * @return the linebreak in String form
     */
    public String getLinebreakString() {
        if (linebreak == NILL) {
            return LINEBREAK[LINEBREAK_CRLF]; // default !!!
        }
        return LINEBREAK[linebreak];
    }
    
	/**
	 * @param linebreak the linebreak to set
	 */
	public void setLinebreak(int linebreak) {
		this.linebreak = linebreak;
	}
    
	/**
	 * @return the language
	 */
	public String getLanguage() {
		return language;
	}
    
	/**
	 * @param language the language to set
	 */
	public void setLanguage(String language) {
        this.language = toISO_639_2(language);
	}
    
	/**
	 * @return the markup_basis
	 */
	public String getMarkup_basis() {
		return markup_basis;
	}
    
	/**
	 * @param markup_basis the markup_basis to set
	 */
	public void setMarkup_basis(String markup_basis) {
		this.markup_basis = markup_basis;
	}
    
	/**
	 * @return the markup_basis_version
	 */
	public String getMarkup_basis_version() {
		return markup_basis_version;
	}
    
	/**
	 * @param markup_basis_version the markup_basis_version to set
	 */
	public void setMarkup_basis_version(String markup_basis_version) {
		this.markup_basis_version = markup_basis_version;
	}
    
	/**
	 * @return the markup_language
	 */
	public String getMarkup_language() {
		return markup_language;
	}
    
	/**
	 * @param markup_language the markup_language to set
	 */
	public void setMarkup_language(String markup_language) {
		this.markup_language = markup_language;
	}
    
	/**
	 * @return the markup_language_version
	 */
	public String getMarkup_language_version() {
		return markup_language_version;
	}
    
	/**
	 * @param markup_language_version the markup_language_version to set
	 */
	public void setMarkup_language_version(String markup_language_version) {
		this.markup_language_version = markup_language_version;
	}
    
    /**
     * Transform a given charset in the "authorized" list given in the textMD schema enumeration.
     * From the schema documentation on charset (http://www.loc.gov/standards/textMD/elementSet/index.html#element_charset).
     * The character set employed by the text. Controlled vocab using IANA names for character sets:
     * http://www.iana.org/assignments/character-sets.
     * The problem arises because the java Charset uses the (preferred MIME name) where textMD uses the Name ...
     * @param srcCharset charset from the file
     * @return normalized charset
     */
    public static String toTextMDCharset(String srcCharset) {
        if (srcCharset == null) return null;
        
        Charset cs = null;
        String textMDCharset = null;
        try {
            cs = Charset.forName(srcCharset);
            textMDCharset = cs.name();
        } catch (Exception e) {
            // Try a unknown one
            if (setOfUnknownJavaCharset.contains(srcCharset)) {
                textMDCharset = srcCharset;
            } else {
                // Downgrade to default
                textMDCharset = CHARSET_ISO8859_1;
            }
        }
        if (textMDCharset != null) {
            return textMDCharset;
        } else {
            // Downgrade to default
            return CHARSET_ISO8859_1;
        }
    }
    
    /**
     * Transform a language to the ISO_639-2 language (only enumeration allowed in textMD schema).
     * @param srcLang language in the file
     * @return normalized language in 3 letters (except qaa-qtz)
     */
    public static String toISO_639_2(String srcLang) {
        if (srcLang == null) return null;
        if ("qaa-qtz".equals(srcLang)) return srcLang;
        
        String textMDLang = null;
        if (srcLang.length() == 3) {
            textMDLang = srcLang;
        }
        else if (srcLang.length() == 2) {
            try {
                Locale loc = new Locale(srcLang);
                textMDLang = loc.getISO3Language();
            } catch (Exception e) {
                // Unknown language
            }
        }
        else if (srcLang.length() > 3) {
            // Just try with the first 2 characters
            try {
                Locale loc = new Locale(srcLang.substring(0, 2));
                srcLang = loc.getISO3Language();
            } catch (Exception e) {
                // Unknown language
            }
        }
        if (textMDLang != null && textMDLang.length() == 3) {
            // From ISO 639-2/T to ISO 639-2/B
            if (fromISO_639_2_T2B.containsKey(textMDLang)) {
                textMDLang = (String)fromISO_639_2_T2B.get(textMDLang);
            }
            return textMDLang;
        }
        return null;

    }
}
