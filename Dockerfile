FROM alpine:3.7

MAINTAINER Incore <incore-dev@lists.illinois.edu>
LABEL PROJECT_REPO_URL         = "" \
      PROJECT_REPO_BROWSER_URL = "" \
      DESCRIPTION              = ")" 

RUN apk add --no-cache \
    gcc \
    g++ \
    libffi-dev \
    make \
    python3 \
    python3-dev \
    openssl-dev && \
  python3 -m ensurepip && \
  rm -r /usr/lib/python*/ensurepip && \
  pip3 install --upgrade pip setuptools && \
  if [[ ! -e /usr/bin/pip ]]; then ln -s pip3 /usr/bin/pip; fi && \
  if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
  rm -r /root/.cache

WORKDIR /srv

COPY incore_auth/requirements.txt incore_auth/
RUN pip install -Ur incore_auth/requirements.txt

COPY IP2LOCATION-LITE-DB5.BIN* incore_auth/

COPY incore_auth incore_auth

WORKDIR /srv/incore_auth

ENV FLASK_APP="app.py" \
    KEYCLOAK_PUBLIC_KEY="" \
    KEYCLOAK_AUDIENCE="" \
    INFLUXDB_V2_URL="" \
    INFLUXDB_V2_ORG="" \
    INFLUXDB_V2_TOKEN=""

#CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0"]
CMD ["gunicorn", "app:app", "--config", "/srv/incore_auth/gunicorn.config.py"]

#ENTRYPOINT ["gunicorn", \
#    "--access-logfile=-", \
#    "--log-level=info", \
#    "--workers=3", \
#    "--bind=0.0.0.0:5000", \
#    "incore_auth.app:app" \
#    ]

