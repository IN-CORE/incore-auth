import logging
import os

from flask import Flask, request, Response, make_response, json
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from urllib.parse import unquote_plus

config = {
    "PROTECTED_RESOURCES": ["dfr3", "data", "hazard", "space"],
    "GROUPS": {"incore_user": ["dfr3", "data", "hazard", "space"]}
}

app = Flask(__name__)

app.config.from_mapping(config)


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
        response = make_response('Unauthorized', 401)
        return response
    try:
        access_token = headers['Authorization'].split(" ")[1]
    except IndexError:
        return make_response('Invalid token', 401)
    public_key = f"-----BEGIN PUBLIC KEY-----\n" \
        f"{str(os.environ.get('KEYCLOAK_PUBLIC_KEY'))}" \
        f"\n-----END PUBLIC KEY-----"

    # decode token for validating its signature
    try:
        access_token = jwt.decode(access_token, public_key)
    except ExpiredSignatureError:
        return make_response(
            'JWT Expired Signature Error: token signature has expired', 401)
    except JWTClaimsError:
        return make_response('JWT Claims Error: token signature is invalid',
                             401)
    except JWTError:
        return make_response('JWT Error: token signature is invalid', 401)

    # retrieve the groups the user belongs to from access token
    try:
        user_groups = access_token["groups"]
    except KeyError:
        return make_response('Invalid token', 401)

    # get all resources the user can access to, based on the groups
    # the user belongs to
    user_accessible_resources = []
    for group in user_groups:
        if group in app.config["GROUPS"]:
            user_accessible_resources.extend(app.config["GROUPS"][group])

    if resource not in user_accessible_resources:
        return Response(status=403)

    # form user-info and add it to the response headers
    user_info = {"preferred_username": access_token["preferred_username"]}
    response = Response(status=200)
    response.headers['x-auth-userinfo'] = json.dumps(user_info)
    response.headers['Authorization'] = headers['Authorization']
    return response


@app.route("/healthz", methods=["GET"])
def healthz():
    return Response("OK", 200)


@app.before_first_request
def setup():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)

# for testing locally
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
