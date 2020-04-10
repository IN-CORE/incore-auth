import logging
import os

import requests

from flask import Flask, request, Response, make_response
from flask_caching import Cache
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from urllib.parse import unquote_plus

config = {
    "DEBUG": False,
    "CACHE_TYPE": "filesystem",
    "CACHE_THRESHOLD": 600,  # max number of items the cache stores before it starts deleting values
    "CACHE_DEFAULT_TIMEOUT": 86400,  # cache will last for one day
    "CACHE_DIR": "./cache/"
}
app = Flask(__name__)

app.config.from_mapping(config)
cache = Cache(app)


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
    # check if the url is for the /healthz route, in the future we might need to check what is the actual rule
    if request.url_rule is not None:
        return healthz()

    # check if the url contains a keyword for the IN-CORE services
    if '/dfr3' in request.url or '/data' in request.url or '/hazard' in request.url \
            or '/space' in request.url or '/service' in request.url or '/lab' in request.url:
        headers = {}
        if request.headers.get('Authorization') is not None:
            headers['Authorization'] = unquote_plus(request.headers['Authorization'])
        elif request.cookies.get('Authorization') is not None:
            headers['Authorization'] = unquote_plus(request.cookies['Authorization'])
        else:
            response = make_response('Unauthorized', 401)
            return response

        public_key = f"-----BEGIN PUBLIC KEY-----\n"\
                     f"{str(os.environ.get('KEYCLOAK_PUBLIC_KEY'))}"\
                     f"\n-----END PUBLIC KEY-----"
        try:
            access_token = headers['Authorization'].split(" ")[1]
        except IndexError:
            return make_response('Invalid token', 401)
        try:
            access_token = jwt.decode(access_token, public_key)
        except ExpiredSignatureError:
            return make_response('JWT Expired Signature Error: token signature has expired', 401)
        except JWTClaimsError:
            return make_response('JWT Claims Error: token signature is invalid', 401)
        except JWTError:
            return make_response('JWT Error: token signature is invalid', 401)

        if '/lab' in request.url:
            if "incore_jupyter" not in access_token["groups"]:
                return Response(status=403)
        else:
            if "incore_user" not in access_token["groups"]:
                return Response(status=403)
        response = get_user_info_from_cache(headers['Authorization'])
        if response is not None:
            return response

        # if token not in cache, return response from keycloak
        return get_user_info_from_keycloak(headers)
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


def get_user_info_from_cache(token: str):
    """
    Try to get user info from cache
    :param token: bearer access token
    :return: 200 with updated headers if token is in the cache, None otherwise
    """
    user_info = cache.get(token)
    if user_info is None:
        return None

    response = Response(status=200)
    response.headers['x-auth-userinfo'] = user_info
    response.headers['Authorization'] = token
    # for testing purposes
    # app.logger.info(user_info)
    return response


def get_user_info_from_keycloak(headers: dict):
    """
    Try to get user info from keycloak
    :param headers: dictionary containing Authorization bearer access token
    :return: HTTP response 200 with updated headers containing user-info, HTTP response 401 otherwise
    """
    url = os.environ.get('KEYCLOAK_URL')
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        response = Response(status=200)
        cache.set(headers['Authorization'], r.text)
        response.headers['x-auth-userinfo'] = r.text
        response.headers['Authorization'] = headers['Authorization']
        app.logger.info(r.text)
        return response
    return Response(status=401)


# for testing locally
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
