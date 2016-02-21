# OCRmyPDF
#
# VERSION               3.2
FROM      debian:stretch
MAINTAINER James R. Barlow <jim@purplerock.ca>

# Add unprivileged user
RUN useradd docker \
  && mkdir /home/docker \
  && chown docker:docker /home/docker

# Update system and install our dependencies
# If this command takes too Docker hub's automated build will timeout,
# so try it in portions
RUN apt-get update && apt-get install -y --no-install-recommends \
  locales \
  python3 \
  python3-pip \
  python3-venv \
  python3-reportlab \
  python3-pil \
  python3-wheel

RUN apt-get install -y --no-install-recommends \
  unpaper \
  qpdf \
  poppler-utils \
  tesseract-ocr \
  tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-eng tesseract-ocr-fra

RUN apt-get install -qy --no-install-recommends \
  libffi-dev \
  libpython3-dev \
  gcc

# Install Ghostscript from Debian sid to work around JPEG 2000 issue in
# Debian stretch libgs9 or gs 9.16~dfsg-2.1

COPY ./share/etc-apt-sources.list /etc/apt/sources.list

RUN apt-get update && apt-get install -y ghostscript/sid


# Enforce UTF-8
# Borrowed from https://index.docker.io/u/crosbymichael/python/ 
RUN dpkg-reconfigure locales && \
  locale-gen C.UTF-8 && \
  /usr/sbin/update-locale LANG=C.UTF-8
ENV LC_ALL C.UTF-8


# Set up a Python virtualenv and take all of the system packages, so we can
# rely on the platform packages rather than importing GCC and compiling them
RUN pyvenv /appenv \
  && pyvenv --system-site-packages /appenv

COPY . /application/

# Replace stock Tesseract 3.04.00 font with improved sharp2.ttf that resolves
# issues in many PDF viewers.
# Discussion is in https://github.com/tesseract-ocr/tesseract/issues/182
COPY ./share/sharp2.ttf /usr/share/tesseract-ocr/tessdata/pdf.ttf
RUN chmod 644 /usr/share/tesseract-ocr/tessdata/pdf.ttf

# Set this here to force a docker version, allowing non-tagged versions to
# be built
# ENV SETUPTOOLS_SCM_PRETEND_VERSION=v3.3.0

# Install application and dependencies
# In this arrangement Pillow and reportlab will be provided by the system
# Even though ocrmypdf is locally present, pull from PyPI because
# Dockerhub and setuptools_scm clash
RUN . /appenv/bin/activate; \
  pip install --upgrade pip \
  && pip install ocrmypdf \
  && pip install --no-cache-dir -r /application/test_requirements.txt

# Remove the junk
RUN apt-get remove -qy gcc
RUN apt-get autoremove -y && apt-get clean -y
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/*

USER docker
WORKDIR /home/docker

ENV OCRMYPDF_TEST_OUTPUT=/tmp/test-output
ENV OCRMYPDF_SHARP_TTF=1

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/docker-wrapper.sh"]