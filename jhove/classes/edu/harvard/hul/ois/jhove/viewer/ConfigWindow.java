/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.text.ParseException;
import javax.swing.*;
import javax.swing.table.*;
//import javax.swing.border.*;
import edu.harvard.hul.ois.jhove.ConfigHandler;
import edu.harvard.hul.ois.jhove.ConfigWriter;
import edu.harvard.hul.ois.jhove.ModuleInfo;

/**
 * Window for high-level editing of the application's
 * configuration file.
 * 
 * @author Gary McGath
 *
 */
public class ConfigWindow extends JDialog {

    private final static String tempDirDefault = "<Default>";
    
    /* The location of the config file. */
    private File _configFile;
    
    /* List of modules.  An entry in the list is an
     * array of 2 Strings, which are the fully qualified
     * class and the init string respectively. */
    private List<ModuleInfo> _modules;
    
    /* List of handlers.  This is just a list of Strings
     * giving the class. */
    private List<String[]> _handlers;
        
    private int _bufferSize;
    
    private File _homeDir;
    private File _tempDir;
    private String _encoding;
    
    /* Display components. */
    
    private Box _mainBox;
    
    private JTable _modTable;
    private JTable _hanTable;
    private AbstractTableModel _modTableModel;
    private AbstractTableModel _hanTableModel;
    private JLabel _homeLabel;
    private JLabel _tempDirLabel;
    private NumericField _bufSizeBox;
    private JTextField _encodingBox;
    
    final static Color _tableColor = new Color (235, 230, 210);
    final static Font _pathFont = new Font ("SansSerif", Font.PLAIN, 10);
    final static Font _infoFont = new Font ("SansSerif", Font.PLAIN, 12);
    
