/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
import java.util.*;

/**
 * Implementation of the WAVE Peak Envelope ('levl') Chunk.
 *
 * @author Gary McGath
 *
 */
public class PeakEnvelopeChunk extends Chunk {


    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public PeakEnvelopeChunk (
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts a BroadcastAudioExtension Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        long version = module.readUnsignedInt (_dstream);
        long format = module.readUnsignedInt (_dstream);
        long pointsPerValue = module.readUnsignedInt (_dstream);
        long blockSize = module.readUnsignedInt (_dstream);
        long peakChannels = module.readUnsignedInt (_dstream);
        long numPeakFrames = module.readUnsignedInt (_dstream);
        long posPeakOfPeaks = module.readUnsignedInt (_dstream);
        long offsetToPeaks = module.readUnsignedInt (_dstream);
        byte[] buf28 = new byte[28];
        ModuleBase.readByteBuf (_dstream, buf28, module);
        String timestamp = byteBufString (buf28);
        module.skipBytes (_dstream, 60, module);

        // The format of the peak data depends on the value of
        // format and pointsPerValue.  If format = 1, points are
        // unsigned byte.  If format = 2, points are unsigned short.
        // The number of points per peak value is equal to the
        // value of pointsPerValue, which must be 1 or 2.
        
        Property peaksProp = null;
        if (bytesLeft > 120) {
            int pointBytes = (int) (bytesLeft - 120);
            int nPoints = 0;
            int nValues = 0;
            if (format == 1) {
                nPoints = pointBytes;
            }
            else if (format == 2) {
                nPoints = pointBytes / 2;
            }
            else {
                info.setValid (false);
                info.setMessage (new ErrorMessage 
                        ("Invalid format value in Peak Envelope Chunk"));
            }
            if (pointsPerValue == 1) {
                nValues = nPoints;
            }
            else if (pointsPerValue == 2) {
                nValues = nPoints / 2;
            }
            else {
                info.setValid (false);
                info.setMessage (new ErrorMessage 
                        ("Invalid pointsPerValue in Peak Envelope Chunk"));
            }
            if (info.getValid() == RepInfo.FALSE) {
                module.skipBytes (_dstream, (int) bytesLeft - 120, module);
                return true;
            }
            
            // We have two different kinds of property depending on 
            // pointsPerValue.
            if (pointsPerValue == 2) {
                Property[] pointArray = new Property[nValues];
                for (int i = 0; i < nValues; i++) {
                    int[] point = new int[2];
                    pointArray[i] = new Property ("Point",
                            PropertyType.INTEGER,
                            PropertyArity.ARRAY,
                            point);
                    if (format == 1) {
                        point[0] = 
                            ModuleBase.readUnsignedByte (_dstream, module);
                        point[1] = 
                            ModuleBase.readUnsignedByte (_dstream, module);
                    }
                    else {
                        point[0] = 
                            module.readUnsignedShort (_dstream);
                        point[1] = 
                            module.readUnsignedShort (_dstream);
                    }
                }
                peaksProp = new Property ("PeakEnvelopeData",
                    PropertyType.PROPERTY,
                    PropertyArity.ARRAY,
                    pointArray);
            }
            else {
                // 1 point per value
                int[] pointArray = new int[nValues];
                for (int i = 0; i < nValues; i++) {
                    if (format == 1) {
                        pointArray[i] = 
                            ModuleBase.readUnsignedByte (_dstream, module);
                    }
                    else {
                        pointArray[i] =
                            module.readUnsignedShort (_dstream);
                    }
                }
                peaksProp = new Property ("PeakEnvelopeData",
                    PropertyType.INTEGER,
                    PropertyArity.ARRAY,
                    pointArray);
            }
        }
        
        // Now put the whole mess together as a List of Properties.
        List plist = new ArrayList (20);
        plist.add (new Property ("Version",
                PropertyType.LONG,
                new Long (version)));
        plist.add (new Property ("Format",
                PropertyType.LONG,
                new Long (format)));
        plist.add (new Property ("PointsPerValue",
                PropertyType.LONG,
                new Long (pointsPerValue)));
        plist.add (new Property ("BlockSize",
                PropertyType.LONG,
                new Long (blockSize)));
        plist.add (new Property ("PeakChannels",
                PropertyType.LONG,
                new Long (peakChannels)));
        plist.add (new Property ("NumPeakFrames",
                PropertyType.LONG,
                new Long (numPeakFrames)));
        plist.add (new Property ("PosPeakOfPeaks",
                PropertyType.LONG,
                new Long (posPeakOfPeaks)));
        plist.add (new Property ("OffsetToPeaks",
                PropertyType.LONG,
                new Long (offsetToPeaks)));
        if (timestamp.length () > 0) {
            plist.add (new Property ("Timestamp",
                PropertyType.STRING,
                timestamp));
        }
        if (peaksProp != null) {
            plist.add (peaksProp);
        }
        module.addWaveProperty (new Property ("PeakEnvelope", 
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                plist));
       
        return true;
    }
}
