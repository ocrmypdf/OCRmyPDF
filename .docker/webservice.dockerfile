# OCRmyPDF webservice
#
FROM      jbarlow83/ocrmypdf-polyglot:latest

USER root

# Update system and install our dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3-flask

RUN apt-get autoremove -y && apt-get clean -y

EXPOSE 5000

COPY .docker/webservice.py /application

USER docker

VOLUME ["/config"]

# This config file is optional
ENV OCRMYPDF_WEBSERVICE_SETTINGS "/config/config.py"

ENTRYPOINT ["python3", "/application/webservice.py"]
