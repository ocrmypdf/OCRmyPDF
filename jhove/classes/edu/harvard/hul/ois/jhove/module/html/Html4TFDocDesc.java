/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.module.HtmlModule;
import java.util.*;

/**
 * Abstract class for common features of HTML 4.0 and 4.01 transitional and frameset
 * documents.  The differences between 4.0 and 4.01 are minor, as
 * are the differences between transitional and frameset so
 * most of the code is found here.
 *
 * @author Gary McGath
 *
 */
public abstract class Html4TFDocDesc extends Html4DocDesc {

    /** Code which is called from the static initializer of the
     *  subclasses.  Note that this is called before the class
     *  is instantiated, and may reference only static fields
     *  and subroutines. */
    protected static void classInit4 (Map stSupportedElements)
    {
        Html4DocDesc.classInit4(stSupportedElements);

        String name;
        HtmlTagDesc td;

        fontMarkup = new String[]
            { "tt", "i", "b", "u", "s", "strike", "big", "small" };
        listMarkup = new String []
            { "ul", "ol", "dir", "menu" };
        specialMarkup = new String[]
            { "a", "img", "applet", "object", "font",
              "basefont", "br", "script", "map", 
              "q", "sub", "sup", "span", "bdo", "iframe" };
        /* inlineContent lists all the content types which are permitted in
         * the markup elements.  For a first cut, strings signify the
         * name of the element which is permitted.  */
        inlineContent = new ArrayList(35);
        addStringsToList (fontMarkup, inlineContent);
        addStringsToList (phraseMarkup, inlineContent);
        addStringsToList (specialMarkup, inlineContent);
        addStringsToList (formMarkup, inlineContent);
        inlineContent.add (HtmlSpecialToken.PCDATA);

        blockContent = new ArrayList (20);
        addStringsToList (headings, blockContent);
        addStringsToList (listMarkup, blockContent);
        String[] blockMisc = new String[]
            {"p", "pre", "dl", "div", "center", "noscript",
              "blockquote", "form", "hr", "table", "fieldset", "address" };
        addStringsToList (blockMisc, blockContent);
        
        flowContent = new ArrayList (30);
        flowContent.addAll (blockContent);
        flowContent.addAll (inlineContent);

        /* Content for the BODY element, also used for other elements */
        bodyContent = new ArrayList (flowContent.size () + 3);
        bodyContent.addAll (flowContent);
        bodyContent.add ("ins");
        bodyContent.add ("del");

        listContent = new ArrayList (1);
        listContent.add ("li");

        thtdAtts = new ArrayList (bigAttrs.size() + 7);  // common attribute list for TH and TD
        thtdAtts.addAll (bigAttrs);
        addSimpleAttribute (thtdAtts, "abbr");
        addSimpleAttribute (thtdAtts, "axis");
        addSimpleAttribute (thtdAtts, "headers");
        addSimpleAttribute (thtdAtts, "scope");
        thtdAtts.add (halignAtt);
        thtdAtts.add (valignAtt);
        addSelfAttribute (thtdAtts, "nowrap");
        addSimpleAttribute (thtdAtts, "rowspan");
        addSimpleAttribute (thtdAtts, "colspan");
        addSimpleAttribute (thtdAtts, "bgcolor");
        addSimpleAttribute (thtdAtts, "width");
        addSimpleAttribute (thtdAtts, "height");
    }

