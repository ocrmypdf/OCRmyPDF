/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;


/**
 *  Profile checker for TIFF Photoshop.
 */
public final class TiffProfilePhotoshop extends TiffProfile
{
    public TiffProfilePhotoshop ()
    {
	super ();
	_profileText = "Adobe Photoshop 'Advanced TIFF'";
    }

    /**
     *  Returns true if the IFD satisfies the requirements of the
     *  profile.  See the Photoshop specification for details.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;

	/* Check required values. */
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
	int pi = niso.getCompressionScheme ();
	if (pi == 6 || pi == 8) {
	    return true;
	}

	if (tifd.getImageSourceData () != null) {
	    return true;
	}

	return false;
    }
}
