/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * This class defines the permitted behavior of a particular HTML tag.
 * The full descriptive power of a DTD description isn't implemented here,
 * but content types and sequences of content are implemented.
 *
 * @author Gary McGath
 *
 */
public class HtmlTagDesc {
    
    /* Name of element.  Constructor forces it to lower case, regardless
     * of how it was specified. */
    private String _name;
    private boolean _openTagRequired;
    private boolean _closeTagRequired;
    
    
    /* Element tags in which this element can be nested.  Only tags for
     * elements with optional opening tags need to be listed here;
     * listing others will just reduce efficiency.  If there are no
     * applicable elements, this can be left null (which it is by
     * default). */
    private List _implicitContainers;
    
    /* Array of permitted content lists.  null indicates an empty element.
     * Each element of the array is a list of tag names which are permissible
     * at a given point.  
     */
    private List[] _contentArray;
    
    /* Array of excluded content strings.  Each String in the array is a tag which
     * may not be included in any descendant of the element. */
    private String[] _excludedContent;
    
    /** Array controlling the number of times each element of _contentArray
     * may be used. */
    protected int[] _sequence;
    
    /** Value in _sequence indicating an element may be used 0 or 1 times. */
    public final static int SEQ0_1 = 0;
    
    /** Value in _sequence indicating an element must be used exactly once. */
    public final static int SEQ1 = 1;

    /** Value in _sequence indicating an element may be used 1 or more times. */
    public final static int SEQ1_MANY = 2;

    /** Value in _sequence indicating an element may be used 0 or more times. */
    public final static int SEQ0_MANY = 3;
    
    /* List of Attributes which are recognized for this tag.
     * Will never be null, but may be empty. */
    private List _attributes;
    
    
    /** Constructor for simple case.
     * 
     *  @param name              Name of the element
     *  @param openTagRequired   <code>true</code> if an opening tag is required
     *  @param closeTagRequired  <code>true</code> if a closing tag is required
     *  @param content           List of permitted tags.  But what do I do when
     *                           a particular order is required?  Null if element
     *                           is defined at EMPTY.
     *  @param attributes        List of HtmlAttributeDesc elements enumerating
     *                           the permitted attributes.  May be null, in which
     *                           case _attributes will be stored as an empty list.
     */
    public HtmlTagDesc (String name,
                    boolean openTagRequired,
                    boolean closeTagRequired,
                    List content,
                    List attributes)
    {
        _name = name.toLowerCase ();
        _openTagRequired = openTagRequired;
        _closeTagRequired = closeTagRequired;
        _implicitContainers = new LinkedList ();
        if (content == null) {
            // Empty element, so there's nothing for the content array
            _contentArray = null;
        }
        else {
            _contentArray = new List[1];
            _contentArray[0] = content;
            _sequence = new int[1];
            _sequence[0] = SEQ0_MANY;  // assume most general case
        }
        if (attributes == null) {
            _attributes = new ArrayList (1);
        }
        else {
            _attributes = attributes;
        }
    }
    
    /** Constructor for sequenced case.
     * 
     *  @param name              Name of the element
     *  @param openTagRequired   <code>true</code> if an opening tag is required
     *  @param closeTagRequired  <code>true</code> if a closing tag is required
     *  @param sequence          Array indicating the sequencing of elements in
     *                           <code> content.  Must have the same length
     *                           as <code>sequence</code>.
     *  @param attributes        List of HtmlAttributeDesc elements enumerating
     *                           the permitted attributes.  May be null, in which
     *                           case _attributes will be stored as an empty list.
     */
    public HtmlTagDesc (String name,
                    boolean openTagRequired,
                    boolean closeTagRequired,
                    int[] sequence,
                    List[] contentArray,
                    List attributes)
    {
        _name = name.toLowerCase ();
        _openTagRequired = openTagRequired;
        _closeTagRequired = closeTagRequired;
        _implicitContainers = new LinkedList ();
        _sequence = sequence;
        _contentArray = contentArray;
        if (attributes == null) {
            _attributes = new ArrayList (1);
        }
        else {
            _attributes = attributes;
        }
    }
    
    /** Specifies tags which may not be included in this
     *  element or in any element nested at any depth
     *  within it.  Corresponds to the -(content) feature
     *  of the DTD. */
    public void setExcludedContent (String[] content)
    {
        _excludedContent = content;
    }
    
    /** Returns <code>true</code> if a given tag is excluded
     *  within this element.  It is necessary to call this
     *  method for each element on the stack to determine if
     *  it is excluded. */
    public boolean excludesTag (String tag)
    {
        if (_excludedContent == null) {
            return false;
        }
        for (int i = 0; i < _excludedContent.length; i++) {
            if (_excludedContent[i].equals (tag)) {
                return true;
            }
        }
        return false;
    }

    /** Alternative way of setting the attribute names.
     *  This can be used where all the attributes are
     *  unrestricted.  This will replace any previously
     *  set attributes. */
    public void setAttributes (String[] attributeArray)
    {
        List atts = new ArrayList (attributeArray.length);
        for (int i = 0; i < attributeArray.length; i++) {
            HtmlAttributeDesc desc = new HtmlAttributeDesc (attributeArray[i]);
            atts.add (desc);
        }
        _attributes = atts;
    }
    
    
    /** Provides the object with an array of element tags in which
     *  this element can be nested.  Only tags for
     * elements with optional opening tags may be listed here.
     */
    public void addImplicitContainer (HtmlTagDesc container)
    {
        _implicitContainers.add (container);
    }

