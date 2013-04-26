/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Encapsulation of a GlobalParameters IFD, as defined by
 * TIFF/FX, RFC 2301.
 *
 * @author Gary McGath
 *
 */
public class GlobalParametersIFD extends IFD {

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/
    private int _profileType;
    private int _faxProfile;
    private int _codingMethods;
    private String _versionYear;
    private int _modeNumber;

    /** Tiff/FX-specific tags. */
    public static final int
        PROFILETYPE = 401,
        FAXPROFILE = 402,
        CODINGMETHODS = 403,
        VERSIONYEAR = 404,
        MODENUMBER = 405;

    private static final String [] PROFILETYPE_L = {
        "Unspecified", "Group 3 Fax"
    };
    
    private static final String [] FAXPROFILE_L = {
        "does not conform to a profile defined for TIFF for facsimile",
        "Minimal black & white lossless, Profile S",
        "Extended black & white lossless, Profile F",
        "Lossless JBIG black & white, Profile J",
        "Lossy color and grayscale, Profile C",
        "Lossless color and grayscale, Profile L",
        "Mixed Raster Content, Profile M"
    };

    private static final String [] CODINGMETHODS_L = {
        "unspecified compression",
        "1-dimensional coding, ITU-T Rec. T.4 (MH - Modified Huffman)",
        "2-dimensional coding, ITU-T Rec. T.4 (MR - Modified Read)",
        "2-dimensional coding, ITU-T Rec. T.6 (MMR - Modified MR)",
        "ITU-T Rec. T.82 coding, using ITU-T Rec. T.85 (JBIG)",
        "ITU-T Rec. T.81 (Baseline JPEG)",
        "ITU-T Rec. T.82 coding, using ITU-T Rec. T.43 (JBIG color)"

    };

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** Instantiate a <code>GlobalParametersIFD</code> object.
     * @param offset IFD offset
     * @param raf TIFF file
     * @param bigEndian True if big-endian file
     */
    public GlobalParametersIFD (long offset, RepInfo info, 
                    RandomAccessFile raf,
                    boolean bigEndian)
    {
        super (offset, info, raf, bigEndian);

        _profileType = NULL;
        _faxProfile = NULL;
        _codingMethods = NULL;
        _versionYear = null;
        _modeNumber = NULL;
    }


    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /** Get the IFD properties. */
    public Property getProperty(boolean rawOutput) throws TiffException {
        List entries = new LinkedList ();
        if (_profileType != NULL) {
            entries.add (addIntegerProperty ("ProfileType", _profileType,
                                             PROFILETYPE_L,
                                             rawOutput));
        }
        if (_faxProfile != NULL) {
            entries.add (addIntegerProperty ("FaxProfile", _faxProfile,
                                             FAXPROFILE_L,
                                             rawOutput));
        }
        if (_codingMethods != NULL) {
            entries.add (addBitmaskProperty ("CodingMethods", _codingMethods,
                                             CODINGMETHODS_L,
                                             rawOutput));
        }
        if (_versionYear != null) {
            entries.add (new Property ("VersionYear",
                            PropertyType.STRING,
                            _versionYear));
        }
        if (_modeNumber != NULL) {
            entries.add (new Property ("ModeNumber",
                            PropertyType.INTEGER,
                            new Integer (_modeNumber)));
        }
        return propertyHeader ("GlobalParameterIFD", entries);
    }

    /** Lookup an IFD tag. */
    public void lookupTag (int tag, int type, long count, long value)
        throws TiffException
    {
        try {
            if (tag == PROFILETYPE) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _profileType = (int) readLong(type, count, value);
            }
            else if (tag == FAXPROFILE) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _faxProfile = (int) readByte(type, count, value);
            }
            else if (tag == CODINGMETHODS) {
                checkType  (tag, type, LONG);
                checkCount (tag, count, 1);
                _codingMethods = (int) readLong(type, count, value);
            }
            else if (tag == VERSIONYEAR) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 4);
                _versionYear = readASCII(count, value);
            }
            else if (tag == MODENUMBER) {
                checkType  (tag, type, BYTE);
                checkCount (tag, count, 1);
                _modeNumber = (int) readByte(type, count, value);
            }
        }
        catch (IOException e) {
            throw new TiffException ("Read error for tag " + tag, value);
        }
    }

}
