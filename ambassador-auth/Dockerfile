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

#COPY requirements/ requirements/
COPY requirements.txt .
RUN pip install -Ur requirements.txt

COPY ambassador_auth ambassador_auth

WORKDIR /srv/ambassador_auth

ENV FLASK_APP="app.py"

CMD ["python", "-m", "flask", "run", "--host", "0.0.0.0"]

#ENTRYPOINT ["gunicorn", \
#    "--access-logfile=-", \
#    "--log-level=info", \
#    "--workers=3", \
#    "--bind=0.0.0.0:5000", \
#    "ambassador_auth.app:app" \
#    ]

