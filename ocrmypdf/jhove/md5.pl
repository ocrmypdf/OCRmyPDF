#!/usr/bin/perl -w

# Generate MD5 checksum

use Digest::MD5;

die "usage: md5.pl file\n" if $#ARGV < 0;

open (FILE, "<$ARGV[0]") or die "can't open file\"$ARGV[0]\"!\n";
$ctx = Digest::MD5->new->addfile (*FILE);
close (FILE);
$digest = $ctx->hexdigest;

print "$digest\n";
