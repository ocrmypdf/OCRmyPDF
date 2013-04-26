/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;


/**
 * Window for setting preferences for the Jhove viewer.
 *
 * @author Gary McGath
 *
 */
public class PrefsWindow extends JDialog 
{
    private JhoveWindow jhoveWin;
    
    private JCheckBox rawCheckBox;
    private JCheckBox checksumCheckBox;
    
    /* State saving information */
    private boolean saveRawOutput;
    private boolean saveChecksum;
    
    /**
     *  Constructor.
     *
     */
    public PrefsWindow (JhoveWindow owner) 
    {
        super (owner, "Jhove Preferences", true);
        addWindowListener (new PrefsWindowListener (this));
        jhoveWin = owner;
        JPanel mainPanel = new JPanel (new GridLayout (4, 1));    
        getContentPane ().add (mainPanel, BorderLayout.CENTER);
        rawCheckBox = new JCheckBox ("Raw data", false);
        mainPanel.add (rawCheckBox); 
        checksumCheckBox = new JCheckBox ("Calculate checksums", false);
        mainPanel.add (checksumCheckBox); 
        
        JPanel bottomPanel = new JPanel (new GridLayout (1, 3));
        getContentPane ().add (bottomPanel, BorderLayout.SOUTH);
        JButton okButton = new JButton ("OK");
        okButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    setPrefsFromDialog ();
                    hide ();
                }
            }
        );
        JButton cancelButton = new JButton ("Cancel");
        cancelButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    hide ();
                    restore ();
                }
            }
        );
        bottomPanel.add (new JLabel (""));
        bottomPanel.add (cancelButton);
        bottomPanel.add (okButton);
    }
    
    /**
     * This is called when the window is made visible.
     * (For efficiency, it is hidden rather than being
     * disposed when the user clicks OK or cancel.)  The
     * state of the dialog is saved, then it is made visible.
     * If the user clicks Cancel, the state of the dialog
     * will be restored.
     */
    public void saveAndShow ()
    {
        saveRawOutput = rawCheckBox.isSelected ();
        saveChecksum = checksumCheckBox.isSelected ();
        show ();
    }
    
    private void restore ()
    {
        rawCheckBox.setSelected (saveRawOutput);
        checksumCheckBox.setSelected (saveChecksum);
    }
    
    private void setPrefsFromDialog ()
    {
        jhoveWin.setRawOutput (rawCheckBox.isSelected ());
        jhoveWin.setDoChecksum(checksumCheckBox.isSelected ());
    }
    
    /********************************************************
     * WindowAdapter subclass for handling window closing
     ********************************************************/
    
    private class PrefsWindowListener extends WindowAdapter 
    {
        private PrefsWindow prefsWin;
        
        public PrefsWindowListener (PrefsWindow w) {
            prefsWin = w;
        }
        
        
        public void windowClosing (WindowEvent e) {
            prefsWin.restore ();
        }
    }
}
