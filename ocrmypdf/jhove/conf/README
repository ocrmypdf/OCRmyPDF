JHOVE - JSTOR/Harvard Object Validation Environment
Copyright 2003-2007 by JSTOR and the President and Fellows of Harvard College
JHOVE is made available under the GNU General Public License (see the file
LICENSE for details)

Rev. 2007-08-30

Edit the configuration file, jhove.conf, and set the JHOVE home
directory:

    <jhoveHome>jhove-home-directory</jhoveHome>

and temporary directory:

    <tempDirectory>temporary-directory</tempDirectory>

On most Unix systems, a reasonable temporary directory is "/var/tmp";
on Windows, "C:\temp".

The optional

    <bufferSize>buffer-size</bufferSize>

element defines the buffer size used for buffer I/O operations.

The optional

    <mixVersion>1.0</mixVersion>

element specifies that the XML output handler should conform to the
MIX 1.0 schema.  The default behavior is for handler output to conform
to the MIX 0.2 schema.

The optional

    <sigBytes>n</sigBytes>

element specifies that JHOVE modules will look for format signatures
in the first <n> bytes of the file.  The default value is 1024.

All class names must be fully qualified with their package name:

    <module>
      <class>fully-package-qualified-class-name</class>
      <init>optional-initialization-argument</init>
      <param>optional-invocation-argument</param>
    </module>

The optional <init> argument is passed to the module once at the time
its class is instantiated.  See module-specific documentation for a
description of any initialization options.

The optional <param> argument is passed to the module every time it is
invoked.  See module-specific documentation for a description of any
invocation options.

The order in which format modules are defined is important; when
performing a format identification operation, JHOVE will search for a
matching module in the order in which the modules are defined in the
configuration file. In general, the modules for more generic formats
should come later in the list. For example, the standard module ASCII
should be defined before the UTF-8 module, since all ASCII objects
are, by definition, UTF-8 objects, but not vice versa.
