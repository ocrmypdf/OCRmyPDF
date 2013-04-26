/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;


/**
 *  This class defines enumerated types for an Agent. 
 *  Applications will not create or modify AgentTypes, but will
 *  use one of the predefined AgentType instances COMMERCIAL, GOVERNMENT,
 *  EDUCATIONAL, NONPROFIT, STANDARD, or OTHER.
 *
 *  @see Agent
 */
public final class AgentType
    extends EnumerationType
{
    /******************************************************************
     * PUBLIC STATIC INSTANCES.
     ******************************************************************/

    /**
     *  Agent type for a commercial entity.
     */
    public static final AgentType COMMERCIAL = new AgentType ("Commercial");
    /**
     *  Agent type for a governmental body.
     */
    public static final AgentType GOVERNMENT = new AgentType ("Government");
    /**
     *  Agent type for an educational institution.
     */
    public static final AgentType EDUCATIONAL = new AgentType ("Educational");
    /**
     *  Agent type for a non-profit organization.
     */
    public static final AgentType NONPROFIT = new AgentType ("Non-profit");
    /**
     *  Agent type for a standards body.
     */
    public static final AgentType STANDARD = new AgentType ("Standards body");
    /**
     *  Agent type that doesn't fit the other categories.
     */
    public static final AgentType OTHER = new AgentType ("Other");

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Applications will never create AgentTypes directly.
     **/
    private AgentType (String value)
    {
	super (value);
    }
}
