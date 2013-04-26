/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;


/**
 *
 * Abstract superclass for Codestream and Tile classes.
 * Many marker segments can apply either to the codestream
 * as a whole or to specific tiles; this class merges those
 * features in a single place. 
 * 
 * @author Gary McGath
 *
 */
public abstract class MainOrTile {

    /* Default value */
    protected final static int NULL = -1;

    /* Precinct size array */
    protected int[] _precSize;

    /** Array of components.  This is created when the SIZ
     * marker segment reports the number of components. */
    protected Property[] _components;

    /** Coding style default property */
    protected Property _codProperty;
    
    /** Quantization default property */
    protected Property _qcdProperty;
    
    /** Progression order change property */
    protected Property _pocProperty;
    
    /** Comments -- list of properties */
    protected List<Property> _comments;
    
    /* List of packet lengths */
    protected List<Long> _packetLengthList;
    
    


    public MainOrTile ()
    {
        _components = null;
        _qcdProperty = null;
        _codProperty = null;
        _comments = new LinkedList<Property> ();
    }



    /** Sets the number of components.  As a side effect,
     *  creates the compoments array.  This should be called
     *  from the SIZMarkerSegment class, and in a valid
     *  file will precede the setting of any components. 
     */
    public void setNumComponents (int nComp)
    {
        _components = new Property[nComp];
    }

    /** Sets a property indexed by component. */
    public void setCompProperty (int idx, Property prop)
    {
        if (_components != null && _components.length > idx) {
            _components[idx] = prop;
        }
    }

    /** Gets the number of components. */
    protected int getNumComponents ()
    {
        if (_components == null) {
            return 0;
        }
        else {
            return _components.length;
        }
    }

    /** Sets the coding style default property. */
    public void setCODProperty (Property prop)
    {
        _codProperty = prop;
    }
    
    /** Sets the quantization default property. */
    public void setQCDProperty (Property prop)
    {
        _qcdProperty = prop;
    }
    
    /** Sets the progression order change property. */
    public void setPOCProperty (Property prop)
    {
        _pocProperty = prop;
    }
    
    /** Adds a property to the comment list */
    public void addComment (Property comment)
    {
        _comments.add (comment);
    }


    /** Add a packet length to the list of packet lengths. */
    public void addPacketLength (long len)
    {
        if (_packetLengthList == null) {
            _packetLengthList = new LinkedList<Long> ();
        }
        _packetLengthList.add (new Long (len));
    }
}
