@ECHO OFF
REM pdump - JSTOR/Harvard Object Validation Environment
REM Copyright 2003-2005 by JSTOR and the President and Fellows of Harvard College
REM JHOVE is made available under the GNU General Public License (see the
REM file LICENSE for details)
REM
REM Driver script for the PDF dump utility
REM
REM Usage: pdump file
REM
REM where file is a PDF file
REM
REM Configuration constants:
REM JHOVE_HOME Jhove installation directory
REM JAVA_HOME  Java JRE directory
REM JAVA       Java interpreter
REM EXTRA_JARS Extra jar files to add to CLASSPATH

SET JHOVE_HOME="C:\Program Files\jhove"

SET JAVA_HOME="C:\Program Files\java\j2re1.4.1_02"
SET JAVA=%JAVA_HOME%\bin\java

SET EXTRA_JARS=

REM NOTE: Nothing below this line should be edited
REM #########################################################################


SET CP=%JHOVE_HOME%\bin\JhoveApp.jar
IF "%EXTRA_JARS%"=="" GOTO FI
  SET CP=%CP%:%EXTRA_JARS
:FI

REM Retrieve a copy of all command line arguments to pass to the application

SET ARGS=
:WHILE
IF "%1"=="" GOTO LOOP
  SET ARGS=%ARGS% %1
  SHIFT
  GOTO WHILE
:LOOP

REM Set the CLASSPATH and invoke the Java loader
%JAVA% -classpath %CP% PDump %ARGS%
