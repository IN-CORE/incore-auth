# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

From version 1.2.0 the file IP2LOCATION-LITE-DB5.BIN is no longer part of the docker image and will need to be downloaded (after registration) from [ip2location](https://lite.ip2location.com/database/ip-country?lang=en_US) and be placed in /srv/incore_auth.

# [Unreleased]

## Added
- New user default usage to zero [#38](https://github.com/IN-CORE/incore-auth/issues/38)


# [1.6.0] - 2023-03-14

## Added
- information about user and groups is synced every 30 minutes back to the database and datawolf

## Changed
- Added playbook and its sub directories to tracking resource [#32](https://github.com/IN-CORE/incore-auth/issues/32)
- updated all packages used

# [1.5.0] - 2022-09-24

## Changed
- updated docker build script. Can push to github, dockerhub and ncsa [#27](https://github.com/IN-CORE/incore-auth/issues/27)
- build both x86 and arm images [#24](https://github.com/IN-CORE/incore-auth/issues/24)
- Hub path has been added to protected path. [#25](https://github.com/IN-CORE/incore-auth/issues/25)

# [1.4.0] - 2021-03-29

## Changed
- Tracking calls to /DFR3Viewer /DataViewer /HazardViewer /jupyterhub
- Only track index.html and / for doc and frontpage.
- X-Usergroup in the header changed to X-Auth-Usergroup

# [1.3.0] - 2021-21-08

## Added
- IP2Location's file location as variable

## Changed
- Removed adding X-Userinfo from response headers

# [1.2.1] - 2021-10-29

## Fixed
- had invalid config for hub resources (extra comma)

# [1.2.0] - 2021-10-28

## Added
- github actions

## Changed
- IP2LOCATION-LITE-DB5.BIN is no longer bundled in docker image.

# [1.1.0] - 2021-10-27

## Added
- maestro service to resources

# [1.0.6] - 2021-07-28

## Added
- plotting service to resources

# [1.0.5] - 2021-06-16

## Fixed
- playbook is not protected resource anymore since it has its own login.

# [1.0.4] - 2021-05-19

## Added
- user's group info to output response header

## Fixed
- allow for options to pass without checks, this will allow for CORS requests

# [1.0.3] - 2021-04-12

First official release

# [1.0.2] -

First intermediate release of  auth code, was not officially released

# [1.0.1] -

Code was migrated from incore-kubernetes, to own repository