    /**
     *  Constructor.
     * 
     *  @param configFile  The file which was opened for
     *                     configuration information, or null
     *                     to start with a clean slate.
     * 
     *  @param handler    A ConfigHandler which has already
     *                    processed the configuration file,
     *                    or null if configFile is null.
     */
    public ConfigWindow (JFrame parent, File configFile, ConfigHandler handler)
    {
        super (parent, "Jhove Configuration", true);
        setDefaultCloseOperation (WindowConstants.DISPOSE_ON_CLOSE);
        _configFile = configFile;
        if (handler != null) {
            _modules = handler.getModule ();
            _handlers = handler.getHandler ();
            _bufferSize = handler.getBufferSize ();
            String dir = handler.getJhoveHome();
            if (dir != null) {
                _homeDir = new File (dir);
            }
            dir = handler.getTempDir();
            if (dir != null) {
                _tempDir = new File (dir);
            }
            _encoding = handler.getEncoding ();
        }
        else {
            // Set up defaults
            _modules = new ArrayList<ModuleInfo> (10);
            _handlers = new ArrayList<String[]> (5);
            _bufferSize = -1;
            _homeDir = null;
            _tempDir = null;
            _encoding = null;
        }
        
        // Set up a Box container for the window top level
        _mainBox = Box.createVerticalBox ();
        getContentPane().setLayout (new BorderLayout ());
        getContentPane().add (_mainBox, "Center");
        _mainBox.setBorder (BorderFactory.createLineBorder(Color.BLACK));
        
        // Keep its size reasonable, taking screen size into account
        java.awt.Rectangle screenRect = MainScreen.mainBounds ();
        int maxHeight = screenRect.height - 200;
        if (maxHeight > 640) {
            maxHeight = 640;
        }
        _mainBox.setMaximumSize (new Dimension (500, maxHeight));
        _mainBox.setPreferredSize (new Dimension (400, maxHeight));
        
        addModuleTable ();
        _mainBox.add(Box.createRigidArea(new Dimension(0, 6)));
        addHandlerTable ();
        addHomeDir ();
        addTempDir ();
        addEncoding ();
        addBufferSize ();
        addSaveCancel ();
        pack ();
    }
    

    
    /*  Create a JTable of two columns which lets the
     *  user add and delete modules, and add it to
     *  the window.
     *  Called by the constructor. 
     */
    private void addModuleTable ()
    {
        JPanel panel = new JPanel ();
        panel.setLayout (new BorderLayout ());
        _mainBox.add (panel);
        // Use an anonymous class to implement the TableModel
        _modTableModel = new AbstractTableModel () {
            public int getRowCount () 
            {
                return _modules.size ();
            }
            public int getColumnCount ()
            {
                return 2;
            }
            public boolean isCellEditable(int row, int col)
            { 
                return true;
            }
            public Object getValueAt (int row, int column)
            {
                ModuleInfo modInfo  = _modules.get (row);
                String[] tuple = { modInfo.clas, modInfo.init};
                return tuple[column];
            }
            public void setValueAt (Object obj, int row, int column)
            {
                ModuleInfo modInfo = _modules.get(row);
                if (column == 0 && obj instanceof String) {
                    modInfo.clas = (String) obj;
                }
                if (column == 1 && obj instanceof String) {
                    modInfo.init = (String) obj;
                }
            }
        };
        
        _modTable = new JTable (_modTableModel);
//        _modTable.setMaximumSize(new Dimension (250, 150));
        _modTable.setSelectionMode (ListSelectionModel.SINGLE_SELECTION);
        _modTable.setCellSelectionEnabled (true);
        _modTable.setBackground (_tableColor);
        JScrollPane modScrollPane = new JScrollPane (_modTable);

        TableColumnModel colMod = _modTable.getColumnModel();
        colMod.getColumn(0).setHeaderValue("Class");
        colMod.getColumn(1).setHeaderValue("Init");
        _modTable.doLayout ();
        // Add a panel with the modules caption and a couple of buttons.
        JPanel topPanel = new JPanel ();
        topPanel.setLayout (new BorderLayout ());
        topPanel.add (new JLabel ("Modules:"), "West");
        
        // Squeeze the buttons over to the right
        JPanel rightPanel = new JPanel ();
        topPanel.add (rightPanel, "East");
        JButton addButton = new JButton ("Add");
        addButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    addModule ();
                }
            }
        );
        rightPanel.add (addButton);
        JButton delButton = new JButton ("Delete");
        delButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    deleteModule ();
                }
            }
        );
        
        // Make both buttons the same size
        addButton.setMinimumSize (delButton.getMinimumSize ());
        addButton.setPreferredSize (delButton.getPreferredSize ());

        rightPanel.add (delButton);
        panel.add (topPanel, "North");
        panel.add (modScrollPane, "Center");  
    }



    /*  Create a JTable of one column which lets the
     *  user add and delete handlers, and add it to
     *  the window.
     *  Called by the constructor. 
     */
    private void addHandlerTable ()
    {
        JPanel panel = new JPanel ();
        panel.setLayout (new BorderLayout ());
        _mainBox.add (panel);
        // Use an anonymous class to implement the TableModel
        _hanTableModel = new AbstractTableModel () {
            public int getRowCount () 
            {
                return _handlers.size ();
            }
            public int getColumnCount ()
            {
                return 1;
            }
            public boolean isCellEditable(int row, int col)
            { 
                return true;
            }
            public Object getValueAt (int row, int column)
            {
                String[] tuple = (String[]) _handlers.get (row);
                if (tuple != null) {
                    return tuple[0];
                }
                else {
                    return "";
                }
            }
            public void setValueAt (Object obj, int row, int column)
            {
                if (obj instanceof String) {
                    String[] stuff = new String[] { (String) obj };
                    _handlers.set (row, stuff);
                }
            }
        };
        
        _hanTable = new JTable (_hanTableModel);
        _hanTable.setSelectionMode (ListSelectionModel.SINGLE_SELECTION);
        _hanTable.setCellSelectionEnabled (true);
        _hanTable.setBackground (_tableColor);
        JScrollPane hanScrollPane = new JScrollPane (_hanTable);

        TableColumnModel colMod = _hanTable.getColumnModel();
        colMod.getColumn(0).setHeaderValue("Class");
        _hanTable.doLayout ();
        // Add a panel with the modules caption and a couple of buttons.
        JPanel topPanel = new JPanel ();
        topPanel.setLayout (new BorderLayout ());
        topPanel.add (new JLabel ("Handlers:"), "West");
        
        // Squeeze the buttons over to the right
        JPanel rightPanel = new JPanel ();
        topPanel.add (rightPanel, "East");
        JButton addButton = new JButton ("Add");
        addButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    addHandler ();
                }
            }
        );
        rightPanel.add (addButton);
        JButton delButton = new JButton ("Delete");
        delButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    deleteHandler ();
                }
            }
        );

        // Make both buttons the same size
        addButton.setMinimumSize (delButton.getMinimumSize ());
        addButton.setPreferredSize (delButton.getPreferredSize ());

        rightPanel.add (delButton);
        panel.add (topPanel, "North");
        panel.add (hanScrollPane, "Center");  
    }
    



    /*  Add a label and text edit box for the encoding */
    private void addEncoding ()
    {
        JPanel panel = new JPanel ();
        _mainBox.add (panel);
        panel.add (new JLabel ("Default encoding: "));
        _encodingBox = new JTextField (_encoding == null ? "" : _encoding, 14);
        panel.add (_encodingBox);
    }
    
    
    
    /*  Add a label and text edit box for the buffer size */
    private void addBufferSize ()
    {
        JPanel panel = new JPanel ();
        _mainBox.add (panel);
        panel.add (new JLabel ("Buffer size (-1 for default): "));
        _bufSizeBox = new NumericField (_bufferSize);
        panel.add (_bufSizeBox);
    }
    
    /*  Add a button and file path string for home directory.
     *  A home directory is required, but there may not be one
     *  initially. 
     *  Called by the constructor. */
    private void addHomeDir ()
    {
        JPanel panel = new JPanel ();
        _mainBox.add (panel);
        panel.setLayout (new GridLayout (1, 2));
        JButton homeButton = new JButton ("Home directory...");
        String homeText = "<none specified>";
        if (_homeDir != null) {
            homeText = _homeDir.getPath();
        }
        _homeLabel = new JLabel(homeText);
        _homeLabel.setFont (_pathFont);
        // Standard trick for not making button take up all available space
        JPanel bpan = new JPanel ();
        //panel.add (bpan);
        panel.add (bpan);
        bpan.add (homeButton);
        homeButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    chooseHomeDir ();
                }
            }
        );
        panel.add (_homeLabel);
        // Both of these probably need to be class variables
    }


    /*  Add a button and file path string for temporary directory.
     *  Called by the constructor. */
    private void addTempDir ()
    {
        JPanel panel = new JPanel ();
        _mainBox.add (panel);
        panel.setLayout (new GridLayout (1, 2));
        JButton tempDirButton = new JButton ("Temp directory...");
        String tempDirText = tempDirDefault;
        if (_tempDir != null) {
            tempDirText = _tempDir.getPath();
        }
        _tempDirLabel = new JLabel(tempDirText);
        _tempDirLabel.setFont (_pathFont);
        // Standard trick for not making button take up all available space
        JPanel bpan = new JPanel ();
        panel.add (bpan);
        bpan.add (tempDirButton);
        tempDirButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    chooseTempDir ();
                }
            }
        );
        panel.add (_tempDirLabel);
    }
    

    /* Add OK and cancel buttons, and a little information */
    private void addSaveCancel ()
    {
        final ConfigWindow thiscw = this;
        JPanel buttonPanel = new JPanel ();
        getContentPane().add (buttonPanel, "South");
        buttonPanel.setLayout (new BorderLayout ());
        JLabel changesLabel = new JLabel 
                    ("Changes take effect on relaunch");
        changesLabel.setFont (_infoFont);
        buttonPanel.add (changesLabel, "North");
        
        JPanel panel = new JPanel ();
        buttonPanel.add (panel, "Center");
        panel.setLayout (new GridLayout (1, 3));
        
        // Blank panel for positioning
        JPanel bpan = new JPanel ();
        panel.add (bpan);
        
        // Add OK button
        bpan = new JPanel ();
        JButton saveButton = new JButton ("OK");
        getRootPane().setDefaultButton (saveButton);
        saveButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    doSave ();
                }
            }
        );
        bpan.add (saveButton);
        panel.add (bpan);

        // Add cancel button
        bpan = new JPanel ();
        JButton cancelButton = new JButton ("Cancel");
        cancelButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    thiscw.dispose ();
                }
            }
        );
        
        // Make both buttons the same size
        saveButton.setMinimumSize (cancelButton.getMinimumSize ());
        saveButton.setPreferredSize (cancelButton.getPreferredSize ());
        bpan.add (cancelButton);
        panel.add (bpan);
        
    }


    /* Carry out the action of the "Save" button. */
    private void doSave ()
    {
        // Splitting off the output to a ConfigFileWriter class
        // makes sense.
        try {
            // Update values from the editing components
            try {
                _bufSizeBox.commitEdit ();
            }
            catch (ParseException e) {
                return;  // refuse to save if value is invalid
            }
            //Object bufSizeValue = _bufSizeBox.getValue ();
            _bufferSize = ((Long) _bufSizeBox.getValue ()).intValue ();
            
            _encoding = _encodingBox.getText ();
            
            // *** Writes to temp file for debugging
            //ConfigWriter cw = new ConfigWriter (new File (_homeDir, "temp"));
            ConfigWriter cw = new ConfigWriter (_configFile, this);
            cw.writeFile (_modules, _handlers,
                _homeDir, _tempDir, _encoding, _bufferSize);
        }
        catch (IOException e) {
            JOptionPane.showMessageDialog(this, 
                    e.getMessage (), 
                    "Can't create config", 
                    JOptionPane.ERROR_MESSAGE);
        }
        
        // Close the window
        dispose ();
    }
   
    /* Choose the home directory.  Since there must be one,
     * there is no "default" button. */
    private void chooseHomeDir ()
    {
        JFileChooser chooser = new JFileChooser ();
        if (_homeDir != null) {
            chooser.setCurrentDirectory (_homeDir);
        }
        chooser.setDialogTitle ("Select Home Directory");
        chooser.setFileSelectionMode (JFileChooser.DIRECTORIES_ONLY);
        if (chooser.showOpenDialog (this) == JFileChooser.APPROVE_OPTION) {
            _homeDir = chooser.getSelectedFile();
            _homeLabel.setText (_homeDir.getPath ());
        }
    }


    /* Choose the temp directory.  Allow a "default" selection. */
    private void chooseTempDir ()
    {
        final JFileChooser chooser = new JFileChooser ();
        if (_homeDir != null) {
            chooser.setCurrentDirectory (_tempDir);
        }
        chooser.setDialogTitle ("Select Temporary Directory");
        // Create a custom panel so we can add the Default button.
        JPanel accessory = new JPanel ();
        accessory.setPreferredSize(new Dimension (160, 40));
        JButton defaultButton = new JButton ("System Default");
        defaultButton.addActionListener (
            new ActionListener () {
                public void actionPerformed (ActionEvent e) 
                {
                    // Exit the dialog and clear _tempDir
                    _tempDir = null;
                    _tempDirLabel.setText (tempDirDefault);
                    chooser.cancelSelection ();
                }
            }
        );
        accessory.add (defaultButton);
        chooser.setAccessory (accessory);
        
        chooser.setFileSelectionMode (JFileChooser.DIRECTORIES_ONLY);
        if (chooser.showOpenDialog (this) == JFileChooser.APPROVE_OPTION) {
            _tempDir = chooser.getSelectedFile();
            _tempDirLabel.setText (_tempDir.getPath ());
        }
    }
    
    /* Add a blank item for a new module */
    private void addModule ()
    {
        ListSelectionModel ls = _modTable.getSelectionModel ();
        int selRow = ls.getMinSelectionIndex();
        // If there's no selection, append to the end
        if (selRow < 0) {
            selRow = _modules.size ();
        }
//        String[] tuple = new String[2];
//        tuple[0] = "";        // class
//        tuple[1] = null;      // init
        ModuleInfo modInfo = new ModuleInfo ("", null);
        _modules.add (selRow, modInfo);
        _modTableModel.fireTableRowsInserted(selRow, selRow);
    }


  
    /* Delete the selected module line */
    private void deleteModule ()
    {
        ListSelectionModel ls = _modTable.getSelectionModel ();
        int selRow = ls.getMinSelectionIndex();
        if (selRow < 0) {
            return;       // no selection
        }
        _modules.remove (selRow);
        _modTableModel.fireTableRowsDeleted (selRow, selRow);
    }
    
    
    /* Add a blank item for a new handler */
    private void addHandler ()
    {
        ListSelectionModel ls = _hanTable.getSelectionModel ();
        int selRow = ls.getMinSelectionIndex();
        // If there's no selection, append to the end
        if (selRow < 0) {
            selRow = _handlers.size ();
        }
        String[] tuple = { "" };
        _handlers.add (selRow, tuple);
        _hanTableModel.fireTableRowsInserted(selRow, selRow);
    }


  
    /* Delete the selected handler line */
    private void deleteHandler ()
    {
        ListSelectionModel ls = _hanTable.getSelectionModel ();
        int selRow = ls.getMinSelectionIndex();
        if (selRow < 0) {
            return;       // no selection
        }
        _handlers.remove (selRow);
        _hanTableModel.fireTableRowsDeleted (selRow, selRow);
    }


    
    /* When the user chooses to close and save, or just save,
     * we come here.
     * 
     * @param configFile   The location to save the file, or none
     *                     if a simple "save" was selected.  If
     *                     configFile is non-null, it becomes the
     *                     new default location.
     */
//    private void saveConfig (File configFile)
//    {
//        if (configFile != null) {
//            _configFile = configFile;
//        }
//        
//        // _configFile may be null.  In that case we must put up
//        // a dialog to select the config file here, and exit the function
//        // if the user cancels.
//        try {
//            FileOutputStream ostrm = new FileOutputStream (configFile);
//        }
//        catch (IOException e) {
//                JOptionPane.showMessageDialog (this,
//                    e.getMessage(), "Error saving config", 
//                    JOptionPane.ERROR_MESSAGE); 
//
//        }
//    }
    
//    private File doConfigFileDialog ()
//    {
//        JFileChooser chooser = new JFileChooser ();
//        chooser.setFileSelectionMode (JFileChooser.DIRECTORIES_ONLY);
//        if (chooser.showOpenDialog (this) == JFileChooser.APPROVE_OPTION) {
//            return chooser.getSelectedFile();
//        }
//        
//        return null;   // placeholder
//    }
}
