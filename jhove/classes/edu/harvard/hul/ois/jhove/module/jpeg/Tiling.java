/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Encapsulation of the tiling information for a JPEG image.
 * 
 * @author Gary McGath
 *
 */
public class Tiling {

    /* List of individual tile descriptions */
    private List<long[]> tileList;
    
    private int _tilingType;
    private int _vertScale;
    private int _horScale;
    private long _refGridHeight;
    private long _refGridWidth;

    
    /**
     *  Constructor.
     */
    public Tiling() {
        tileList = new LinkedList<long[]> ();
    }
    
    /**
     *  Adds a tile to the list.
     */
    public void addTile (long vertScale, 
            long horScale, 
            long vertOffset, 
            long horOffset)
    {
        // Represent the tile as an array of 4 longs
        long[] tile = new long[4];
        tile[0] = vertScale;
        tile[1] = horScale;
        tile[2] = vertOffset;
        tile[3] = horOffset;
        
        tileList.add (tile);
    }
    
    /**
     * Returns a property listing all the tiles.
     */
    public Property buildTileListProp ()
    {
        List<Property> tpList = new LinkedList<Property> ();
        ListIterator<long[]> iter = tileList.listIterator ();
        while (iter.hasNext ()) {
            long[] tile =  iter.next ();
            Property[] tProp = new Property[4];
            tProp[0] = new Property ("VerticalScale",
                        PropertyType.LONG,
                        new Long (tile[0]));
            tProp[1] = new Property ("HorizontalScale",
                        PropertyType.LONG,
                        new Long (tile[1]));
            tProp[2] = new Property ("VerticalOffsret",
                        PropertyType.LONG,
                        new Long (tile[2]));
            tProp[3] = new Property ("HorizontalOffset",
                        PropertyType.LONG,
                        new Long (tile[3]));
            tpList.add (new Property ("Tile",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        tProp));
        }
        return new Property ("Tiles",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                tpList);
    }
    
    

    public void setTilingType (int tilingType)
    {
        _tilingType = tilingType;
    }
    
    
    public void setVertScale (int vertScale)
    {
        _vertScale = vertScale;
    }
    
    
    public void setHorScale (int horScale)
    {
        _horScale = horScale;
    }
    
    
    public void setRefGridHeight (long refGridHeight)
    {
        _refGridHeight = refGridHeight;
    }
    
    
    public void setRefGridWidth (long refGridWidth)
    {
        _refGridWidth = refGridWidth;
    }
    
    
    public int getTilingType ()
    {
        return _tilingType;
    }
    
    
    public int getVertScale ()
    {
        return _vertScale;
    }
    
    
    public int getHorScale ()
    {
        return _horScale;
    }
    
    
    public long getRefGridHeight ()
    {
        return _refGridHeight;
    }
    
    
    public long getRefGridWidth ()
    {
        return _refGridWidth;
    }
    
    

}
