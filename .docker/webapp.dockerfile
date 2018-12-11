# OCRmyPDF polyglot
#
FROM      jbarlow83/ocrmypdf:latest

USER root

# Update system and install our dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3-flask

RUN apt-get autoremove -y && apt-get clean -y

EXPOSE 5000

COPY .docker/webapp.py /application

USER docker

ENTRYPOINT ["python3", "/application/webapp.py"]
