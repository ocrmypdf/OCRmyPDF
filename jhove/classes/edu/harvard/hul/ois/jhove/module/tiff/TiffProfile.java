/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.tiff;


/**
 *  Abstract class for TIFF profile checkers.
 *  A profile applies to a given IFD; the caller should
 *  run all profiles on all IFD's and accumulate a List
 *  of the Strings returned by <code>getText</code>
 *  when <code>satisfiesProfile</code> returns true.
 */
public abstract class TiffProfile
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/
    protected String _profileText;     // String used for profile property
    protected int _mimeClass;          // MIME subclass satisfied by profile
    private boolean _alreadyOK;

    /** Values for mimeClass.  These are the appropriate indices into
     *  TiffModule.MIMETYPE */
    public final static int
        MIME_GENERIC = 0,
        MIME_FX = 1,              // TIFF-FX profiles
        MIME_1314 = 2;            // RFC 1314 profile


    /** 
     *   Creates a TiffProfile.
     *   Subclass constructors should assign a value to
     *   _profileText, then call the super constructor.
     * 
     *   Sets _mimeClass to MIME_GENERIC.  Profiles which
     *   indicate other MIME classes should assign a different
     *   value to _mimeClass, which is the index into 
     *   TiffModule.MIMETYPE that should be used.
     */
    public TiffProfile () 
    {
        _alreadyOK = false;
        _mimeClass = MIME_GENERIC;
    }

    /** 
     * Returns <code>true</code> if the IFD satisfies the profile.
     * This calls <code>satisfiesThisProfile()</code>, which does the actual work.
     * <code>satisfiesProfile()</code> sets the alreadyOK flag, which may be
     * checked by calling <code>isAlreadyOK()</code> to save the effort of
     * testing the same profile more than once and thus generating
     * duplicate output.
     * Subclasses should not override <code>satisfiesProfile</code>.
     *
     * @param ifd   The IFD which is being evaluated against the profile
     */
    public final boolean satisfiesProfile (IFD ifd)
    {
        boolean sp = satisfiesThisProfile (ifd);
        _alreadyOK = false;        
        if (sp) {
            _alreadyOK = true;
        }
        return sp;
    }

    /**
     * Returns <code>true</code> if the IFD satisfies the
     * profile.  Subclasses should override <code>satisfiesThisProfile()</code>,
     * not <code>satisfiesProfile()</code>, as
     * <code>satisfiesProfile()</code> does some
     * additional bookkeeping for all subclases.
     */
    public abstract boolean satisfiesThisProfile (IFD ifd);

    /**
     *  Returns the text which describes this profile.
     */
    public String getText () 
    {
        return _profileText;
    }
    
    /**
     *  Sets the value of the alreadyOK flag.
     */
    public void setAlreadyOK (boolean ok)
    {
        _alreadyOK = ok;
    }
    
    /**
     *  Returns the MIME class for this profile.  This
     *  will be one of the values MIME_GENERIC, MIME_FX,
     *  and MIME_1314, corresponding to indices into
     *  TiffModule.MIMETYPE.  All profiles which don't imply
     *  a special MIME type other than image/tiff should
     *  take no special action, allowing MIME_GENERIC
     *  to be returned.  Classes which return a different
     *  value should assign that value to MIME_CLASS in
     *  the constructor rather than overriding this.
     */
    public int getMimeClass ()
    {
        return _mimeClass;
    }

    /**
     *  Returns the value of the alreadyOK flag.  
     *  This flag can be used when a profile is being checked
     *  against more than one IFD, to see if it has satisfied
     *  a previous IFD and thus avoid duplicate profile listings.
     *  The alreadyOK flag is set whenever satisfiesProfile
     *  returns <code>true</code>.
     */
     public boolean isAlreadyOK ()
     {
        return _alreadyOK;
     }

     /* Various routines to reduce the tedium of checking
        tags which are common to many profiles. */

    /**
     *  Checks if the value of the Compression tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesCompression (TiffIFD ifd, int [] values) 
    {
        int compression = ifd.getNisoImageMetadata ().getCompressionScheme ();
        for (int i = 0; i < values.length; i++) {
            if (compression == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the PlanarConfiguration tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesCompression (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesCompression (ifd, values);
    }

    /**
     *  Checks if the value of the PhotometricInterpretation tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesPhotometricInterpretation (TiffIFD ifd,
							  int [] values) 
    {
        int pInt = ifd.getNisoImageMetadata ().getColorSpace ();
        for (int i = 0; i < values.length; i++) {
            if (pInt == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the PhotometricInterpretation tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesPhotometricInterpretation (TiffIFD ifd,
							  int value)
    {
        int [] values = { value } ;
        return satisfiesPhotometricInterpretation (ifd, values);
    }

    /**
     *  Checks if the value of the ResolutionUnit tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesResolutionUnit (TiffIFD ifd, int [] values) 
    {
        int ru = ifd.getNisoImageMetadata ().getSamplingFrequencyUnit ();
        for (int i = 0; i < values.length; i++) {
            if (ru == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the ResolutionUnit tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesResolutionUnit (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesResolutionUnit (ifd, values);
    }


    /**
     *  Checks if the value of the XResolution tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesXResolution (TiffIFD ifd, int [] values) 
    {
        long xf = ifd.getNisoImageMetadata ().getXSamplingFrequency ().toLong ();
        for (int i = 0; i < values.length; i++) {
            if (xf == values[i]) {
                return true;
            }
        }
        return false;
    }



    /**
     *  Checks if the value of the XResolution tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesYResolution (TiffIFD ifd, int [] values) 
    {
        long yf = ifd.getNisoImageMetadata ().getYSamplingFrequency ().toLong ();
        for (int i = 0; i < values.length; i++) {
            if (yf == values[i]) {
                return true;
            }
        }
        return false;
    }




    /**
     *  Checks if the value of the SamplesPerPixel tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesSamplesPerPixel (TiffIFD ifd, int [] values) 
    {
        int spp = ifd.getNisoImageMetadata ().getSamplesPerPixel ();
        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the SamplesPerPixel tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesSamplesPerPixel (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesSamplesPerPixel (ifd, values);
    }

    /**
     *  Checks if the value of the PlanarConfiguration tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesPlanarConfiguration (TiffIFD ifd, int [] values) 
    {
        int spp = ifd.getNisoImageMetadata ().getPlanarConfiguration ();
        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the PlanarConfiguration tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesPlanarConfiguration (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesPlanarConfiguration (ifd, values);
    }

    /**
     *  Checks if the value of the Orientation tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesOrientation (TiffIFD ifd, int [] values) 
    {
        int spp = ifd.getNisoImageMetadata ().getOrientation ();

        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the Orientation tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesOrientation (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesOrientation (ifd, values);
    }
    
    /**
     *  Checks if the value of the ImageColorIndicator tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesImageColorIndicator (TiffIFD ifd, int [] values) 
    {
        int spp = ifd.getImageColorIndicator ();
        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the ImageColorIndicator tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesImageColorIndicator (TiffIFD ifd, int value)
    {
        int [] values = { value } ;
        return satisfiesImageColorIndicator (ifd, values);
    }
    
    /**
     *  Checks if the value of the NewSubfileType tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of long values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesNewSubfileType (TiffIFD ifd, long [] values) 
    {
        long spp = ifd.getNewSubfileType ();
        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the NewSubfileType tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesNewSubfileType (TiffIFD ifd, long value)
    {
        long [] values = { value } ;
        return satisfiesNewSubfileType (ifd, values);
    }
    
    /**
     *  Checks if the value of the BackgroundColorIndicator tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesBackgroundColorIndicator (TiffIFD ifd,
							 int [] values) 
    {
        int spp = ifd.getBackgroundColorIndicator ();
        for (int i = 0; i < values.length; i++) {
            if (spp == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the BackgroundColorIndicator tag matches
     *  the value passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param value   A value which must match the tag value to
     *                 satisfy the test.
     */
    protected boolean satisfiesBackgroundColorIndicator (TiffIFD ifd,
							 int value)
    {
        int [] values = { value } ;
        return satisfiesBackgroundColorIndicator (ifd, values);
    }
    
    /** Checks the DotRange against a minimum and a maximum value.  Returns
     * true if the DotRange exists, is well-formed (i.e., has at least
     * 2 values, and the first two values equal minValue and maxValue
     * respectively.
     */
    protected boolean satisfiesDotRange (TiffIFD ifd, int minValue,
					 int maxValue) 
    {
	int [] dotRange = ifd.getDotRange ();
	if (dotRange == null || dotRange.length < 2) {
	    return false;
	}
	return (dotRange[0] == minValue || dotRange[1] == maxValue);
    }
    
    
    /**
     *  Checks if the value of the ImageWidth tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesImageWidth (TiffIFD ifd, int [] values) 
    {
        long iw = ifd.getNisoImageMetadata ().getImageWidth ();
        for (int i = 0; i < values.length; i++) {
            if (iw == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the Indexed tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesIndexed (TiffIFD ifd, int [] values) 
    {
        int ix = ifd.getIndexed ();
        for (int i = 0; i < values.length; i++) {
            if (ix == values[i]) {
                return true;
            }
        }
        return false;
    }

    /**
     *  Checks if the value of the Indexed tag matches
     *  any of the values in the array passed to it.
     *
     *  @param ifd     The IFD being checked
     *  @param values  An array of values, any of which will
     *                 satisfy the test.
     */
    protected boolean satisfiesFillOrder (TiffIFD ifd, int [] values) 
    {
        int f = ifd.getFillOrder ();
        for (int i = 0; i < values.length; i++) {
            if (f == values[i]) {
                return true;
            }
        }
        return false;
    }

}
