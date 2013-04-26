/**********************************************************************
 * UserHome - JSTOR/Harvard Object Validation Environment
 * Copyright 2006 by the President and Fellows of Harvard College
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 **********************************************************************/

import java.io.*;

/**
 * Determine the default value of the Java user.home property.
 */
public class UserHome
{
    public static void main (String [] args)
    {
	System.out.println ("Default user.home is \"" +
			    System.getProperty ("user.home") + "\"");
    }
}
