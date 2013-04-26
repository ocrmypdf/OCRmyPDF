/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import edu.harvard.hul.ois.jhove.*;
//import javax.swing.*;

/**
 * This is an output handler which connects JHOVE output to the
 * Swing interface of the viewer application.  It is responsible
 * for creating appropriate windows and making them known to (?).
 *
 * @author Gary McGath
 *
 */
public class ViewHandler extends HandlerBase {

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "VIEW";
    private static final String RELEASE = "1.0";
    private static final int [] DATE = {2004, 11, 2};
    private static final String NOTE = "This is the JHOVE Viewer output " +
        "handler";
    private static final String RIGHTS = "Copyright 2004 by JSTOR and " +
        "the President and Fellows of Harvard College. " +
        "Released under the terms of the GNU Lesser General Public License.";

    private JhoveWindow _jhwin;
    
    private ViewWindow _viewWin;
    private String syncStr = "anyoldtext";   // object just for synchronizing

    // Initial position for view windows.  
    // Stagger them by adding an increment each time.
    private static int viewWinXPos = 24;
    private static int viewWinYPos = 24;
    // Original positions for cyclying back to.
    private static final int viewWinOrigXPos = 24;
    private static final int viewWinOrigYPos = 24;
    private static final int viewWinXInc = 25;
    private static final int viewWinYInc = 22;
    
    private int nDocs;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a ViewHandler.
     * 
     *  @param   jhwin   The JhoveWindow which acts as the parent to
     *                   output windows.
     */
    public ViewHandler (JhoveWindow jhwin, App app, JhoveBase base)
    {
        super (NAME, RELEASE, DATE, NOTE, RIGHTS);
        _app = app;
        _base = base;
        base.setCallback (jhwin);
        Agent agent = new Agent ("Harvard University Library",
                                 AgentType.EDUCATIONAL);
        agent.setAddress ("Office for Information Systems, " +
                          "90 Mt. Auburn St., " +
                          "Cambridge, MA 02138");
        agent.setTelephone ("+1 (617) 495-3724");
        agent.setEmail("jhove-support@hulmail.harvard.edu");
        _vendor = agent;
        _jhwin = jhwin;

    }

    /** Do the initial output.  This needs to set up the window. */
    public void showHeader ()
    {
        _viewWin = new ViewWindow (_app, _base, _jhwin);
        nDocs = 0;
    }

    /**
     *  Outputs the information contained in a RepInfo object.
     *  showHeader must be called to set up the ViewWindow before
     *  this is called.
     * 
     *  I need to break out part of the ViewWindow code to here so
     *  it can produce the output for one file.
     */
    public void show (RepInfo info)
    {
        _viewWin.addRepInfo (info, _app, _base);
        ++nDocs;
    }
    
    public void show ()
    {
    }
    
    public void show (App app)
    {
    }
    
    public void show (Module module)
    {
    }


    /** Complete the output.  Does this have to do anything? */
    public void showFooter ()
    {
        // If no files were processed, just discard the window. */
        if (nDocs == 0) {
            _viewWin.dispose ();
        }
        // We synchronize this against the modal dialogs,
        // since otherwise the application is apt to put up
        // viewWin as a frozen window over the modal dialog.
        synchronized (syncStr) {
            //MainScreen.centerWindow (viewWin);
            _viewWin.setLocation (viewWinXPos, viewWinYPos);
            viewWinXPos += viewWinXInc;
            viewWinYPos += viewWinYInc;
            
            // After a while, cycle back to the original positions
            // After a while, cycle back to the original positions
            if (viewWinXPos > viewWinOrigXPos + 320) {
                viewWinXPos = viewWinOrigXPos;
            }
            if (viewWinYPos > viewWinOrigYPos + 160) {
                viewWinYPos = viewWinOrigYPos;
            }
            _viewWin.show ();
        }
        _viewWin.expandRows ();
        _viewWin.show ();
    }

    /**
     *  Outputs information about the OutputHandler specified
     *  in the parameter.
     *  Since this never should occur in a normal list of
     *  handlers, it's unnecessary to do anything (I think).
     */
    public void show (OutputHandler handler)
    {
    }

}
