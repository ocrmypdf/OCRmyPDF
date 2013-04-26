/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;


import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
import java.util.*;

/**
 * Implementation of the WAVE Cart Chunk.
 *
 * @author Gary McGath
 *
 */
public class CartChunk extends Chunk {

    /** Number of timer tags.  This is a fixed value specified by the
     *  chunk definition. */
    private static final int N_TIMER_TAGS = 8;
    
    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public CartChunk (
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts a Cart Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        byte[] buf4 = new byte[4];
        ModuleBase.readByteBuf (_dstream, buf4, module);
        String version = byteBufString(buf4);
        // Title and most other fields within this chunk are ASCII strings
        // with a fixed allocation; calling trim() is necessary to get rid
        // of nulls.
        byte[] buf64 = new byte[64];
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String title = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String artist = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String cutID = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String clientID = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String category = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String classification = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String outCue = byteBufString (buf64);
        byte[] buf10 = new byte[10];
        ModuleBase.readByteBuf (_dstream, buf10, module);
        String startDate = byteBufString (buf10);
        byte[] buf8 = new byte[8];
        ModuleBase.readByteBuf (_dstream, buf8, module);
        String startTime = byteBufString (buf8);

        ModuleBase.readByteBuf (_dstream, buf10, module);
        String endDate = byteBufString (buf10);
        ModuleBase.readByteBuf (_dstream, buf8, module);
        String endTime = byteBufString (buf8);

        ModuleBase.readByteBuf (_dstream, buf64, module);
        String producerAppID = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String producerAppVersion = byteBufString (buf64);
        ModuleBase.readByteBuf (_dstream, buf64, module);
        String userDef = byteBufString (buf64);

        int levelReference = module.readSignedInt(_dstream);
        
        List timerTags = new ArrayList (N_TIMER_TAGS);
        for (int i = 0; i < N_TIMER_TAGS; i++) {
            String timerTagUsage = module.read4Chars(_dstream).trim ();
            long timerTagValue = module.readUnsignedInt (_dstream);
            if (timerTagUsage.length () > 0) {
                Property[] ttprop = new Property[2];
                ttprop[0] = new Property ("Usage",
                        PropertyType.STRING,
                        timerTagUsage);
                ttprop[1] = new Property ("Value",
                        PropertyType.LONG,
                        new Long (timerTagValue));
                
                timerTags.add (new Property ("PostTimer",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        ttprop));
            }
        }
        module.skipBytes (_dstream, 276, module);
   
        byte[] buf1k = new byte[1024];
        ModuleBase.readByteBuf (_dstream, buf1k, module);
        String url = byteBufString (buf1k);
        
        String tagText = "";
        if (bytesLeft > 2048) {
            byte[] bufTagText = new byte[(int) bytesLeft - 2048];
            ModuleBase.readByteBuf (_dstream, bufTagText, module);
            tagText = byteBufString (bufTagText);
        }
        
        // Whew -- we've read the whole thing.  Now make that into a
        // list of Properties.
        List plist = new ArrayList (20);
        if (version. length () > 0) {
            plist.add (new Property ("Version", PropertyType.STRING, version));
        }
        if (title.length() > 0) {
            plist.add (new Property ("Title", PropertyType.STRING, title));
        }
        if (artist.length () > 0) {
            plist.add (new Property ("Artist", PropertyType.STRING, artist));
        }
        if (cutID.length () > 0) {
            plist.add (new Property ("CutID", PropertyType.STRING, cutID));
        }
        if (clientID.length () > 0) {
            plist.add (new Property ("ClientID", PropertyType.STRING, clientID));
        }
        if (category.length() > 0) {
            plist.add (new Property ("Category", PropertyType.STRING, category));
        }
        if (classification.length () > 0) {
            plist.add (new Property 
                ("Classification", PropertyType.STRING, classification));
        }
        if (outCue.length () > 0) {
            plist.add (new Property ("OutCue", PropertyType.STRING, outCue));
        }
        if (startDate.length () > 0) {
            plist.add (new Property ("StartDate", PropertyType.STRING, startDate));
        }
        if (startTime.length () > 0) {
            plist.add (new Property ("StartTime", PropertyType.STRING, startTime));
        }
        if (endDate.length () > 0) {
            plist.add (new Property ("EndDate", PropertyType.STRING, endDate));
        }
        if (endTime.length () > 0) {
            plist.add (new Property ("EndTime", PropertyType.STRING, startTime));
        }
        if (producerAppID.length () > 0) {
            plist.add (new Property
                ("ProducerAppID", PropertyType.STRING, producerAppID));
        }
        if (producerAppVersion.length () > 0) {
            plist.add (new Property
                ("ProducerAppVersion", PropertyType.STRING, producerAppVersion));
        }
        if (userDef.length () > 0) {
            plist.add (new Property ("UserDef", PropertyType.STRING, userDef));
        }
        plist.add (new Property ("LevelReference", PropertyType.INTEGER,
                new Integer (levelReference)));
        if (timerTags.size() > 0) {
            plist.add (new Property ("PostTimers", PropertyType.PROPERTY,
                PropertyArity.LIST,
                timerTags));
        }
        if (url.length () > 0) {
            plist.add (new Property ("URL", PropertyType.STRING, url));
        }
        if (tagText.length () > 0) {
            plist.add (new Property ("TagText", PropertyType.STRING, tagText));
        }
        
        module.addWaveProperty (new Property ("Cart", 
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                plist));
        return true;
    }

}
