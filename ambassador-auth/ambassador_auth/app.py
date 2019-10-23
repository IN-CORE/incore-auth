from flask import Flask, request, Response, make_response

import requests
import logging
import config as cfg

app = Flask(__name__)

@app.before_request
def verify_token():
    """
    This function distinguishes between requests that need authentication and  verifies if those who need to be
    authenticated contain the authorization token in its headers or cookies and verifies
    with keycloak if the token is valid. If the verification was successful, it updates the headers with
    the user-info received from keycloak.
    :return: 200 if authentication is not required, 200 if authentication is required and token is present and valid,
    401 otherwise.
    """
    # check if the url is for the /healthz route, in the future we might need check what is the actual rule
    if request.url_rule is not None:
        return healthz()

    # check if the url contains a keyword for the incore services
    if '/api' in request.url or '/dfr3' in request.url or '/data' in request.url or '/hazard' in request.url \
            or '/space' in request.url or '/doc' in request.url or '/service' in request.url:
        headers = {}
        if request.headers.get('Authorization') is not None:
            headers['Authorization'] = request.headers['Authorization']
        else:
            response = make_response('Unauthorized', 401)
            return response

        url = cfg.KEYCLOAK_URL
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            response = Response(status=200)
            response.headers['x-auth-userinfo'] = r.text
            return response

        return Response(status=401)
    else:
        return Response(status=200)


@app.route("/healthz", methods=["GET"])
def healthz():
    return Response("Healthz OK", 200)


@app.before_first_request
def setup():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
