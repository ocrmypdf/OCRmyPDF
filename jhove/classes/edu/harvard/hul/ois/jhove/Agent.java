/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  Encapsulates information about agents, either individual 
 *  persons or corporate bodies.
 */
public class Agent
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    private String _name;
    private AgentType _type;
    private String _address;
    private String _telephone;
    private String _fax;
    private String _email;
    private String _web;
    private String _note;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates an Agent given a name and an AgentType.
     */
    public Agent (String name, AgentType type)
    {
	_name = name;
	_type = type;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Returns the value of the address property.
     */
    public String getAddress ()
    {
	return _address;
    }

    /**
     *  Returns the value of the email property.
     */
    public String getEmail ()
    {
	return _email;
    }

    /**
     *  Returns the value of the fax property.
     */
    public String getFax ()
    {
	return _fax;
    }

    /**
     *  Returns the value of the name property.
     */
    public String getName ()
    {
	return _name;
    }

    /**
     *  Returns the value of the note property.
     */
    public String getNote ()
    {
	return _note;
    }

    /**
     *  Returns the value of the telephone property.
     */
    public String getTelephone ()
    {
	return _telephone;
    }

    /**
     *  Returns the value of the type property.
     */
    public AgentType getType ()
    {
	return _type;
    }

    /**
     *  Returns the value of the web property.
     */
    public String getWeb ()
    {
	return _web;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /**
     *  Sets the value of the address property.
     */
    public void setAddress (String address)
    {
	_address = address;
    }

    /**
     *  Sets the value of the email property.
     */
    public void setEmail (String email)
    {
	_email = email;
    }

    /**
     *  Sets the value of the fax property.
     */
    public void setFax (String fax)
    {
	_fax = fax;
    }

    /**
     *  Sets the value of the name property.
     */
    public void setName (String name)
    {
	_name = name;
    }

    /**
     *  Sets the value of the note property.
     */
    public void setNote (String note)
    {
	_note = note;
    }

    /**
     *  Sets the value of the telephone property.
     */
    public void setTelephone (String telephone)
    {
	_telephone = telephone;
    }

    /**
     *  Sets the value of the web property.
     */
    public void setWeb (String web)
    {
	_web = web;
    }
}
