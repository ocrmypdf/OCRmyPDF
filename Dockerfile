# OCRmyPDF
#
# VERSION               3.0.0
FROM      debian:stretch
MAINTAINER James R. Barlow <jim@purplerock.ca>

# Add unprivileged user
RUN useradd docker \
  && mkdir /home/docker \
  && chown docker:docker /home/docker

# Update system and install our dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  locales \
  ghostscript \
  tesseract-ocr \
  tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-eng tesseract-ocr-fra \
  qpdf \
  poppler-utils \
  python3 \
  python3-pip \
  python3-venv \
  python3-reportlab \
  python3-pil

# Enforce UTF-8
# Borrowed from https://index.docker.io/u/crosbymichael/python/ 
RUN dpkg-reconfigure locales && \
  locale-gen C.UTF-8 && \
  /usr/sbin/update-locale LANG=C.UTF-8
ENV LC_ALL C.UTF-8

# Build unpaper 6.1
RUN apt-get install -y \
  wget \
  gcc \
  libavformat-dev \
  libavcodec-dev \
  libavutil-dev \
  autoconf \
  automake \
  make \
  pkg-config \
  xsltproc

WORKDIR /root
RUN wget https://github.com/Flameeyes/unpaper/archive/unpaper-6.1.tar.gz
RUN tar xf unpaper-6.1.tar.gz
WORKDIR /root/unpaper-unpaper-6.1
RUN autoreconf -i
RUN ./configure CFLAGS="-O2 -march=native -pipe -flto"
RUN make -j install

RUN apt-get remove -y \
  gcc \
  autoconf \
  automake \
  pkg-config \
  xsltproc \
  make
RUN apt-get autoremove -y && apt-get clean -y
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set up a Python virtualenv and take all of the system packages, so we can
# rely on the platform packages rather than importing GCC and compiling them
RUN pyvenv /appenv \
  && pyvenv --system-site-packages /appenv

COPY . /application/

# Install application and dependencies
# In this arrangement Pillow and reportlab will be provided by the system
RUN . /appenv/bin/activate; \
  pip install --upgrade pip \
  && pip install --no-cache-dir /application \
  && pip install --no-cache-dir -r /application/test_requirements.txt

USER docker
WORKDIR /home/docker

ENV DEFAULT_RUFFUS_HISTORY_FILE=/tmp/.{basename}.ruffus_history.sqlite
ENV OCRMYPDF_TEST_OUTPUT=/tmp/test-output
ENV OCRMYPDF_IN_DOCKER=1

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/docker-wrapper.sh"]