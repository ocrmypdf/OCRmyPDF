/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import edu.harvard.hul.ois.jhove.*;
import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * The AIFF Common chunk.
 * 
 * @author Gary McGath
 *
 */
public class CommonChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public CommonChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts various properties into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        AiffModule module = (AiffModule) _module;
        int numChannels = module.readUnsignedShort (_dstream);
        long numSampleFrames = module.readUnsignedInt (_dstream);
        int sampleSize = module.readUnsignedShort (_dstream);
        bytesLeft -= 8;
        
        String compressionType = null;
        String compressionName = null;
        
        double sampleRate = module.read80BitDouble (_dstream);
        bytesLeft -= 10;
         
        if (module.getFileType () == AiffModule.AIFCTYPE) {
            if (bytesLeft == 0) {
                // This is a rather special case, but testing did turn up
                // a file that misbehaved in this way.
                info.setMessage (new ErrorMessage
                        ("Common Chunk in AIFF-C does not have compression type",
                         module.getNByte()));
                info.setWellFormed (false);
                return false;
            }
            compressionType = module.read4Chars (_dstream);
            // According to David Ackerman, the compression type can
            // change the endianness of the document.
            if (compressionType.equals ("sowt")) {
                module.setEndian (false);    // little-endian
            }
            bytesLeft -= 4;
            compressionName = module.readPascalString (_dstream);
            bytesLeft -= compressionName.length () + 1;
        }
        
        AESAudioMetadata aes = module.getAESMetadata ();
        aes.setBitDepth (sampleSize);
        aes.setSampleRate (sampleRate);
        aes.setNumChannels (numChannels);
        setChannelLocations (aes, numChannels);
        //aes.setDuration ((double) numSampleFrames / sampleRate);
        aes.setDuration (numSampleFrames);
        module.addAiffProperty (new Property ("SampleFrames",
                PropertyType.LONG,
                new Long (numSampleFrames)));
        // Proper handling of compression type should depend
        // on whether raw output is set
        if (compressionType != null) {
            module.addAiffProperty (new Property ("CompressionType",
						  PropertyType.STRING, 
						  compressionType));
	    if (compressionType.equals ("NONE")) {
	    }
	    else if (compressionType.equals ("raw ")) {
            aes.setAudioDataEncoding ("PCM 8-bit offset-binary");
	    }
	    else if (compressionType.equals ("twos")) {
            aes.setAudioDataEncoding ("PCM 16-bit twos-complement big-endian");
	    }
	    else if (compressionType.equals ("sowt")) {
            aes.setAudioDataEncoding ("PCM 16-bit twos-complement little-endian");
	    }
	    else if (compressionType.equals ("fl32")) {
            aes.setAudioDataEncoding ("PCM 32-bit integer");
	    }
	    else if (compressionType.equals ("fl64")) {
            aes.setAudioDataEncoding ("PCM 64-bit floating point");
	    }
	    else if (compressionType.equals ("in24")) {
            aes.setAudioDataEncoding ("PCM 24-bit integer");
	    }
	    else if (compressionType.equals ("in32")) {
            aes.setAudioDataEncoding ("PCM 32-bit integer");
	    }
	    else {
            aes.setAudioDataEncoding (compressionName);

                // The size of the data after compression isn't available
                // from the Common chunk, so we mark it as "unknown."
                // With a bit more sophistication, we could combine the
                // information from here and the Sound Data chunk to get
                // the effective byte rate, but we're about to release.
           String name = compressionName;
           if (name == null || name.length () == 0) {
               name = compressionType;
	       }
           aes.setBitrateReduction (compressionName, "", "", "",
					 "LOSSY", "UNKNOWN", "FIXED");
           }
        }
        if (compressionName != null && compressionName.length () > 0) {
            module.addAiffProperty (new Property ("CompressionName",
						  PropertyType.STRING,
						  compressionName));
        }
        
        return true;
    }

    /* Assign channel locationss according to the number of 
     * channels and the standard AIFF assignment. */
    @SuppressWarnings("fallthrough")
    private void setChannelLocations 
        (AESAudioMetadata aes, int numChannels)
    {
        String[] mapLoc = new String[numChannels];
        switch (numChannels) {
            case 1:
            mapLoc[0] = "UNKNOWN";
            break;
            
            // There are two 4-channel alternatives.  Pick one.
            case 4:
            mapLoc[3] = "SURROUND";
            // fall through to case 3

            case 3:
            mapLoc[2] = "CENTER";
            // fall through to case 2
            
            case 2:
            mapLoc[0] = "LEFT";
            mapLoc[1] = "RIGHT";
            break;
            
            case 6:
            mapLoc[0] = "LEFT";
            mapLoc[1] = "LEFT_CENTER";
            mapLoc[2] = "CENTER";
            mapLoc[3] = "RIGHT";
            mapLoc[4] = "RIGHT_CENTER";
            mapLoc[5] = "SURROUND";
            break;
            
            // If we get some other number of channels, punt.
            default:
            for (int i = 0; i < numChannels; i++) {
                mapLoc[i] = "UNKNOWN";
            }
        }
        aes.setMapLocations(mapLoc);
    }
}
