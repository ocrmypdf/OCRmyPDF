/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;

/**
 * Encapsulation of a tile-part in a JPEG 2000 codestream.
 *
 * @author Gary McGath
 *
 */
public class TilePart {

    private Tile _tile;
    private int _index;
    private long _length;
    
    /**
     *  Constructor.
     * 
     *  @param   tile   The Tile of which this is a part
     *  @param   index  The index of this tile part
     */
    public TilePart (Tile tile, int index)
    {
        _tile = tile;
        _index = index;
    }


    /** Sets the length field.  This must be called before
     *  calling makeProperty. */
    public void setLength (long len)
    {
        _length = len;
    }


    /** Returns a Property based on the TilePart. 
     *  The Property is named "TilePart". */
    public Property makeProperty ()
    {
        Property indexProp = new Property ("Index",
                PropertyType.INTEGER,
                new Integer (_index));
        Property lengthProp = new Property ("Length",
                PropertyType.LONG,
                new Long (_length));
        List propList = new ArrayList (2);
        propList.add (indexProp);
        propList.add (lengthProp);
        return new Property ("TilePart",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList);
    }
}
