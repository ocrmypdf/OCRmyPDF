#!/usr/bin/perl

########################################################################
# Jhove - JSTOR/Harvard Object Validation Environment
# Copyright 2004 by JSTOR and the President and Fellows of Harvard College
#
# A Perl script for plugging local path information into the
# various script files of JHOVE, as well as conf/jhove.conf.
#
# This is configured only for Unix (including OS X).
#
#    Usage: configure.pl jhove_home_directory [java_home_directory [java_runtime_directory]]
#
#    If invoked with no arguments, it will output a usage message.
#
########################################################################
use File::Copy;

sub mung {
    my $f = $_[0];
    my $bak = $f . "~";
    #If there is no backup file, copy the file to the
    #backup.  Otherwise work from the backup.
    if (!(-e $bak)) {
        rename ($f, $bak);
    }
    open (INFILE, $bak);
    open (OUTFILE, ">" . $f);

    #Walks through each line of file, making substitutions.
    #Remember that the JAVA_HOME and JAVA arguments are optional.
    while (<INFILE>) {
        s/^JHOVE_HOME=.*/JHOVE_HOME=$ARGV[0]/;
        if ($narg >= 2) {
            s/^JAVA_HOME=.*/JAVA_HOME=$ARGV[1]/;
        }
        if ($narg >= 3) {
            s/^JAVA=.*/JAVA=$ARGV[2]/;
        }
        print OUTFILE;
    }
    close (INFILE);
    close (OUTFILE);
    if (-e $f) {
        print ("Fixed " . $f . "\n");
    }
}


$narg = $#ARGV + 1;
if ($narg <= 0) {
    print "Usage: configure.pl jhove_home_directory [java_home_directory [java_runtime_directory]]\n";
    exit;
}
print "JHOVE_HOME will be set to " . $ARGV[0] . "\n";
if ($narg >= 2) {
    print "JAVA_HOME will be set to " . $ARGV[1] . "\n";
}
if ($narg >= 3) {
    print "JAVA will be set to " . $ARGV[2] . "\n";
}
mung ("jhove");
mung ("adump");
mung ("gdump");
mung ("jdump");
mung ("j2dump");
mung ("pdump");
mung ("tdump");
mung ("wdump");

#Fix up the config file.  We assume that the <jhoveHome>
#element is all on one line.
if (!(-e "conf/jhove.conf~")) {
    rename ("conf/jhove.conf", "conf/jhove.conf~");
}
open (INFILE, "conf/jhove.conf~");
open (OUTFILE, ">conf/jhove.conf");
while (<INFILE>) {
    s!<jhoveHome>.*</jhoveHome>!<jhoveHome>$ARGV[0]</jhoveHome>!;
    print OUTFILE;
}
close (INFILE);
close (OUTFILE);
if (-e "conf/jhove.conf") {
    print "Fixed conf/jhove.conf\n";
}
exit;

