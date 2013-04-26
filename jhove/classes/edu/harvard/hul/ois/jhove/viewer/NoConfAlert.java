/**********************************************************************
 * JhoveView - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;

/**
 *  This class implements an alert which is posted when no 
 *  configuration file can be found. 
 */
public class NoConfAlert extends JDialog
{
    public NoConfAlert (JFrame owner)
    {
        super (owner, "Fatal Error", true);

	// Create a panel with an informative message.
        JPanel mainPanel = new JPanel ();
        getContentPane ().add (mainPanel, "Center");
	String infoString = new String ("Jhove could not find " +
	 "a configuration file.  You must have one of the " +
         "following in jhove/conf under your home directory:\n\n" +
	 "(1) A properties file called jhove.properties " +
	 "with a property named edu.harvard.hul.ois.jhove.config " +
	 "having the path to your configuration file as its " +
	 "value; or\n\n" +
	 "(2) A configuration file named jhove.conf\n\n " +
         "Note: Under Windows, your home directory is the directory " +
         "with your username under Documents and Settings.\n");

	JTextArea infoArea = new JTextArea (infoString);
	infoArea.setLineWrap (true);
	infoArea.setWrapStyleWord (true);
	Dimension prefSize = new Dimension (250, 300);
	infoArea.setMinimumSize (prefSize);
	infoArea.setPreferredSize (prefSize);
	mainPanel.add (infoArea);
        
	// Create a panel with a button for quitting.
        JPanel bottomPanel = new JPanel ();
        getContentPane ().add (bottomPanel, "South");
	JButton exitButton = new JButton ("Quit");
	bottomPanel.add (exitButton);
        exitButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    dispose ();
                }
            }
        );
	pack ();
    }
}