    /** Defines the A element. */
    protected static void addAElement (Map stSupportedElements)
    {
        /* The Anchor (A) element */
        String name = "a";
        List atts = new ArrayList (bigAttrs.size () + 14);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "hreflang");
        addSimpleAttribute (atts, "target");  // not in strict
        addSimpleAttribute (atts, "rel");
        addSimpleAttribute (atts, "rev");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "shape");
        addSimpleAttribute (atts, "rect");
        addSimpleAttribute (atts, "coords");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        List content = new ArrayList (inlineContent.size ());
        content.addAll (inlineContent);
        content.remove ("a");
        
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addAppletElement 
        (Map stSupportedElements, HtmlAttributeDesc ialignAtt)
    {
        String name = "applet";
        List content = new ArrayList (flowContent.size ());
        content.addAll (flowContent);
        content.add ("param");
        List atts = new ArrayList (9);
        addSimpleAttribute (atts, "codebase");
        addSimpleAttribute (atts, "archive");
        addSimpleAttribute (atts, "code");
        addSimpleAttribute (atts, "object");
        addSimpleAttribute (atts, "alt");
        addSimpleAttribute (atts, "alt");
        addSimpleAttribute (atts, "name");
        addRequiredAttribute (atts, "width");
        addRequiredAttribute (atts, "height");
        atts.add (ialignAtt);
        addSimpleAttribute (atts, "hspace");
        addSimpleAttribute (atts, "vspace");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        stSupportedElements.put (name, td);
   
    }
    
    protected static void addAreaElement 
        (Map stSupportedElements, HtmlAttributeDesc shapeAtt)
    {
        String name = "area";
        List atts = new ArrayList (10);
        atts.add (shapeAtt);
        addSimpleAttribute (atts, "coords");
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "target");
        atts.add (new HtmlAttributeDesc ("nohref", 
            new String[] {"nohref"}, 
            HtmlAttributeDesc.IMPLIED));
        atts.add (new HtmlAttributeDesc ("alt",
            null,
            HtmlAttributeDesc.REQUIRED));
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addBaseElement (Map stSupportedElements)
    {
        String name = "base";
        List atts = new ArrayList (2);
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "target");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addBasefontElement (Map stSupportedElements)
    {
        String name = "basefont";
        List atts = new ArrayList (4);
        addSimpleAttribute (atts, "id");
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "color");
        addSimpleAttribute (atts, "face");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }
    
    protected static void addBlockquoteElement (Map stSupportedElements)
    {
        String name = "blockquote";
        List content = new ArrayList (blockContent.size () + 1);
        content.addAll (blockContent);
        content.add ("script");
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "cite");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, flowContent, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addBrElement (Map stSupportedElements, List coreAttrs)
    {
        String name = "br";
        List atts = new ArrayList (coreAttrs.size () + 1);
        atts.addAll (coreAttrs);
        atts.add (new HtmlAttributeDesc ("clear", 
            new String[] {"left", "all", "right", "none" },
            HtmlAttributeDesc.OTHER));
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addButtonElement 
        (Map stSupportedElements)
    {
        String name = "button";
        List content = new ArrayList (formMarkup.length + 3);
        addStringsToList(formMarkup, content);
        content.add ("form");
        content.add ("isindex");
        content.add ("fieldset");
        content.add ("iframe");
        List atts = new ArrayList (biggerAttrs.size () + 8);
        atts.addAll (biggerAttrs);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        atts.add (new HtmlAttributeDesc ("type",
            new String[] {"button", "submit" , "reset"},
            HtmlAttributeDesc.OTHER));
        addSelfAttribute (atts, "disabled");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
    }

    protected static void addCaptionElement 
        (Map stSupportedElements, List inlineContent, 
                HtmlAttributeDesc valignAtt)
    {
        String name = "caption";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.add (new HtmlAttributeDesc ("align", 
            new String[] {"top", "bottom", "left", "right" },
            HtmlAttributeDesc.IMPLIED));
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
    }
    
    protected static void addCenterElement (Map stSupportedElements)
    {
        String name = "center";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, flowContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addDirElement (Map stSupportedElements)
    {
        String name = "dir";
        List atts = new ArrayList (1);
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addDivElement (Map stSupportedElements)
    {
        String name = "div";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        atts.add (new HtmlAttributeDesc
            ("align",
             new String [] {"left", "center", "right", "justify"},
             HtmlAttributeDesc.IMPLIED));
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, flowContent, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addDlElement 
        (Map stSupportedElements)
    {
        String name = "dl";
        List dlContent = new ArrayList (2);
        addStringsToList(new String[] { "dt", "dd" }, dlContent);
        List atts = new ArrayList (bigAttrs.size () + 1);
        addSelfAttribute(atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, dlContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Adds the Font element. */
    protected static void addFontElement (Map stSupportedElements)
    {
        String name = "font";
        List atts = new ArrayList (bigAttrs.size () + 10);
        atts.addAll (bigAttrs);
        atts.addAll (i18nAttrs);
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "color");
        addSimpleAttribute (atts, "face");
        
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
   
    }

    /** Adds to Frame element. */
    protected static void addFrameElement (Map stSupportedElements)
    {
        String name = "frame";
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "longdesc");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "src");
        addSimpleAttribute (atts, "marginwidth");
        addSimpleAttribute (atts, "marginheight");
        addSelfAttribute (atts, "noresize");
        atts.add (new HtmlAttributeDesc ("scrolling",
                new String[] { "yes", "no", "auto" },
                HtmlAttributeDesc.OTHER));
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    /** Adds the Frameset element.  This is called only for 
     *  4.0 and 4.01 Frameset docuemnts. */
    protected static void addFramesetElement 
        (Map stSupportedElements)
    {
        String name = "frameset";
        List content = new ArrayList (3);
        addStringsToList (new String[] {"frameset", "frame", "noframes" },
                content);
        List atts = new ArrayList (coreAttrs.size () + 4);
        atts.addAll (coreAttrs);
        addSimpleAttribute(atts, "rows");
        addSimpleAttribute(atts, "cols");
        addSimpleAttribute(atts, "onload");
        addSimpleAttribute(atts, "onunload");
        HtmlTagDesc td = new HtmlTagDesc (name, false, false, content, atts);
        stSupportedElements.put (name, td);
    }
        
    protected static void addHeadElement (Map stSupportedElements)
    {
        String name = "head";
        String[] headMisc = new String[] 
            {"script", "style", "meta", "link" };
        List headContent = new ArrayList (7);
        headContent.add ("title");
        headContent.add ("isindex");
        headContent.add ("base");
        headContent.add ("script");
        headContent.add ("style");
        headContent.add ("meta");
        headContent.add ("link");
        headContent.add ("object");
        HtmlTagDesc td = new HtmlTagDesc (name, false, false, headContent, null);
        stSupportedElements.put (name, td);
        /* Attributes TITLE (required), ISINDEX (optional), and BASE (optional)
         * are supposed to come in that order, ahead of anything else.
         * For the moment, just toss them in with the rest. */
        addStringsToList (headMisc, headContent);
    }

    protected static void addHrElement (Map stSupportedElements)
    {
        String name = "hr";
        List atts = new ArrayList (bigAttrs.size () + 4);
        atts.add (new HtmlAttributeDesc ("align",
            new String[] { "left", "center", "right" },
            HtmlAttributeDesc.IMPLIED));
        addSelfAttribute (atts, "noshade");
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "width");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }


    protected static void addInputElement 
        (Map stSupportedElements)
    {
        final String name = "input";
        List atts = new ArrayList (biggerAttrs.size () + 20);
        atts.addAll (biggerAttrs);
        atts.add (new HtmlAttributeDesc ("type", 
            new String[] {"text", "password", "checkbox", "radio", "submit", 
                        "reset", "file", "hidden", "image", "button"},
            HtmlAttributeDesc.OTHER));
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        addSelfAttribute (atts, "checked");
        addSelfAttribute (atts, "disabled");
        addSelfAttribute (atts, "readonly");
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "maxlength");
        addSimpleAttribute (atts, "src");
        addSimpleAttribute (atts, "alt");
        addSimpleAttribute (atts, "usemap");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        addSimpleAttribute (atts, "onselect");
        addSimpleAttribute (atts, "onchange");
        addSimpleAttribute (atts, "accept");
        atts.add (new HtmlAttributeDesc ("align",
            new String[] { "top", "middle", "bottom", "left", "right" },
            HtmlAttributeDesc.IMPLIED));
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, null, atts);
        stSupportedElements.put (name, td);
    }

    
    protected static void addLegendElement (Map stSupportedElements)
    {
        final String name = "label";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "accesskey");
        atts.add (new HtmlAttributeDesc ("align",
            new String[] {"top", "left", "bottom", "right" },
            HtmlAttributeDesc.IMPLIED));
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
    }
    
    protected static void addLiElement 
        (Map stSupportedElements)
    {
        final String name = "li";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "value");
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, flowContent, atts);
        stSupportedElements.put (name, td);   
    }

    protected static void addLinkElement 
        (Map stSupportedElements)
    {
        final String name = "link";
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "charset");
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "hreflang");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "rel");
        addSimpleAttribute (atts, "rev");
        addSimpleAttribute (atts, "media");
        addSimpleAttribute (atts, "target");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addMenuElement (Map stSupportedElements)
    {
        final String name = "menu";
        List atts = new ArrayList (1);
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }
    
    
    /** Adds the NOFRAMES element.  The content differs between Transitional
     *  and Frameset DTD's. */
    protected static void addNoframesElement (Map stSupportedElements, int version)
    {
        final String name = "noframes";
        List content;
        if (version == HtmlModule.HTML_4_01_FRAMESET ||
                version == HtmlModule.HTML_4_0_FRAMESET) {
            content = new ArrayList (1);
            // There's something I obviously don't understand about DTD syntax.
            // The content is given as (BODY) -(NOFRAMES)
            // But if the only allowed element is BODY, it's superfluous to
            // exclude NOFRAMES.  What am I missing?
            content.add ("body");
        }
        else {
            content = flowContent;
        }
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, bigAttrs);
        stSupportedElements.put (name, td);
    }


    protected static void addNoscriptElement (Map stSupportedElements)
    {
        final String name = "noscript";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, flowContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addObjectElement  (Map stSupportedElements)
    {
        final String name = "object";
        List atts = new ArrayList (biggerAttrs.size () + 13);
        atts.addAll (biggerAttrs);
        addSelfAttribute (atts, "declare");
        addSimpleAttribute (atts, "classid");
        addSimpleAttribute (atts, "codebase");
        addSimpleAttribute (atts, "data");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "codetype");
        addSimpleAttribute (atts, "archive");
        addSimpleAttribute (atts, "standby");
        addSimpleAttribute (atts, "height");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "usemap");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "align");
        addSimpleAttribute (atts, "border");
        addSimpleAttribute (atts, "hspace");
        addSimpleAttribute (atts, "vspace");
    }

    protected static void addOlElement 
        (Map stSupportedElements)
    {
        final String name = "ol";
        List atts = new ArrayList (bigAttrs.size () + 3);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "type");
        addSelfAttribute (atts, "compact");
        addSimpleAttribute (atts, "start");
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addPElement (Map stSupportedElements)
    {
        final String name = "p";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        atts.add (new HtmlAttributeDesc
            ("align",
             new String [] {"left", "center", "right", "justify"},
             HtmlAttributeDesc.IMPLIED));
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, inlineContent, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addPreElement (Map stSupportedElements)
    {
        final String name = "pre";
        List preContent = new ArrayList (inlineContent.size ());
        preContent.addAll(inlineContent);
        /* Take out excluded elements */
        removeStringsFromList (preContent,
            new String []
             {"img", "object", "big", "small", "sub", "sup"});
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "width");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, preContent, atts);
        stSupportedElements.put (name, td);   
    }

    protected static void addScriptElement  (Map stSupportedElements)
    {
        final String name = "script";
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        List atts = new ArrayList (6);
        addSimpleAttribute (atts, "charset");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "language");
        addSimpleAttribute (atts, "src");
        addSelfAttribute (atts, "defer");
        addSimpleAttribute (atts, "event");
        addSimpleAttribute (atts, "for");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addTableElement (Map stSupportedElements)
    {
        final String name = "table";
        List atts = new ArrayList (biggerAttrs.size () + 10);
        atts.addAll (biggerAttrs);
        addSimpleAttribute (atts, "summary");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "border");
        atts.add (new HtmlAttributeDesc ("frame",
            new String[] { "void", "above", "below", "hsides", 
                         "lhs", "rhs", "vsides", "box", "border" },
            HtmlAttributeDesc.IMPLIED));
        atts.add (new HtmlAttributeDesc ("rules",
            new String[] { "none", "groups", "rows", "cols", "all" },
            HtmlAttributeDesc.IMPLIED));
                           
        addSimpleAttribute (atts, "rules");
        addSimpleAttribute (atts, "cellspacing");
        addSimpleAttribute (atts, "cellpadding");
        atts.add (new HtmlAttributeDesc ("align",
            new String[] { "left", "center", "right" },
            HtmlAttributeDesc.IMPLIED));
        addSimpleAttribute (atts, "bgcolor");
        addSimpleAttribute (atts, "datapagesize");
        List[] contentArray = new List[5];
        int[] contentSequence = new int[] 
                { HtmlTagDesc.SEQ0_1, 
                  HtmlTagDesc.SEQ0_MANY, 
                  HtmlTagDesc.SEQ0_1,
                  HtmlTagDesc.SEQ0_1,
                  HtmlTagDesc.SEQ1_MANY };
        List content = new ArrayList (1);
        content.add ("caption");
        contentArray[0] = content;
        
        content = new ArrayList(2);
        content.add ("col");
        content.add ("colgroup");
        contentArray[1] = content;
        
        content = new ArrayList (1);
        content.add ("thead");
        contentArray[2] = content;
        
        content = new ArrayList (1);
        content.add ("tfoot");
        contentArray[3] = content;
        
        content = new ArrayList (1);
        content.add ("tbody");
        contentArray[4] = content;
        
        HtmlTagDesc td = new HtmlTagDesc 
            (name, true, true, contentSequence, contentArray, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addTrElement (Map stSupportedElements)
    {
        final String name = "tr";
        List atts = new ArrayList (bigAttrs.size() + 3);
        atts.addAll (bigAttrs);
        atts.add (halignAtt);
        atts.add (valignAtt);
        addSimpleAttribute (atts, "bgcolor");
        List content = new ArrayList (2);
        content.add ("th");
        content.add ("td");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        td.addImplicitContainer((HtmlTagDesc) stSupportedElements.get ("tbody"));
        stSupportedElements.put (name, td);
    }

    protected static void addUlElement (Map stSupportedElements)
    {
        final String name = "ul";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "type");
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

}
