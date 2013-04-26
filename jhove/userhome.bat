@ECHO OFF
REM userhome - JSTOR/Harvard Object Validation Environment
REM Copyright 2004-2006 by the President and Fellows of Harvard College
REM JHOVE is made available under the GNU General Public License (see the
REM file LICENSE for details)
REM
REM Driver script to display the default Java user.home property
REM
REM Usage: userhome
REM
REM Configuration constants:
REM JHOVE_HOME Jhove installation directory
REM JAVA_HOME  Java JRE directory
REM JAVA       Java interpreter
REM EXTRA_JARS Extra jar files to add to CLASSPATH

SET JHOVE_HOME="C:\Program Files\jhove"

SET JAVA_HOME="C:\Program Files\java\j2re1.4.2_07"
SET JAVA=%JAVA_HOME%\bin\java

REM NOTE: Nothing below this line should be edited
REM #########################################################################

REM Set the CLASSPATH and invoke the Java loader
%JAVA% -classpath %JHOVE_HOME%\classes UserHome
