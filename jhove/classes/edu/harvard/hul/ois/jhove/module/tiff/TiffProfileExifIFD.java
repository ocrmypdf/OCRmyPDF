/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

/**
 * Profile checker for the Exif IFD of a TIFF file which potentially
 * matches the TIFF profile.  This is called from TiffProfileExif
 * to check the Exif IFD.
 *
 * @author Gary McGath
 *
 */
public class TiffProfileExifIFD extends TiffProfile {

    private int _majVersion;
    private int _minVersion;

    public TiffProfileExifIFD ()
    {        
        super ();
        // This isn't used directly to report a profile, so the
        // profile text is irrelevant.
        _profileText = null;
        _majVersion = -1;
        _minVersion = -1;
    }

    /**
     *  Returns true if the IFD satisfies the requirements of an
     *  Exif profile.  See the Exif specification for details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
        if (!(ifd instanceof ExifIFD)) {
            return false;
        }
        ExifIFD eifd = (ExifIFD) ifd;
        String version = eifd.getExifVersion ();
        if (version.equals ("0220")) {
            _majVersion = 2;
            _minVersion = 2;
        }
        else if (version.equals ("0210")) {
            _majVersion = 2;
            _minVersion = 1;
        }
        else if (version.equals ("0200")) {
            _majVersion = 2;
            _minVersion = 0;
        }
        else {
            // Other versions aren't accepted
            return false;
        }
        if (!(eifd.getFlashpixVersion ().equals ("0100"))) {
            return false;
        }
        int colspc = eifd.getColorspace ();
        if (colspc != 1 && colspc != 65535) {
            return false;
        }
        return true;
    }
}
