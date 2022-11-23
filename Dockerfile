FROM python:3.7-alpine

MAINTAINER Incore <incore-dev@lists.illinois.edu>
LABEL PROJECT_REPO_URL         = "" \
      PROJECT_REPO_BROWSER_URL = "" \
      DESCRIPTION              = ")"

WORKDIR /srv

COPY incore_auth/requirements.txt incore_auth/
RUN pip3 install -Ur incore_auth/requirements.txt

COPY incore_auth incore_auth

WORKDIR /srv/incore_auth

ENV FLASK_APP="app.py" \
    KEYCLOAK_PUBLIC_KEY="" \
    KEYCLOAK_AUDIENCE="" \
    DATAWOLF_URL="http://incore-datawolf:8888/datawolf" \
    MONGODB_URI="" \
    INFLUXDB_V2_URL="" \
    INFLUXDB_V2_ORG="" \
    INFLUXDB_V2_TOKEN="" \
    INFLUXDB_V2_FILE_LOCATION="data/IP2LOCATION-LITE-DB5.BIN"

CMD ["gunicorn", "app:app", "--config", "/srv/incore_auth/gunicorn.config.py"]
