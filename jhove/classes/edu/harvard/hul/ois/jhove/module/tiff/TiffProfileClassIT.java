/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;

import edu.harvard.hul.ois.jhove.*;

/**
 *  Abstract superclass for Tiff Profile Checkers Tiff IP/whatever.
 *
 *  @author Gary McGath
 */
public abstract class TiffProfileClassIT
    extends TiffProfile
{
    public TiffProfileClassIT ()
    {
        super ();
    }

    /**
     *  Returns true if the IFD satisfies the requirements
     *  which are common to all Tiff IT profiles.
     *  Subclasses will call this, then apply additional
     *  tests if it returns <code>true</code>.
     */
    public boolean satisfiesThisProfile (IFD ifd) 
    {
	if (!(ifd instanceof TiffIFD)) {
	    return false;
	}
	TiffIFD tifd = (TiffIFD) ifd;

        /* Check required tags. */
	NisoImageMetadata niso = tifd.getNisoImageMetadata ();
        if (niso.getImageWidth () == NisoImageMetadata.NULL ||
            niso.getImageLength () == NisoImageMetadata.NULL ||
            niso.getStripOffsets () == null ||
            niso.getStripByteCounts () == null ||
            niso.getXSamplingFrequency () == null ||
            niso.getYSamplingFrequency () == null) {
            return false;
        }

        return true;
    }
}
