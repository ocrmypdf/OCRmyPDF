/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.module.HtmlModule;
import java.util.*;
/**
 * Abstract class for the HTML 4.01 Transitional and Frameset document
 * types.  These are identical except for one element apiece, so nearly
 * all the code is here or in its superclasses.
 * 
 * @author Gary McGath
 *
 */
public abstract class Html4_01TFDocDesc extends Html4TFDocDesc {

    /** Initialization code.  This is called from the static initializer
     *  of our subclasses. */
    protected static void classInit4 (Map stSupportedElements, int version)
    {
        Html4TFDocDesc.classInit4(stSupportedElements);
        int i;
        String name;
        HtmlTagDesc td;
        
        for (i = 0; i < fontMarkup.length; i++) {
            name = fontMarkup[i];
            td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
            stSupportedElements.put (name, td);
        }
        
        /* Phrase elements. */
        for (i = 0; i < phraseMarkup.length; i++) {
            name = phraseMarkup[i];
            td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
            stSupportedElements.put (name, td);
        }
        
        addSupElement (stSupportedElements);
        addSubElement (stSupportedElements);
        addSpanElement (stSupportedElements);
        addBdoElement (stSupportedElements);
        addBasefontElement (stSupportedElements);
        addFontElement (stSupportedElements);
        addBrElement (stSupportedElements, coreAttrs);

        addAddressElement (stSupportedElements);
        addDivElement (stSupportedElements);
        addCenterElement (stSupportedElements);
        addAElement (stSupportedElements);
        addMapElement (stSupportedElements);
        
        HtmlAttributeDesc shapeAtt = new HtmlAttributeDesc ("shape", 
            new String[] {"rect", "circle", "poly", "default" },
            HtmlAttributeDesc.REQUIRED);
        addAreaElement (stSupportedElements, shapeAtt);
        addLinkElement (stSupportedElements);
        addImgElement (stSupportedElements);
        addObjectElement (stSupportedElements);
        addParamElement (stSupportedElements);
        HtmlAttributeDesc ialignAtt = new HtmlAttributeDesc ("align",
                new String[] { "top", "middle", "bottom", "left", "right" },
                HtmlAttributeDesc.IMPLIED);
        addAppletElement (stSupportedElements, ialignAtt);
        addHrElement (stSupportedElements);
        addPElement (stSupportedElements);

        /* The heading (H1-H6) elements */
        for (i = 0; i < headings.length; i++) {
            name = headings[i];
            td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
            stSupportedElements.put (name, td);
        }

        addPreElement (stSupportedElements);
        addQElement (stSupportedElements);
        addBlockquoteElement (stSupportedElements);
        addInsElement (stSupportedElements);
        addDelElement (stSupportedElements);
        
        addDlElement (stSupportedElements);
        addDtElement (stSupportedElements);
        addDdElement (stSupportedElements);

        addOlElement (stSupportedElements);
        addUlElement (stSupportedElements);
        addDirElement (stSupportedElements);
        addMenuElement (stSupportedElements);
        addLiElement (stSupportedElements);
        addFormElement (stSupportedElements);
        addLabelElement (stSupportedElements);
        
        addInputElement (stSupportedElements);
        addSelectElement (stSupportedElements);
        addOptgroupElement (stSupportedElements);
        addOptionElement (stSupportedElements);
        addTextareaElement (stSupportedElements);
        addFieldsetElement (stSupportedElements);
        addLegendElement (stSupportedElements);
        addButtonElement (stSupportedElements);
        addTableElement (stSupportedElements);
        
        HtmlAttributeDesc halignAtt = new HtmlAttributeDesc
            ("align",
             new String [] {"left", "center", "right", "justify", "char"},
             HtmlAttributeDesc.IMPLIED);
        HtmlAttributeDesc valignAtt = 
            new HtmlAttributeDesc ("valign", 
                new String[] { "top", "middle", "bottom", "baseline" },
                HtmlAttributeDesc.IMPLIED);
        List cellalignAttrs = new ArrayList (4);  // combine cellhalign and cellvalign
        cellalignAttrs.add (new HtmlAttributeDesc ("align",
                new String[] {"left", "center", "right", "justify", "char" },
                HtmlAttributeDesc.IMPLIED));
        addSimpleAttribute (cellalignAttrs, "char");
        addSimpleAttribute (cellalignAttrs, "charoff");
        cellalignAttrs.add (valignAtt);
        addTheadElement (stSupportedElements, cellalignAttrs);
        addTfootElement (stSupportedElements, cellalignAttrs);
        addTbodyElement (stSupportedElements, cellalignAttrs);
        addTrElement (stSupportedElements);

        
        addThElement (stSupportedElements);
        addTdElement (stSupportedElements); 
        addCaptionElement 
            (stSupportedElements, inlineContent, valignAtt);
        
        addColgroupElement (stSupportedElements, cellalignAttrs);
        addColElement (stSupportedElements, cellalignAttrs);
        
        addHeadElement (stSupportedElements);
        addTitleElement (stSupportedElements);
        addBaseElement (stSupportedElements);
        addMetaElement (stSupportedElements);
        addScriptElement (stSupportedElements);
        addNoscriptElement (stSupportedElements);
        addStyleElement (stSupportedElements);
         
        /* The HTML element */
        name = "html";
        List htmlContent = new ArrayList (2);
        htmlContent.add ("head");
        if (version == HtmlModule.HTML_4_01_FRAMESET) {
            htmlContent.add ("frameset");
        }
        else {
            htmlContent.add ("body");
        }
        td = new HtmlTagDesc (name, false, false, htmlContent, i18nAttrs);
        stSupportedElements.put (name, td);
        addNoframesElement (stSupportedElements, version);     
        if (version == HtmlModule.HTML_4_01_FRAMESET) {
            addFramesetElement (stSupportedElements);
            addFrameElement (stSupportedElements);
        }
        addBodyElement (stSupportedElements);
    }

    private static void addFormElement (Map stSupportedElements)
    {
        final String name = "form";
        List atts = new ArrayList (bigAttrs.size () + 9);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "action");
        addSimpleAttribute (atts, "method");
        addSimpleAttribute (atts, "enctype");
        addSimpleAttribute (atts, "accept");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "onsubmit");
        addSimpleAttribute (atts, "onreset");
        addSimpleAttribute (atts, "target");
        addSimpleAttribute (atts, "accept-charset");
        List formContent = new ArrayList (flowContent.size ());
        formContent.addAll (flowContent);
        //formContent.add ("script");
        removeStringsFromList (formContent, new String[] { "form" });
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, formContent, atts);
        stSupportedElements.put (name, td);
    }


    private static void addImgElement (Map stSupportedElements)
    {
        String name = "img";
        List atts = new ArrayList (bigAttrs.size () + 10);
        atts.addAll (bigAttrs);
        addRequiredAttribute (atts, "src");
        addRequiredAttribute (atts, "alt");
        addSimpleAttribute (atts, "longdesc");
        addSimpleAttribute (atts, "name");  // new to 4.01
        addSimpleAttribute (atts, "height");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "usemap");
        addSelfAttribute (atts, "ismap");
        atts.add (new HtmlAttributeDesc ("align",
            new String[] { "top", "middle", "bottom", "left", "right" },
            HtmlAttributeDesc.IMPLIED));
        addSimpleAttribute (atts, "border");
        addSimpleAttribute (atts, "hspace");
        addSimpleAttribute (atts, "vspace");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

}
