from flask import Flask, request, Response, make_response

import requests
import logging

app = Flask(__name__)


@app.before_request
def verify_token():
    """
    This function verifies if any request contains the authorization token in its headers or cookies, then it verifies
    with keycloak if the token is valid, and updates the headers with the user info if successful.
    :return: user info headers and 200 if token is valid, 401 otherwise.
    """
    headers = {}
    if request.headers.get('Authorization') is not None:
        headers['Authorization'] = request.headers['Authorization']
    elif 'Authorization' in request.cookies:
        headers['Authorization'] = request.cookies['Authorization']
    else:
        response = make_response('Unauthorized', 401)
        return response

    url = r'https://incore-dev-kube.ncsa.illinois.edu/auth/realms/In-core/protocol/openid-connect/userinfo'
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        response = make_response('OK', r.status_code)
        response.headers['x-auth-userinfo'] = r.text
        return response

    return Response(status=401)


@app.before_first_request
def setup():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
