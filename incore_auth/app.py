import logging
import json
import os
import time
import urllib.request

import IP2Location
import geohash2
import influxdb_client

from flask import Flask, request, Response, make_response, json
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from urllib.parse import unquote_plus
from dotenv import load_dotenv

# Load .env file
load_dotenv()
CONTRIBUTION_DB_NAME = os.getenv('INFLUXDB_V2_FILE_LOCATION', 'data/IP2LOCATION-LITE-DB5.BIN')

config = json.load(open("config.json"))
app = Flask(__name__)
app.config.from_mapping(config)

geoserver = {}
geoserver_delta = 2

# setup database for geolocation
try:
    geolocation = IP2Location.IP2Location(CONTRIBUTION_DB_NAME)
except:
    app.logger.exception("No IP2Location database found.")
    geolocation = None
    pass

# setup logger to work nicely with gunicorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


def record_request(request_info):
    if 'X-Forwarded-For' not in request.headers:
        return

    # get some handy variables
    username = request_info["username"]
    resource = request_info['resource']
    uri = request_info['uri']

    # only track frontpage once
    if resource == "frontpage" and uri != "/":
        return

    # only track manual once
    if resource == "doc" and not uri.endswith("index.html"):
        app.logger.info(f"skipping resource {resource} - {request_info}")
        return

    # only track geoserver once every second
    if resource == "geoserver":
        if username in geoserver and geoserver[username] > time.time():
            return
        geoserver[username] = time.time() + geoserver_delta

    # skip non tracked resources
    if resource not in config["TRACKED_RESOURCES"]:
        app.logger.debug(f"ignoring resource {resource} - {request_info}")
        return
    app.logger.info(f"adding resource {resource} - {request_info}")

    remote_ip = request.headers.get('X-Forwarded-For', '')
    if not remote_ip:
        remote_ip = request.remote_addr

    server = request.headers.get('X-Forwarded-Host', '')
    if not server:
        server = request.host

    # find the group
    if "incore_ncsa" in request_info["groups"]:
        group = "NCSA"
    elif "incore_coe" in request_info["groups"]:
        group = "CoE"
    else:
        group = "public"

    # basic information for all endpoints
    tags = {
        "server": server,
        "http_method": request.method,
        "resource": resource,
        "username": username,
        "group": group
    }
    fields = {
        "url": uri,
        "ip": remote_ip,
        "elapsed": time.time() - request_info['start']
    }

    # store specific information
    fields.update(request_info['fields'])
    fields.update(request_info['tags'])

    # calculate geo location
    if geolocation:
        try:
            rec = geolocation.get_all(remote_ip)
            tags["country_code"] = rec.country_short
            tags["country"] = rec.country_long
            tags["region"] = rec.region
            tags["city"] = rec.city
            fields["latitude"] = rec.latitude
            fields["longitude"] = rec.longitude
            fields["geohash"] = geohash2.encode(rec.latitude, rec.longitude)
        except Exception:
            app.logger.error("Could not lookup IP address")

    # create the datapoint that is written to influxdb
    datapoint = {
        "measurement": "auth",
        "tags": tags,
        "fields": fields,
        "time": int(time.time() * 10 ** 9)
    }

    # either write to influxdb, or to console
    if config['influxdb']:
        config['influxdb'].write("incore", "incore", datapoint)
    else:
        app.logger.info(datapoint)


def request_userinfo(request_info):
    # retrieve access token from header or cookies
    try:
        if request.headers.get('Authorization') is not None:
            access_token = unquote_plus(request.headers['Authorization']).split(" ")[1]
        elif request.cookies.get('Authorization') is not None:
            access_token = unquote_plus(request.cookies['Authorization']).split(" ")[1]
        else:
            app.logger.debug("Missing Authorization header")
            request_info['error'] = 'Missing Authorization information'
            return
    except IndexError:
        app.logger.debug("Missing Authorization header")
        request_info['error'] = 'Missing Authorization information'
        return

    # decode token for validating its signature
    try:
        access_token = jwt.decode(access_token, config['public_key'], audience=config['audience'])
    except ExpiredSignatureError:
        app.logger.debug("token signature has expired")
        request_info['error'] = 'JWT Expired Signature Error: token signature has expired'
        return
    except JWTClaimsError:
        app.logger.debug("toke signature has invalid claim")
        request_info['error'] = 'JWT Claims Error: token signature is invalid'
        return
    except JWTError:
        app.logger.debug("jwt error")
        request_info['error'] = 'JWT Error: token signature is invalid'
        return
    except Exception:
        app.logger.debug("random exception")
        request_info['error'] = 'JWT Error: invalid token'
        return

    # retrieve the groups the user belongs to from access token
    request_info['username'] = access_token["preferred_username"]
    request_info['groups'] = access_token.get("groups", [])
    if "roles" in access_token:
        request_info['roles'] = access_token["roles"]
    elif "realm_access" in access_token:
        request_info['roles'] = access_token["realm_access"].get("roles", [])
    else:
        request_info['roles'] = []


