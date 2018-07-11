# OCRmyPDF
#
FROM      ubuntu:18.04

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential autoconf automake libtool \
  leptonica \
  libexempi3 \
  ocrmypdf \
  pngquant \
  python3-pip \
  python3-venv \
  tesseract-ocr \
  tesseract-ocr-chi-sim \
  tesseract-ocr-deu \
  tesseract-ocr-eng \
  tesseract-ocr-fra \
  tesseract-ocr-por \
  tesseract-ocr-spa \
  unpaper \
  wget

ENV LANG=C.UTF-8

# Compile and install jbig2
RUN wget -q https://github.com/agl/jbig2enc/archive/0.29.tar.gz -O - | \
      tar xz -C jbig2 --strip-components=1 \
  && cd jbig2 \
  && ./autogen.sh && ./configure && make install \
  && cd .. \
  && rm -rf jbig2

RUN apt-get uninstall autoconf automake libtool

RUN python3 -m venv --system-site-packages /appenv

# This installs the latest binary wheel instead of the code in the current
# folder. Installing from source will fail, apparently because cffi needs
# build-essentials (gcc) to do a source installation
# (i.e. "pip install ."). It's unclear to me why this is the case.
RUN . /appenv/bin/activate; \
  pip install --upgrade pip \
  && pip install ocrmypdf

# Now copy the application in, mainly to get the test suite.
# Do this now to make the best use of Docker cache.
COPY . /application
RUN . /appenv/bin/activate; \
  pip install -r /application/test_requirements.txt

# Remove the junk, including the source version of application since it was
# already installed
RUN rm -rf /tmp/* /var/tmp/* /root/* /application/ocrmypdf \
  && apt-get autoremove -y \
  && apt-get autoclean -y

RUN useradd docker \
  && mkdir /home/docker \
  && chown docker:docker /home/docker

USER docker
WORKDIR /home/docker

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/.docker/docker-wrapper.sh"]
