import logging
import json
import os
import urllib.request

from flask import Flask, request, Response, make_response, json
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from urllib.parse import unquote_plus

config = json.load(open("config.json"))

app = Flask(__name__)

app.config.from_mapping(config)

# setup logger to work nicely with gunicorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


@app.before_request
def verify_token():
    """
    This function distinguishes between requests that need authorization
    and verifies if those who need to be authorized contain the access
    token in its headers or cookies. If the token verification and user
    authorization was successful, it updates the headers, adding a
    user-info string.
    :return: HTTP response. 200 if path is not protected. 200 if path is
    protected and meets the following criteria: 1) request contains an
    Authorization header or cookie with bearer token. 2) The access
    token has a valid signature (not expired or invalid). 3) The user
    belongs to the appropriate group required to access the protected
    path. 401 if token is invalid or not present. 403 if token is
    present and valid but the user does not belong to the appropriate
    groups for the protected path.
    """
    # check if the url is for the /healthz route, in the future we might
    # need to check what is the actual rule
    if request.url_rule is not None:
        return healthz()

    # retrieve resource from url
    path = request.url[len(request.url_root):]
    try:
        resource = path.split('/')[0]
    except IndexError:
        app.logger.info("No / found in path.")
        return Response(status=200)

    if resource not in app.config["PROTECTED_RESOURCES"]:
        return Response(status=200)

    # retrieve access token from header or cookies
    headers = {}
    if request.headers.get('Authorization') is not None:
        headers['Authorization'] = unquote_plus(
            request.headers['Authorization'])
    elif request.cookies.get('Authorization') is not None:
        headers['Authorization'] = unquote_plus(
            request.cookies['Authorization'])
    else:
        app.logger.debug("Missing Authorization header")
        response = make_response('Unauthorized', 401)
        return response
    try:
        access_token = headers['Authorization'].split(" ")[1]
    except IndexError:
        app.logger.debug("invalid formed Authorization header")
        return make_response('Invalid token', 401)

    # decode token for validating its signature
    try:
        access_token = jwt.decode(access_token, config['public_key'],
                                  audience=config['audience'])
    except ExpiredSignatureError:
        app.logger.debug("token signature has expired")
        return make_response(
            'JWT Expired Signature Error: token signature has expired', 401)
    except JWTClaimsError:
        app.logger.debug("toke signature has invalid claim")
        return make_response(
            'JWT Claims Error: token signature is invalid', 401)
    except JWTError:
        app.logger.debug("jwt error")
        return make_response('JWT Error: token signature is invalid', 401)
    except Exception:
        app.logger.debug("random exception")
        return make_response('JWT Error: invalid token', 401)

    # retrieve the groups the user belongs to from access token
    user_groups = access_token.get("groups", [])
    if "roles" in access_token:
        user_roles = access_token["roles"]
    elif "realm_access" in access_token:
        user_roles = access_token["realm_access"].get("roles", [])
    else:
        user_roles = []

    # get all resources the user can access to, based on the groups
    # the user belongs to
    user_accessible_resources = []
    if "GROUPS" in app.config:
        for group in user_groups:
            if group in app.config["GROUPS"]:
                user_accessible_resources.extend(app.config["GROUPS"][group])
    if "ROLES" in app.config:
        for role in user_roles:
            if role in app.config["ROLES"]:
                user_accessible_resources.extend(app.config["ROLES"][role])

    if resource not in user_accessible_resources:
        app.logger.debug("role not found in user_accessible_resources")
        return make_response("access denied", 403)

    # form user-info and add it to the response headers
    user_info = {"preferred_username": access_token["preferred_username"]}
    response = Response(status=200)
    response.headers['x-auth-userinfo'] = json.dumps(user_info)
    response.headers['Authorization'] = headers['Authorization']

    if request.headers.get('x-userinfo') is not None:
        response.headers['x-userinfo'] = request.headers.get('x-userinfo')
    elif request.cookies.get('x-userinfo') is not None:
        response.headers['x-userinfo'] = request.headers.get('x-userinfo')
    return response


@app.route("/healthz", methods=["GET"])
def healthz():
    return Response("OK", 200)


def urljson(url):
    response = urllib.request.urlopen(url)
    if response.code >= 200 or response <= 299:
        encoding = response.info().get_content_charset('utf-8')
        return json.loads(response.read().decode(encoding))
    else:
        raise(Exception(f"Could not load data from {url} "
                        f"code={response.code}"))


@app.before_first_request
def setup():
    keycloak_pem = os.environ.get('KEYCLOAK_PUBLIC_KEY', None)
    if keycloak_pem:
        config['pem'] = str(keycloak_pem)
        app.logger.info("Got public_key from environment variable.")
    else:
        keycloak_url = os.environ.get('KEYCLOAK_URL', None)
        if keycloak_url:
            result = urljson(keycloak_url)
            config['pem'] = result['public_key']
            app.logger.info("Got public_key from url.")
        else:
            config['pem'] = ''
            app.logger.error("Could not find PEM, things will be broken.")
    config['public_key'] = f"-----BEGIN PUBLIC KEY-----\n" \
                           f"{config['pem']}\n" \
                           f"-----END PUBLIC KEY-----"

    keycloak_audience = os.environ.get('KEYCLOAK_AUDIENCE', None)
    if keycloak_audience:
        config['audience'] = keycloak_audience
    else:
        config['audience'] = None

# for testing locally
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
