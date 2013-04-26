/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module;


/**
 *  This class encapsulates a Unicode code block.
 *
 *  @see Utf8Module 
 */
public class Utf8Block
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Unicode 6.0.0 blocks, derived from
     * &lt;http://www.unicode.org/Public/3.2-Update/Blocks-3.2.0.txt&gt;
     * and updated to Unicode 6.0.0  */
    public static final Utf8Block [] unicodeBlock = {
	new Utf8Block (0x0000, 0x007F, "Basic Latin"),
	new Utf8Block (0x0080, 0x00FF, "Latin-1 Supplement"),
	new Utf8Block (0x0100, 0x017F, "Latin Extended-A"),
	new Utf8Block (0x0180, 0x024F, "Latin Extended-B"),
	new Utf8Block (0x0250, 0x02AF, "IPA Extensions"),
	new Utf8Block (0x02B0, 0x02FF, "Spacing Modifier Letters"),
	new Utf8Block (0x0300, 0x036F, "Combining Diacritical Marks"),
	new Utf8Block (0x0370, 0x03FF, "Greek and Coptic"),
	new Utf8Block (0x0400, 0x04FF, "Cyrillic"),
	new Utf8Block (0x0500, 0x052F, "Cyrillic Supplementary"),
	new Utf8Block (0x0530, 0x058F, "Armenian"),
	new Utf8Block (0x0590, 0x05FF, "Hebrew"),
	new Utf8Block (0x0600, 0x06FF, "Arabic"),
	new Utf8Block (0x0700, 0x074F, "Syriac"),
	new Utf8Block (0x0780, 0x07BF, "Thaana"),
    new Utf8Block (0x07C0, 0x07FF, "NKo"),
    new Utf8Block (0x0840, 0x085F, "Mandaic"),
	new Utf8Block (0x0900, 0x097F, "Devanagari"),
	new Utf8Block (0x0980, 0x09FF, "Bengali"),
	new Utf8Block (0x0A00, 0x0A7F, "Gurmukhi"),
	new Utf8Block (0x0A80, 0x0AFF, "Gujarati"),
	new Utf8Block (0x0B00, 0x0B7F, "Oriya"),
	new Utf8Block (0x0B80, 0x0BFF, "Tamil"),
	new Utf8Block (0x0C00, 0x0C7F, "Telugu"),
	new Utf8Block (0x0C80, 0x0CFF, "Kannada"),
	new Utf8Block (0x0D00, 0x0D7F, "Malayalam"),
	new Utf8Block (0x0D80, 0x0DFF, "Sinhala"),
	new Utf8Block (0x0E00, 0x0E7F, "Thai"),
	new Utf8Block (0x0E80, 0x0EFF, "Lao"),
	new Utf8Block (0x0F00, 0x0FFF, "Tibetan"),
	new Utf8Block (0x1000, 0x109F, "Myanmar"),
	new Utf8Block (0x10A0, 0x10FF, "Georgian"),
	new Utf8Block (0x1100, 0x11FF, "Hangul Jamo"),
	new Utf8Block (0x1200, 0x137F, "Ethiopic"),
	new Utf8Block (0x13A0, 0x13FF, "Cherokee"),
	new Utf8Block (0x1400, 0x167F, "Unified Canadian Aboriginal Syllabics"),
	new Utf8Block (0x1680, 0x169F, "Ogham"),
	new Utf8Block (0x16A0, 0x16FF, "Runic"),
	new Utf8Block (0x1700, 0x171F, "Tagalog"),
	new Utf8Block (0x1720, 0x173F, "Hanunoo"),
	new Utf8Block (0x1740, 0x175F, "Buhid"),
	new Utf8Block (0x1760, 0x177F, "Tagbanwa"),
	new Utf8Block (0x1780, 0x17FF, "Khmer"),
	new Utf8Block (0x1800, 0x18AF, "Mongolian"),

	/* 1900-1D7F new for 4.0 */
	new Utf8Block (0x1900, 0x194F, "Limbu"),
	new Utf8Block (0x1950, 0x197F, "Tai Le"),
	new Utf8Block (0x19E0, 0x19FF, "Khmer Symbols"),
    new Utf8Block (0x1B00, 0x1B7F, "Balinese"),
    new Utf8Block (0x1BC0, 0x1BFF, "Batak"),
	new Utf8Block (0x1D00, 0x1D7F, "Phonetic Extensions"),

	new Utf8Block (0x1E00, 0x1EFF, "Latin Extended Additional"),
	new Utf8Block (0x1F00, 0x1FFF, "Greek Extended"),
	new Utf8Block (0x2000, 0x206F, "General Punctuation"),
	new Utf8Block (0x2070, 0x209F, "Superscripts and Subscripts"),
	new Utf8Block (0x20A0, 0x20CF, "Currency Symbols"),
	new Utf8Block (0x20D0, 0x20FF, "Combining Diacritical Marks for Symbols"),
	new Utf8Block (0x2100, 0x214F, "Letterlike Symbols"),
	new Utf8Block (0x2150, 0x218F, "Number Forms"),
	new Utf8Block (0x2190, 0x21FF, "Arrows"),
	new Utf8Block (0x2200, 0x22FF, "Mathematical Operators"),
	new Utf8Block (0x2300, 0x23FF, "Miscellaneous Technical"),
	new Utf8Block (0x2400, 0x243F, "Control Pictures"),
	new Utf8Block (0x2440, 0x245F, "Optical Character Recognition"),
	new Utf8Block (0x2460, 0x24FF, "Enclosed Alphanumerics"),
	new Utf8Block (0x2500, 0x257F, "Box Drawing"),
	new Utf8Block (0x2580, 0x259F, "Block Elements"),
	new Utf8Block (0x25A0, 0x25FF, "Geometric Shapes"),
	new Utf8Block (0x2600, 0x26FF, "Miscellaneous Symbols"),
	new Utf8Block (0x2700, 0x27BF, "Dingbats"),
	new Utf8Block (0x27C0, 0x27EF, "Miscellaneous Mathematical Symbols-A"),
	new Utf8Block (0x27F0, 0x27FF, "Supplemental Arrows-A"),
	new Utf8Block (0x2800, 0x28FF, "Braille Patterns"),
	new Utf8Block (0x2900, 0x297F, "Supplemental Arrows-B"),
	new Utf8Block (0x2980, 0x29FF, "Miscellaneous Mathematical Symbols-B"),
	new Utf8Block (0x2A00, 0x2AFF, "Supplemental Mathematical Operators"),
    new Utf8Block (0x2C60, 0x2C7F, "Latin Extended-C"),
	new Utf8Block (0x2E80, 0x2EFF, "CJK Radicals Supplement"),
	new Utf8Block (0x2F00, 0x2FDF, "Kangxi Radicals"),
	new Utf8Block (0x2FF0, 0x2FFF, "Ideographic Description Characters"),
	new Utf8Block (0x3000, 0x303F, "CJK Symbols and Punctuation"),
	new Utf8Block (0x3040, 0x309F, "Hiragana"),
	new Utf8Block (0x30A0, 0x30FF, "Katakana"),
	new Utf8Block (0x3100, 0x312F, "Bopomofo"),
	new Utf8Block (0x3130, 0x318F, "Hangul Compatibility Jamo"),
	new Utf8Block (0x3190, 0x319F, "Kanbun"),
	new Utf8Block (0x31A0, 0x31BF, "Bopomofo Extended"),
	new Utf8Block (0x31F0, 0x31FF, "Katakana Phonetic Extensions"),
	new Utf8Block (0x3200, 0x32FF, "Enclosed CJK Letters and Months"),
	new Utf8Block (0x3300, 0x33FF, "CJK Compatibility"),
	new Utf8Block (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),

	/* 4DC0-4DFF new for 4.0 */
	new Utf8Block (0x4DC0, 0x4DFF, "Yijing Hexagram Symbols"),

	new Utf8Block (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
	new Utf8Block (0xA000, 0xA48F, "Yi Syllables"),
	new Utf8Block (0xA490, 0xA4CF, "Yi Radicals"),
    new Utf8Block (0xA720, 0xA7FF, "Latin Extended-D"),
    new Utf8Block (0xA840, 0xA87F, "Phags-pa"),
    new Utf8Block (0xAB00, 0xAB2F, "Ethiopic Extended-A"),
	new Utf8Block (0xAC00, 0xD7AF, "Hangul Syllables"),
	new Utf8Block (0xD800, 0xDB7F, "High Surrogates"),
	new Utf8Block (0xDB80, 0xDBFF, "High Private Use Surrogates"),
	new Utf8Block (0xDC00, 0xDFFF, "Low Surrogates"),
	new Utf8Block (0xE000, 0xF8FF, "Private Use Area"),
	new Utf8Block (0xF900, 0xFAFF, "CJK Compatibility Ideographs"),
	new Utf8Block (0xFB00, 0xFB4F, "Alphabetic Presentation Forms"),
	new Utf8Block (0xFB50, 0xFDFF, "Arabic Presentation Forms-A"),
	new Utf8Block (0xFE00, 0xFE0F, "Variation Selectors"),
	new Utf8Block (0xFE20, 0xFE2F, "Combining Half Marks"),
	new Utf8Block (0xFE30, 0xFE4F, "CJK Compatibility Forms"),
	new Utf8Block (0xFE50, 0xFE6F, "Small Form Variants"),
	new Utf8Block (0xFE70, 0xFEFF, "Arabic Presentation Forms-B"),
	new Utf8Block (0xFF00, 0xFFEF, "Halfwidth and Fullwidth Forms"),
	new Utf8Block (0xFFF0, 0xFFFF, "Specials"),

	new Utf8Block (0x10000, 0x1007F, "Linear B Syllabary"),
	new Utf8Block (0x10080, 0x100FF, "Linear B Ideograms"),
	new Utf8Block (0x10100, 0x1013F, "Aegean Numbers"),

	new Utf8Block (0x10300, 0x1032F, "Old Italic"),
	new Utf8Block (0x10330, 0x1034F, "Gothic"),

	new Utf8Block (0x10380, 0x1039F, "Ugaritic"),

	new Utf8Block (0x10400, 0x1044F, "Deseret"),
    new Utf8Block (0x10900, 0x1091F, "Phoenician"),

	new Utf8Block (0x10450, 0x1047F, "Shavian"),
	new Utf8Block (0x10480, 0x104AF, "Osmanya"),
	new Utf8Block (0x10800, 0x1083F, "Cypriot Syllabary"),
    new Utf8Block (0x11000, 0x1107F, "Brahmi"),
    new Utf8Block (0x12000, 0x120FF, "Cuneiform"),
    new Utf8Block (0x16800, 0x168BF, "Bamum Supplement"),
    new Utf8Block (0x1B000, 0x1B0FF, "Kana Supplement"),

	new Utf8Block (0x1D000, 0x1D0FF, "Byzantine Musical Symbols"),
	new Utf8Block (0x1D100, 0x1D1FF, "Musical Symbols"),
    new Utf8Block (0x1D360, 0x1D37F, "Counting Rod Numerals"),
	new Utf8Block (0x1D400, 0x1D7FF, "Mathematical Alphanumeric Symbols"),
    new Utf8Block (0x1F0A0, 0x1F0FF, "Playing Cards"),
    new Utf8Block (0x1F300, 0x1F3FF, "Miscellaneous Symbols and Pictographs"),
    new Utf8Block (0x1F600, 0x1F64F, "Emoticons"),
    new Utf8Block (0x1F680, 0x1F6FF, "Transport and Map Symbols"),
    new Utf8Block (0x1F700, 0x1F77F, "Alchemical Symbols"),
	new Utf8Block (0x20000, 0x2A6DF, "CJK Unified Ideographs Extension B"),
    new Utf8Block (0x2B740, 0x2B78F, "CJK Unified Ideographs Extension D"),
	new Utf8Block (0x2F800, 0x2FA1F, "CJK Compatibility Ideographs Supplement"),
	new Utf8Block (0xE0000, 0xE007F, "Tags"),

	/* E0100-E01EF new for 4.0 */
	new Utf8Block (0xE0100, 0xE01EF, "Variation Selectors Supplement"),

	new Utf8Block (0xF0000, 0xFFFFF, "Supplementary Private Use Area-A"),
	new Utf8Block (0x100000, 0x10FFFF, "Supplementary Private Use Area-B")
    };

    private int _end;
    private String _name;
    private int _start;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a Utf8Block, specifying the start and end codes
     *  and block name.
     *
     *  @param start  Start code as defined in the Unicode block specification
     *  @param end    End code as defined in the Unicode block specification
     *  @param name   Block name
     */
    public Utf8Block (int start, int end, String name)
    {
	_start = start;
	_end   = end;
	_name  = name;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Returns the end code.
     */
    public int getEnd ()
    {
	return _end;
    }

    /**
     *  Returns the block name.
     */
    public String getName ()
    {
	return _name;
    }

    /**
     *  Returns the start code.
     */
    public int getStart ()
    {
	return _start;
    }
}
