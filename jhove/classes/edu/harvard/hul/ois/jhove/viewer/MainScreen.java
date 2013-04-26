/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import java.awt.*;

/**
 * Static methods for positioning windows on the main screen.
 * 
 * @author Gary McGath
 *
 */
public class MainScreen {

    /**
     *  Private constructor to prevent instantiation
     */
    private MainScreen ()
    {
        
    }
    
    
    /**
     *  Center the window on the main screen.
     */
    public static void centerWindow (Window win)
    {
        Rectangle devBounds = mainBounds ();
        Rectangle winBounds = win.getBounds ();
        int lmargin = (devBounds.width - winBounds.width) / 2;
        int tmargin = (devBounds.height - winBounds.height) / 2;
        // Don't go off the edge
        if (lmargin < 0) {
            lmargin = 0;
        }
        if (tmargin < 0) {
            tmargin = 0;
        }
        win.setLocation (lmargin, tmargin);
    }


    /**
     *  Center the window at the top of the main screen.
     */
    public static void centerTopWindow (Window win)
    {
        Rectangle devBounds = mainBounds ();
        Rectangle winBounds = win.getBounds ();
        int lmargin = (devBounds.width - winBounds.width) / 2;
        // Don't go off the edge
        if (lmargin < 0) {
            lmargin = 0;
        }
        win.setLocation (lmargin, 0);
    }
    
    
    /**
     *  Returns the bounds of the main monitor device.
     */
    public static Rectangle mainBounds ()
    {
        GraphicsEnvironment ge = GraphicsEnvironment.
                getLocalGraphicsEnvironment();
        GraphicsDevice dev = ge.getDefaultScreenDevice();
        GraphicsConfiguration conf = dev.getDefaultConfiguration ();
        return conf.getBounds ();
    }
}
