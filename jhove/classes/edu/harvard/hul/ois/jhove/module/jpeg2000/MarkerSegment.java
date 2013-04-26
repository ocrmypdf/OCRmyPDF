/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;


/**
 * Abstract superclass for marker segments.  
 *
 * @author Gary McGath
 *
 */
public abstract class MarkerSegment {

    protected final static int
        SOC = 0X4F,             // start of codestream
        COD = 0X52,             // coding style default
        COC = 0X53,             // coding style component
        TLM = 0X55,             // tile-part lengths
        PLM = 0X57,             // packet length, main header
        PLT = 0X58,             // packet length, tile-part header
        QCD = 0X5C,             // quantization default
        QCC = 0X5D,             // quantization component
        RGN = 0X5E,             // region of interest
        POC = 0X5F,             // progression order change
        PPM = 0X60,             // Packed packet headers, main header
        PPT = 0X61,             // packed packet headers, tile-part header
        CRG = 0X63,             // component registration
        COM = 0X64,             // comment
        SOT = 0X90,             // start of tile part
        SOP = 0X91,             // start of packet
        EPH = 0X92,             // end of packet header
        SOD = 0X93,             // start of data
        EOC = 0XD9,             // end of codestream
        SIZ = 0X51;             // image and tile size
    
    protected ContCodestream _ccs;
    protected Codestream _cs;
    protected Jpeg2000Module _module;
    protected DataInputStream _dstream;
    protected RepInfo _repInfo;

    /**
     *  Constructor.
     *  After an instance of a MarkerSegment is created,
     *  the setter methods <code>setContCodestream</code>, 
     *  <code>setCodestream</code>, <code>setModule</code>, 
     *  and <code>setDataInputStream</code> must all be called as
     *  part of the setup before <code>process</code> is called.
     */
    public MarkerSegment ()
    {
    }
    
    /** Sets the Continuous Codestream from which this marker was
     *  obtained.
     */
    public void setContCodestream (ContCodestream ccs)
    {
        _ccs = ccs;
    }
    
    /** Sets the Codestream object being built. */
    public void setCodestream (Codestream cs)
    {
        _cs = cs;
    }
    
    /** Sets the Module under which all this is happening. */
    public void setModule (Jpeg2000Module module)
    {
        _module = module;
    }
    
    /** Sets the DataInputStream over which this marker is being
     *  read.
     */
    public void setDataInputStream (DataInputStream dstream)
    {
        _dstream = dstream;
    }
    
    /** Sets the RepInfo into which messages may be placed. */
    public void setRepInfo (RepInfo repInfo)
    {
        _repInfo = repInfo;
    }
    
    /** Returns <code>true</code> if this segment is a Marker.
     *  Will return <code>false</code> unless overridden. */
    public boolean isMarker ()
    {
        return false;
    }
    
    /** Static factory method for generating an object of the
     *  appropriate subclass of MarkerSegment, based on the
     *  marker code.
     * 
     *  @param  markerCode   The 8-bit marker code (ignoring the FF). */
    protected static MarkerSegment markerSegmentMaker (int markerCode)
    {
        switch (markerCode) {
            case SOT:
            return new SOTMarkerSegment ();
            
            case COC:
            return new COCMarkerSegment ();
            
            case COD:
            return new CODMarkerSegment ();
            
            case COM:
            return new CommentMarkerSegment ();

            case CRG:
            return new CRGMarkerSegment ();
            
            case PLM:
            return new PLMMarkerSegment ();
            
            case PLT:
            return new PLTMarkerSegment ();

            case POC:
            return new POCMarkerSegment ();
            
            case PPM:
            return new PPMMarkerSegment ();

            case PPT:
            return new PPTMarkerSegment ();

            case QCC:
            return new QCCMarkerSegment ();
            
            case QCD:
            return new QCDMarkerSegment ();
            
            case RGN:
            return new RGNMarkerSegment ();
            
            case SIZ:
            return new SIZMarkerSegment ();
            
            case TLM:
            return new TLMMarkerSegment ();
            
            case  SOC:       // start of codestream
            case  EPH:       // end of packet header
            case  SOD:       // start of data
            case  EOC:
            return new Marker ();
            
            // SOP won't be implemented, at least for the time
            // being, since it occurs within the bitstream data
            // of a codestream, which we don't analyze.
            case SOP:
            default:
            return new DefaultMarkerSegment ();
        }
    }
    
    /** Reads and returns the length field of the marker segment.
     *  The setter methods <code>setModule</code> 
     *  and <code>setDataInputStream</code> must be called as
     *  part of the setup before <code>readMarkLen</code> is called.
     */
    protected int readMarkLen () throws IOException
    {
        return _module.readUnsignedShort (_dstream);
    }
    
    
    /** Determines size of fields indexed by number of components.
     *  Some marker segments have fields which are 1 byte long if
     *  the number of components is 1-255, and 2 bytes long if
     *  the number of components is 256-65535.
     * 
     *  @return 0 if number of components not yet set, otherwise 1 or 2
     */
    protected int nCompBytes ()
    {
        int nComp = _cs.getNumComponents ();
        if (nComp == 0) {
            return 0;        // indicates an error condition
        }
        int compIdx;
        // size of Ccoc field depends on number of components
        return (nComp < 257 ? 1 : 2);   
    }


    /** Returns the MainOrTile object which is currently
     *  applicable in the Contiguous Codestream.  If the
     *  Contiguous Codestream has a current Tile, that is
     *  returned; otherwise the Codestream object established
     *  by setCodestream is returned.
     */
    protected MainOrTile getMainOrTile ()
    {    
        Tile tile = _ccs.getCurTile ();
        if (tile != null) {
            return tile;
        }
        else {
            return _cs;
        }
    }

    /** Process the marker or marker segment.  The DataInputStream
     *  will be at the point of having read the marker code.  The
     *  <code>process</code> method must consume exactly the number
     *  of bytes remaining in the marker segment; for a marker,
     *  this number will always be 0.
     * 
     *  @param    bytesToEat   The number of bytes that must be consumed.
     *                         For a Marker, this number will always be 0.
     *                         If it is 0 for a MarkerSegment, the
     *                         number of bytes to consume is unknown.
     *  @return                <code>true</code> if segment is well-formed,
     *                         <code>false</code> otherwise.
     */
    protected abstract boolean process (int bytesToEat) throws IOException;
}
