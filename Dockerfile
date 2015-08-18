# OCRmyPDF
#
# VERSION               3.0.0
FROM      ubuntu:14.04
MAINTAINER James R. Barlow <jim@purplerock.ca>

# Add unprivileged user
RUN useradd docker \
  && mkdir /home/docker \
  && chown docker:docker /home/docker

# Update system
RUN apt-get update && apt-get install -y --no-install-recommends \
  bc \
  curl \
  zlib1g-dev \
  libjpeg-dev \
  ghostscript \
  tesseract-ocr \
  tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-eng tesseract-ocr-fra \
  qpdf \
  unpaper \
  poppler-utils \
  python3 \
  python3-pip \
  python3-pil \
  python3-pytest \
  python3-reportlab


RUN apt-get install -y wget

# Ubuntu 14.04's ensurepip is broken
# http://www.thefourtheye.in/2014/12/Python-venv-problem-with-ensurepip-in-Ubuntu.html

RUN python3 -m venv . --without-pip
RUN /bin/bash -c "source ./bin/activate \
  && wget -O - -o /dev/null https://bootstrap.pypa.io/get-pip.py | python \
  && deactivate"

USER docker
WORKDIR /home/docker

