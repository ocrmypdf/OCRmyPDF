/**********************************************************************
 * JhoveView - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import java.awt.*;
import javax.swing.*;
import java.awt.event.*;

/**
 *   Window for showing progress of file processing.
 *   We may or may not have the total length available;
 *   if we do, we show the total length as part of the
 *   information. 
 *   Normally we keep one window alive for the whole application,
 *   showing and hiding it as needed.
 */
public class ProgressWindow extends JFrame{

    private long _contentLength;
    private long _byteCount;
    private String _docName;
    private JLabel _progressLabel;
    private JLabel _docNameLabel;
    private int _progressState;
    
    /**
     *   Progress state: Indeterminate or not yet started.
     */
    public final static int UNKNOWN = 0;
    /**
     *   Progress state: URI is being downloaded.
     */
    public final static int DOWNLOADING = 1;
    /**
     *   Progress state: Processing the document.
     */
    public final static int PROCESSING = 2;


    /**
     *  Constructor.
     *
     *  @param canceler  An ActionListener which responds to the
     *                   Cancel button.
     */
    public ProgressWindow (ActionListener canceler)
    {
        Font fileFont = new Font ("Dialog", Font.PLAIN, 14);
        Font progFont = new Font ("Dialog", Font.PLAIN, 12);
        Dimension labelDim = new Dimension (460, 24);
        _docNameLabel = new JLabel ();
        _docNameLabel.setHorizontalAlignment (SwingConstants.CENTER);
        _docNameLabel.setFont (fileFont);
        _docNameLabel.setMinimumSize (labelDim);
        _docNameLabel.setPreferredSize (labelDim);
        getContentPane ().add (_docNameLabel, BorderLayout.NORTH);

        _progressLabel = new JLabel ();
        _progressLabel.setHorizontalAlignment (SwingConstants.CENTER);
        _progressLabel.setFont (progFont);
        _progressLabel.setMinimumSize (labelDim);
        _progressLabel.setPreferredSize (labelDim);
        getContentPane ().add (_progressLabel, BorderLayout.CENTER);

        // Put the Cancel button inside a panel so it doesn't
        // fill the whole space.
        JPanel botPanel = new JPanel ();
        getContentPane ().add (botPanel, BorderLayout.SOUTH);
        JButton cancelButton = new JButton ("Cancel");
        botPanel.add (cancelButton);
        cancelButton.addActionListener (canceler);

        setTitle ("Progress");
        setDefaultCloseOperation (JFrame.DO_NOTHING_ON_CLOSE);
        pack ();
        MainScreen.centerTopWindow (this);

        _contentLength = -1;
        _byteCount = -1;
        _progressState = UNKNOWN;
    }

    /** 
     *  Set the total length to be displayed.  If this is set
     *  to a positive number, then the display will show 
     *  "xxxx bytes of yyyy".  If it is not set, or is set
     *  to a zero or negative number, the display will show
     *  "xxxx bytes".
     *  
     *  @param   length  The length to display
     *  @param   update  If <code>true</code>, requests a display update.
     */
    public void setContentLength (long length, boolean update)
    {
        _contentLength = length;
        if (update) {
            updateDisplay ();
        }
    }
    
    /**  Set the progress state.  
     *
     *  @param   state   The state value to assign.  Valid values are
     *                   UNKNOWN, DOWNLOADING, and PROCESSING.
     *  @param   update  If <code>true</code>, requests a display update
     */
    public void setProgressState (int state, boolean update) {
        _progressState = state;
        if (update) {
            updateDisplay ();
        }
    }


    /**
     *  Set the name of the document being displayed.
     *
     *  @param   name    The file name or URL to display
     *  @param   update  If <code>true</code>, requests a display update
     */
    public void setDocName (String name, boolean update) 
    {
        _docName = name;
        if (update) {
            updateDisplay ();
        }
    }


    /**
     *  Update the byte count.  Setting the count to a negative number blanks
     *  the byte count pane.
     *
     *  @param   count   The new byte count value
     *  @param   update  If <code>true</code>, requests a display update
     */
    public void setByteCount (long count, boolean update)
    {
        _byteCount = count;
        if (update) {
            updateDisplay ();
        }
    }

    private void updateDisplay ()
    {
        String progString = "";
        String txt;
        switch (_progressState) {
            case DOWNLOADING:
                txt = "Downloading " + _docName;
                break;
            case PROCESSING:
                txt = "Processing " + _docName;
                break;
            default:
                txt = _docName;
                break;
        }
        _docNameLabel.setText (txt);
        if (_byteCount >= 0) {
            progString = Long.toString (_byteCount) + " bytes";
            if (_contentLength > 0) {
                progString += " out of " + Long.toString (_contentLength);
            }
        }
        _progressLabel.setText (progString);
        Container content = getContentPane ();
        content.update (content.getGraphics ());
    }
}
