#!/bin/sh
#DO NOT RUN THIS ON A DEVELOPEMENT DIRECTORY, ONLY ON A 
#CHECKED-OUT COPY TO BE PACKAGED!

if [ "$1" = "" ]; then
 echo "Usage: packagejhove.sh [version]"
 echo "e.g., packagejhove.sh 1_8"
 exit 1
fi

echo "This script will prepare your directory for uploading."
echo "DO NOT RUN IT unless you're a developer and know what"
echo "you are doing. "

echo "Start in the top-level directory of the JHOVE checkout."
echo "Run ant and ant javadoc and do any necessary testing and"
echo "committing before running this script."
echo 
echo

echo "To continue, enter the secret phrase."
read OATH
if [ "$OATH" != "I solemnly swear that I am up to no good" ]; then
 exit 1
fi

cd ..
cat >>CVSS << EOF
CVS
.cvsignore
EOF
tar cvfX jhove-$1.tar CVSS jhove
gzip jhove-$1.tar
cp -r jhove jhove-zip
cd jhove-zip
find . \( -name CVS -o -name .cvsignore \) -exec rm -r {} \;	
cd ..
mv jhove jhove-ok
mv jhove-zip jhove
zip -r jhove-$1.zip jhove
rm -r jhove
mv jhove-ok jhove
jhove/md5.pl jhove-$1.tar.gz >jhove-$1.tar.gz.md5
jhove/md5.pl jhove-$1.zip >jhove-$1.zip.md5 