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
  wget \
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
  python3-pytest \
  python3-dev \
  gcc


# Ubuntu 14.04's ensurepip is broken, so it cannot create py3 virtual envs
# Use elaborate workaround: create a venv without pip, activate that environment,
# download a script to install pip into the environment
# http://www.thefourtheye.in/2014/12/Python-venv-problem-with-ensurepip-in-Ubuntu.html

RUN python3 -m venv appenv --without-pip
RUN . /appenv/bin/activate; \
  wget -O - -o /dev/null https://bootstrap.pypa.io/get-pip.py | python

COPY ./*requirements.txt /application/

# Build wheels separately so build is cached by Docker
RUN . /appenv/bin/activate; \
  pip install wheel \
  && pip wheel --wheel-dir=/wheelhouse -r /application/requirements.txt \
  && pip wheel --wheel-dir=/wheelhouse -r /application/test_requirements.txt

COPY . /application/

# Install application using our built wheels
RUN . /appenv/bin/activate; \
  pip install --no-index --find-links=/wheelhouse /application \
  && pip install --no-index --find-links=/wheelhouse -r /application/test_requirements.txt

USER docker
WORKDIR /home/docker

ENV DEFAULT_RUFFUS_HISTORY_FILE=/tmp/.{basename}.ruffus_history.sqlite

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/docker-wrapper.sh"]