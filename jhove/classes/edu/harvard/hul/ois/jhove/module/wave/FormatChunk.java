/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.Chunk;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the WAVE Format Chunk.
 *
 * @author Gary McGath
 *
 */
public class FormatChunk extends Chunk {

    /** Compression code for original Microsoft PCM */
    public final static int WAVE_FORMAT_PCM = 1;
    
    /** Compression code for MPEG */
    public final static int WAVE_FORMAT_MPEG = 0X50;
    
    /** Compression code for Microsoft Extensible Wave Format */
    public final static int WAVE_FORMAT_EXTENSIBLE = 0XFFFE;
    
    /** Table of lossless compression codes. */
    private final static int[] losslessCodecs = {
        0X163,         // WMA lossless
        0X1971         // Sonic foundry lossless
    };
    
    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public FormatChunk(
        WaveModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts appropriate Properties into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException, JhoveException {
        WaveModule module = (WaveModule) _module;
        int validBitsPerSample = -1;
        byte[] subformat = null;
        long channelMask = -1;
        int compressionCode = module.readUnsignedShort (_dstream);
        module.setCompressionCode (compressionCode);
        int numChannels = module.readUnsignedShort (_dstream);
        long sampleRate = module.readUnsignedInt (_dstream);
        module.setSampleRate (sampleRate);
        long bytesPerSecond = module.readUnsignedInt (_dstream);
        int blockAlign = module.readUnsignedShort (_dstream);
        module.setBlockAlign (blockAlign);
        int bitsPerSample = module.readUnsignedShort (_dstream);
        bytesLeft -= 16;
        byte[] extraBytes = null;
        if (bytesLeft > 0) {
            int extraFormatBytes = module.readUnsignedShort (_dstream);
            extraBytes = new byte[extraFormatBytes];
            if (compressionCode == WAVE_FORMAT_EXTENSIBLE && bytesLeft >= 22) {
                // This is -- or should be -- WAVEFORMATEXTENSIBLE.
                // Need to do some additional checks on profile satisfaction.
                boolean wfe = true;     // accept tentatively
                // The next word may be valid bits per sample, samples
                // per block, or merely "reserved".  Which one it is
                // apparently depends on the compression format.  I really
                // can't figure out how to tell which it is without
                // exhaustively researching all compression formats.
                validBitsPerSample = module.readUnsignedShort (_dstream);
                channelMask = module.readUnsignedInt (_dstream);
                // The subformat is a GUID
                subformat = new byte[20];
                ModuleBase.readByteBuf(_dstream, subformat, module);
                
                // Nitpicking profile requirements
                if ((((bitsPerSample + 7) / 8) * numChannels) != blockAlign) {
                    wfe = false;
                }
                if ((bitsPerSample % 8) != 0) {
                    // So why was that fancy ceiling arithmetic needed?
                    // So it can be the same calculation as with WaveFormatEx.
                    wfe = false;
                }
                if (validBitsPerSample > bitsPerSample) {
                    wfe = false;
                }
                if (wfe) {
                    module.setWaveFormatExtensible(true);
                }
            }
            else {
                if (compressionCode != WAVE_FORMAT_PCM ||
                    (((bitsPerSample + 7) / 8) * numChannels) == blockAlign) {
                    module.setWaveFormatEx (true);
                }
                ModuleBase.readByteBuf (_dstream, extraBytes, module);
            }
            
            // Possible pad to maintain even alignment
            if ((extraFormatBytes & 1) != 0) {
                _module.skipBytes (_dstream, 1, module);
            }
        }
        else {
            // no extra bytes signifies the PCM profile.  In this
            // case, the compression code also needs to be 1 (Microsoft
            // PCM).
            if (compressionCode == WAVE_FORMAT_PCM &&
                    (((bitsPerSample + 7) / 8) * numChannels) == blockAlign) {
                module.setPCMWaveFormat(true);
            }
        }
        
        // Set a TENTATIVE flag if this chunk satisfies the broadcast
        // wave format.
        if (compressionCode == WAVE_FORMAT_PCM ||
                compressionCode == WAVE_FORMAT_MPEG) {
            module.setBroadcastWave (true);
        }
        
        module.addWaveProperty
            (module.addIntegerProperty ("CompressionCode", compressionCode,
                    WaveStrings.COMPRESSION_FORMAT,
                    WaveStrings.COMPRESSION_INDEX));
        AESAudioMetadata aes = module.getAESMetadata ();
        String compName;
        try {
            compName = WaveStrings.COMPRESSION_FORMAT
                [WaveStrings.COMPRESSION_INDEX[compressionCode]];
        }
        catch (Exception e) {
            throw new JhoveException ("Error in FormatChunk: " + e.getClass().getName());
        }
        aes.setAudioDataEncoding(compName);
        aes.setNumChannels(numChannels);
        setChannelLocations (aes, numChannels);
        aes.setSampleRate(sampleRate);
        aes.setBitDepth(bitsPerSample);
        
        // Check which codecs are non-lossy
        String qual = "LOSSY";
        for (int i = 0; i < losslessCodecs.length; i++) {
            if (compressionCode == losslessCodecs[i]) {
                qual = "CODE_REGENERATING";
            }
        } 
        if (compressionCode == WAVE_FORMAT_PCM) {
            aes.clearBitrateReduction ();
        }
        else {
            aes.setBitrateReduction (compName, "", "", "",
                qual, Long.toString (bytesPerSecond), "FIXED");
        }

        module.addWaveProperty (new Property ("AverageBytesPerSecond",
                    PropertyType.LONG,
                    new Long (bytesPerSecond)));
        module.addWaveProperty (new Property ("BlockAlign",
                    PropertyType.INTEGER,
                    new Integer (blockAlign)));
        if (extraBytes != null) {
            module.addWaveProperty (new Property ("ExtraFormatBytes",
                    PropertyType.BYTE,
                    PropertyArity.ARRAY,
                    extraBytes));
        }
        if (validBitsPerSample != -1) {
            // Should this property be called something like
            // ValidBitsPersampleOrSamplesPerBlock?
            module.addWaveProperty (new Property ("ValidBitsPerSample",
                    PropertyType.INTEGER,
                    new Integer (validBitsPerSample)));
        }
        if (channelMask != -1) {
            module.addWaveProperty (new Property ("ChannelMask",
                    PropertyType.LONG,
                    new Long (channelMask)));
        }
        if (subformat != null) {
            module.addWaveProperty (new Property ("Subformat",
                    PropertyType.BYTE,
                    PropertyArity.ARRAY,
                    subformat));
        }
        return true;
    }

    /* Set default channel assignments.  This is fairly simple,
     * but it's helpful to keep the same structure as the equivalent
     * CommonChunk.setChannelLocations function. */
    private void setChannelLocations 
        (AESAudioMetadata aes, int numChannels)
    {
        String[] mapLoc = new String[numChannels];
        switch (numChannels) {
            case 2:
            mapLoc[0] = "LEFT";
            mapLoc[1] = "RIGHT";
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
