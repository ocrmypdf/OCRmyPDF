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
  ghostscript \
  tesseract-ocr \
  tesseract-ocr-deu tesseract-ocr-spa tesseract-ocr-eng tesseract-ocr-fra \
  qpdf \
  unpaper \
  poppler-utils \
  python3 \
  python3-pip \
  python3-venv \
  python3-reportlab \
  python3-pil

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

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/docker-wrapper.sh"]