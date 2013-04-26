/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import java.io.DataInputStream;
import java.io.IOException;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import edu.harvard.hul.ois.jhove.module.iff.ChunkHeader;

/**
 * Implementation of the WAVE Note Chunk.
 *
 * @author Gary McGath
 *
 */
public class NoteChunk extends SimpleTextChunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public NoteChunk(
        ModuleBase module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and adds to the module's list of Notes.
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        Property p = readTextProp (module, "Note");
        module.addNote (p);
        return true;
    }

}
