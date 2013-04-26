/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * A LinkedList dressed up as a stack for processing HTML objects.
 * It knows about certain elements and their history on the stack.
 *
 * @author Gary McGath
 *
 */
public class HtmlStack extends LinkedList {

    /** Elements which get special treatment. */
    private HtmlTagDesc headElement;
    private HtmlTagDesc bodyElement;
    private HtmlTagDesc framesetElement;
    
    private boolean headSeen;
    private boolean bodySeen;
    
    /** Sets the value of the HEAD element for easy comparison */
    protected void setHeadElement (HtmlTagDesc elem)
    {
        headElement = elem;
    }

    /** Sets the value of the HEAD element for easy comparison */
    protected void setBodyElement (HtmlTagDesc elem)
    {
        bodyElement = elem;
    }

    /** Sets the value of the HEAD element for easy comparison */
    protected void setFramesetElement (HtmlTagDesc elem)
    {
        bodyElement = elem;
    }

    /** Pops top element from element stack.  If we ever decide
     * to go to a different stack implementation, it's necessary
     * only to change these methods.  Also, they add some
     * type checking.
     * 
     * Name changed from "pop" to "popp" to avoid a conflict in Java 1.6
     * with the List class.
     *  */
    protected void popp ()
    {
        removeLast ();
    }
    
    /** Pushes an element onto the stack.  This should have
     * its element field set to function properly. */
    protected void push (JHOpenTag tag)
    {
        add (tag);
        HtmlTagDesc element = tag.getElement ();
        if (element == headElement) {
            headSeen = true;
        }
        else if (element == bodyElement) {
            bodySeen = true;
        }
    }

    /** Gets the top of the element stack without popping it. */
    protected JHOpenTag top ()
    {
        return (JHOpenTag) getLast();
    }
    
    /** Searches backwards through the element stack for a
     * match to a given tag.  Return -1 if no match. */
    protected int search (String tag) 
    {
        /* Supposedly this ListIterator setup works
         * for walking backwards. */
        ListIterator liter = listIterator 
                (size());
        int idx = size () - 1;
        while (liter.hasPrevious ()) {
            JHOpenTag stackTag = (JHOpenTag) liter.previous();
            HtmlTagDesc elem = stackTag.getElement ();
            if (elem.matches (tag)) {
                return idx;
            }
            idx--;
        }
        
        /* No match, return -1 */
        return -1;
    }
    
    /** Pops elements from the stack up to and including the
     * one indexed by idx */
    protected void popTo (int idx)
    {
        int npop = size () - idx;
        for (int i = 0; i < npop; i++) {
            removeLast();
        }
    }

    /** Returns <code>true</code> if a HEAD element has been
     *  pushed on the stack. */
    protected boolean isHeadSeen ()
    {
        return headSeen;
    }
    
    /** Returns <code>true</code> if a BODY element has been
     *  pushed on the stack. */
    protected boolean isBodySeen ()
    {
        return bodySeen;
    }
    
    /** Returns <code>true</code> if any element on the stack
     *  prohibits the specified tag. */
    protected boolean excludesTag (String tag) {
        Iterator iter = iterator ();
        while (iter.hasNext ()) {
            JHOpenTag stackTag = (JHOpenTag) iter.next ();
            if (stackTag.getElement ().excludesTag (tag)) {
                return true;
            }
        }
        return false;
    }
}
