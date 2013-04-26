/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * The AIFF Marker chunk.
 *
 * @author Gary McGath
 *
 */
public class MarkerChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public MarkerChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a Markers property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        AiffModule module = (AiffModule) _module;
        int numMarkers = module.readUnsignedShort (_dstream);
        if (numMarkers == 0) {
            return true;   // trivial but legal case
        }
        List markerList = new ArrayList (numMarkers);
        for (int i = 0; i < numMarkers; i++) {
            int id = module.readUnsignedShort (_dstream);
            long position = module.readUnsignedInt (_dstream);
            String markerName = module.readPascalString(_dstream);
            
            Property[] mArr = new Property[3];
            mArr[0] = new Property ("ID",
                    PropertyType.INTEGER,
                    new Integer (id));
            mArr[1] = new Property ("Position",
                    PropertyType.LONG,
                    new Long (position));
            mArr[2] = new Property ("Name",
                    PropertyType.STRING,
                    markerName);
            markerList.add (new Property ("Marker",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    mArr));
        }
        module.addAiffProperty (new Property ("Markers",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    markerList));
        return true;
    }

}
