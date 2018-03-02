# OCRmyPDF polyglot
#
FROM      jbarlow83/ocrmypdf:latest

USER root

# Update system and install our dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  tesseract-ocr-all 

RUN apt-get autoremove -y && apt-get clean -y

USER docker

# Must use array form of ENTRYPOINT
# Non-array form does not append other arguments, because that is "intuitive"
ENTRYPOINT ["/application/.docker/docker-wrapper.sh"]