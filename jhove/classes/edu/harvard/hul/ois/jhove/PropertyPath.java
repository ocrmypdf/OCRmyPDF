/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


import java.util.*;

/**
 * A description of the location of a Property in a
 * RepInfo object.  Properties can be nested under other
 * properties, in lists, maps, or subproperties. This class
 * provides a general way to specify their location.
 * 
 * For the moment, only paths by name are fully supported. 
 *
 * @author Gary McGath
 *
 */
public class PropertyPath {

    private List pathInfo;
    
    /**
     * No-argument constructor.
     * Creates an empty path.
     */
    public PropertyPath ()
    {
        pathInfo = new LinkedList ();
    }
    
    /**
     *  Cloning constructor.
     *  This creates a new pathInfo list, whose elements
     *  are shared with the original PropertyPath's list.
     */
    public PropertyPath (PropertyPath path) 
    {
        pathInfo = new LinkedList ();
        pathInfo.addAll (path.pathInfo);
    }
    
    /**
     *  String array constructor.
     *  This allows creation of a path in a common and simple
     *  case:  a hierarchy of named subproperties. It's the
     *  equivalent of creating an empty PropertyPath and then
     *  calling addElement successively with each of the strings
     *  in the array.
     */
    public PropertyPath (String[] pathArray)
    {
        pathInfo = new LinkedList ();
        for (int i = 0; i < pathArray.length; i++) {
            pathInfo.add (pathArray[i]);
        }
    }

    /**
     *  Adds a property name to the path.
     */
    public void addPropertyName (String str)
    {
        pathInfo.add (str);
        // Now -- how do we add a key and distinguish it from a 
        // property name?  We could define an internal type for
        // keys.  Do that for the moment and see what that leads
        // to in retrieval.  Alternatively, it isn't needed because
        // we can see that a property has arity Map.
    }
    
    /**
     *  Adds a key to the path, for a property map.
     */
    public void addPropertyKey (Object obj)
    {
        pathInfo.add (new PropertyKey (obj));
    }
    
    /**
     *  Adds an index to the path, for an indexed property.
     */
    public void addPropertyIndex (int idx)
    {
        pathInfo.add (new Integer (idx));
    }
    
    /**
     *   Walk down the path and return the specified Property.
     *   
     *   @param   info   The RepInfo object to search
     * 
     *   @return  The specified Property if found, otherwise null.
     */
    public Property locateProperty (RepInfo info)
    {
        return locateProperty (info, false);
    }
    

    /**
     *   Walk down the path and return the specified Property.
     *   
     *   @param   info   The RepInfo object to search
     *   @param   trace  If <code>true</code>, write debugging information
     *                   to standard output.
     * 
     *   @return  The specified Property if found, otherwise null.
     */
    public Property locateProperty (RepInfo info, boolean trace)
    {
        if (pathInfo.isEmpty ()) {
            // An empty path can't reach any property
            if (trace) {
                System.out.println ("Empty property path");
            }
            return null;
        }
        Object obj = pathInfo.get(0);
        if (!(obj instanceof String)) {
            // The initial qualifier must be a property name
            if (trace) {
                System.out.println ("Not a property name");
            }
            return null;
        }
        String top = (String) obj;
        if (trace) {
            System.out.println ("Getting proprerty " + top);
        }
        Property prop = info.getProperty (top);
        if (prop == null) {
            // No property of that name in RepInfo
            if (trace) {
                System.out.println ("Property is null");
            }
            return null;
        }
        int pathLen = pathInfo.size ();
        // Pass the CDR of the list to locateSubProperty.
        return locateSubProperty (prop, pathInfo.subList (1, pathLen), trace);
    }
    
    /* Recursive function for extracting a subproperty of a property. */
    private Property locateSubProperty (Property property, List path, boolean trace)
    {
        // If there's nothing left of the path, we're done.
        if (path.isEmpty ()) {
            return property;
        }
        List cdr = path.subList (1, path.size());
        PropertyArity arity = property.getArity ();
        PropertyType type = property.getType ();
        Object val = property.getValue ();
        if (trace) {
            System.out.println ("Property arity = " + arity + ", type = " + type);
        }
        // If the type isn't PROPERTY, then there are no subproperties.
        if (type != PropertyType.PROPERTY) {
            if (trace) {
                System.out.println ("Not a property, type is " + type.toString ());
            }
            return null;
        }
        Object obj = path.get (0);

        if (obj instanceof String) {
            Iterator iter;
            // Iterate through the property and see if any of the elements
            // are Properties that match the name.  
            String name = (String) obj;
            if (trace) {
                System.out.println ("Looking for subproperty " + name + 
                    " arity= " + arity.toString ());
            }
            if (arity.equals (PropertyArity.SCALAR)) {
                // There's just one shot at matching a scalar.
                Property p = (Property) property.getValue ();
                if (p.getName().equals (name)) {
                    return locateSubProperty (p, cdr, trace);
                }
                else {
                    return null;
                }
            }
            else if (arity.equals (PropertyArity.ARRAY)) {
                // We know it's an array of Properties, which saves much
                // hair-tearing.
                Property[] parray = (Property []) val;
                for (int i = 0; i < parray.length; i++) {
                    Property p = parray[i];
                    if (p.getName ().equals (name)) {
                        return locateSubProperty (p, cdr, trace);
                    }
                }
                return null;
            }
            else if (arity.equals (PropertyArity.LIST)) {
                iter = ((List) val).listIterator ();
                return getIteratedSubProperty (iter, name, cdr, trace);
            }
            else if (arity.equals (PropertyArity.SET)) {
                iter = ((Set) val).iterator ();
                return getIteratedSubProperty (iter, name, cdr, trace);
            }
            else if (arity.equals (PropertyArity.MAP)) {
                iter = ((Map) val).values().iterator();
                return getIteratedSubProperty (iter, name, cdr, trace);
            }
            else {
                // Should never happen, but keep compiler happy
                //System.out.println ("Unknown arity");
                return null;
            }
        }
        else if (obj instanceof Integer) {
            int idx = ((Integer) obj).intValue();
            //System.out.println ("Property index = " + idx + ", arity= " + arity.toString ());
            if (arity.equals (PropertyArity.LIST)) {
                List propList = (List) val;
                return locateSubProperty 
                    ((Property) propList.get (idx), cdr, trace);
            }
            else if (arity.equals (PropertyArity.ARRAY)) {
                Property[] propArr = (Property []) val;
                return locateSubProperty (propArr[idx], cdr, trace);
            }
            else {
                // Other arities are not indexable
                return null;
            }
        }
        else if (obj instanceof PropertyKey) {
            // This is applicable only to a Map.
            if (arity != PropertyArity.MAP) {
                return null;
            }
            return null;   // I'm not sure this case is even meaningful
        }
        else {
            // We should never get here
            return null;
        }
    }
    
    /* Walk through an Iterator, whose elements are Properties,
     * and return the subproperty by <code>path</code> of the first element
     * whose name matches <code>name</code>.
     */
    private Property getIteratedSubProperty (Iterator iter, 
                    String name, 
                    List path,
                    boolean trace)
    {
        while (iter.hasNext ()) {
            Property p = (Property) iter.next ();
            if (p.getName ().equals (name)) {
                return locateSubProperty (p, path, trace);
            }
        }
        return null;
    }
    
    
        
    private class PropertyKey
    {
        public Object key;
        
        public PropertyKey (Object obj)
        {
            key = obj;
        }
    }
}