def request_resource(request_info):
    try:
        uri = request.headers.get('X-Forwarded-Uri', '')
        if not uri:
            uri = request.url
        request_info['uri'] = uri
        pieces = uri.split('/')
        if len(pieces) == 2:
            if pieces[1] in config["TRACKED_RESOURCES"]:
                request_info['resource'] = pieces[1]
            else:
                request_info['resource'] = "frontpage"
        else:
            request_info['resource'] = pieces[1]
            if request_info['resource'] == "doc" and len(pieces) > 2:
                request_info['fields']['manual'] = pieces[2]
            if request_info['resource'] == "data" and len(pieces) > 4 and uri.endswith('blob'):
                request_info['fields']['dataset'] = pieces[4]
            if request_info['resource'] == "dfr3" and len(pieces) > 4:
                request_info['fields']['fragility'] = pieces[4]
    except IndexError:
        app.logger.info("No / found in path.")
        request_info['resource'] = 'NA'


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

    # allow options, probably CORS
    if request.headers.get('X-Forwarded-Method', '') == 'OPTIONS':
        return Response(status=200)

    # dict to hold all information
    request_info = {
        "username": "",
        "method": request.method,
        "url": request.path,
        "resource": "",
        "groups": [],
        "roles": [],
        "error": "",
        "fields": {},
        "tags": {},
        "start": time.time()
    }

    # get info requested
    request_resource(request_info)
    request_userinfo(request_info)

    # record request
    record_request(request_info)

    # non protected resource is always ok
    if request_info['resource'] not in app.config["PROTECTED_RESOURCES"]:
        return Response(status=200)

    # check the authentication
    if not request_info['username']:
        return make_response(request_info['error'], 401)

    # check the authorization
    authorized = False
    if "GROUPS" in app.config and not authorized:
        for group in request_info['groups']:
            if group in app.config["GROUPS"] and request_info['resource'] in app.config["GROUPS"][group]:
                authorized = True
                break
    if "ROLES" in app.config and not authorized:
        for role in request_info['roles']:
            if role in app.config["ROLES"] and request_info['resource'] in app.config["ROLES"][role]:
                authorized = True
                break
    if not authorized:
        app.logger.debug("role not found in user_accessible_resources")
        return make_response("access denied", 403)

    # everything is ok
    user_info = {"preferred_username": request_info['username']}
    group_info = {"groups": request_info['groups']}
    response = Response(status=200)
    response.headers['X-Auth-UserInfo'] = json.dumps(user_info)
    response.headers['X-Auth-UserGroup'] = json.dumps(group_info)

    if request.headers.get('Authorization') is not None:
        response.headers['Authorization'] = unquote_plus(request.headers['Authorization'])
    elif request.cookies.get('Authorization') is not None:
        response.headers['Authorization'] = unquote_plus(request.cookies['Authorization'])

    if request.headers.get('X-UserGroup') is not None:
        response.headers['X-UserGroup'] = request.headers.get('x-UserGroup')
    elif request.cookies.get('X-UserGroup') is not None:
        response.headers['X-UserGroup'] = request.cookies['X-UserGroup']

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
        raise(Exception(f"Could not load data from {url} code={response.code}"))


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

    # setup influxdb
    try:
        client = influxdb_client.InfluxDBClient.from_env_properties()
        writer = client.write_api()
        config['influxdb'] = writer
    except:
        app.logger.exception("Could not setup influxdb writer")
        config['influxdb'] = None
        pass


# for testing locally
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