    public boolean matches (String name)
    {
        return name.equals (_name);
    }
    
    /** Reports whether this is a temporary tag descriptor.
     *  Returns <code>false</code> unless overridden.
     */
    public boolean isTemp ()
    {
        return false;
    }
    

    /** Reports whether this element allows a given tag name
     *  in its content, at the specified index.  
     */
    protected boolean allowsTag (String tag, int index, HtmlDocDesc doc)
    {
        if (_contentArray == null) {
            // null means no content allowed
            return false;
        }
        /* Check for index out of bounds. */
        if (index >= _contentArray.length) {
            return false;
        }
        Iterator iter = _contentArray[index].iterator ();
        while (iter.hasNext ()) {
            String allowedTag;
            try {
                allowedTag = (String) iter.next ();
            }
            catch (Exception e) {
                // Catch bad casts here -- any non-strings
                // should be ignored.
                continue;
            }
            if (allowedTag.equals (tag)) {
                return true;
            }
        }
        
        /* We might still be OK if we can construct a set of
         * elements with optional opening tags which will fill
         * in the gap.  */
        HtmlTagDesc tagDesc = (HtmlTagDesc) doc.supportedElements.get (tag);
        if (tagDesc != null &&
                tagDesc._implicitContainers != null) {
            Iterator citer = tagDesc._implicitContainers.iterator ();
            while (citer.hasNext ()) {
                HtmlTagDesc ctnr = (HtmlTagDesc) citer.next ();
                // Call self recursively to try to insert the implicit
                // tag.  There may be more than one level of recursion,
                // at least theoretically.
                if (allowsTag (ctnr._name, index, doc)) {
                    JHOpenTag ctnrTag = new JHOpenTag (ctnr._name);
                    ctnrTag.setElement (ctnr);
                    doc.pushElementStack(ctnrTag);
                    return true;
                }
            }
        }
        return false;
    }
    
    /** Reports whether this element can be implicitly nested
     *  in an element with a given tag. There may be more than
     *  one implicit container for a tag; if the DTD is unambiguous,
     *  there should be only one which is permissible in any
     *  given context.
     */
    protected List implicitContainers (String tag)
    {
        return _implicitContainers;
    }
    
    /** Reports whether additional elements can be matched
     *  at the specified content index.  The index is assumed
     *  to be legal. */
    protected boolean canGetMoreAt (int index, int elemCount)
    {
        switch (_sequence[index]) {
            case SEQ0_1:
            case SEQ1:
                return (elemCount == 0);
            case SEQ1_MANY:
            case SEQ0_MANY:
                return true;
            default:
                return false;   // Should never happen
        }
    }
    
    /** Reports whether it's legal to advance to the next content
     *  index.  The index is assumed to be legal, but the one
     *  to which it's trying to advance may not be. */
    protected boolean canAdvanceFrom (int index, int elemCount)
    {
        if (index == _sequence.length - 1) {
            return false;   // No more content to match
        }
        switch (_sequence[index]) {
            case SEQ0_1:
            case SEQ0_MANY:
                return true;
            case SEQ1:
                return (elemCount == 1);
            case SEQ1_MANY:
                return (elemCount >= 1);
            default:
                return false;   // Should never happen
        }
    }

    /** Reports whether this element allows a given tag name
     *  in its content.  This version should be used only with
     *  element descriptors that aren't associated with tags,
     *  for determining if a hypothetical implied element could
     *  contain the given tag. 
     */
    protected boolean allowsTag (String tag, HtmlDocDesc doc)
    {
        return allowsTag (tag, 0, doc);
    }     


    protected boolean allowsPCData ()
    {
        if (_contentArray == null) {
            return false;
        }
        Iterator iter = _contentArray[0].iterator ();
        while (iter.hasNext ()) {
            Object contentItem = iter.next ();
            if (contentItem == HtmlSpecialToken.PCDATA) {
                return true;
            }
        }
        return false;
    }


    /** Returns the attribute with a given name, or null if
     *  no such attribute is defined for the element */
    protected HtmlAttributeDesc namedAttDesc (String name)
    {
        Iterator iter = _attributes.iterator ();
        while (iter.hasNext ()) {
            HtmlAttributeDesc desc = (HtmlAttributeDesc) iter.next ();
            if (desc.nameMatches (name)) {
                return desc;
            }
        }
        /* No match. */
        return null;
    }
    
    /** Accepts a list of attribute names, and returns a List
     *  of required attribute names which are not present
     *  in the parameter list.  Returns an empty List
     *  if all required attributes are present. */
    protected List missingRequiredAttributes (List names)
    {
        List val = new ArrayList (_attributes.size ());
        // Build a list of required attributes, which will
        // be whittled away by comparison with the parameter list
        List reqNames = new ArrayList (_attributes.size ());
        Iterator iter = _attributes.iterator ();
        while (iter.hasNext ()) {
            HtmlAttributeDesc desc = (HtmlAttributeDesc) iter.next ();
            if (desc.isRequired ()) {
                boolean found = false;
                Iterator niter = names.iterator ();
                while (niter.hasNext ()) {
                    String name = (String) niter.next ();
                    if (desc.nameMatches (name.toLowerCase ())) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    val.add (desc.getName ());
                }
            }
        }
        return val;
    }
    
    /** Returns true if the closing tag is required */
    protected boolean isCloseTagRequired ()
    {
        return _closeTagRequired;
    }

    /** Returns true if this element has empty content */
    protected boolean isContentEmpty ()
    {
        return _contentArray == null;
    }
}
