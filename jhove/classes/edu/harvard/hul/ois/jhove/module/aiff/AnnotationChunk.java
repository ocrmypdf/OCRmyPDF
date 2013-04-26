/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Implementation of the AIFF Annotation Chunk.
 *
 * @author Gary McGath
 *
 */
public class AnnotationChunk extends TextChunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public AnnotationChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and adds an Annotation property to the
     *  module's list of annotations. 
     * 
     *  There can be multiple Annotation Chunks, so we don't
     *  create a property here directly.
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        String name = readText ();
        ((AiffModule) _module).addAnnotation (new Property (propName, 
                PropertyType.STRING,
                name));
        return true;
    }

}
