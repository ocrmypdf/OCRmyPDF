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

# Ubuntu 14.04's ensurepip is broken, so it cannot create py3 virtual envs
# Use elaborate workaround: create a venv without pip, activate that environment,
# download a script to install pip into the environment
# http://www.thefourtheye.in/2014/12/Python-venv-problem-with-ensurepip-in-Ubuntu.html

RUN python3 -m venv appenv --without-pip
RUN . /appenv/bin/activate; \
  wget -O - -o /dev/null https://bootstrap.pypa.io/get-pip.py | python

RUN apt-get install -y gcc python3-dev

COPY . /application/

RUN . /appenv/bin/activate; \
  pip install /application/.

USER docker
WORKDIR /home/docker

ENV DEFAULT_RUFFUS_HISTORY_FILE=/tmp/.{basename}.ruffus_history.sqlite

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/docker-wrapper.sh"]