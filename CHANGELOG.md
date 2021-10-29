# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

From version 1.2.0 the file IP2LOCATION-LITE-DB5.BIN is no longer part of the docker image and will need to be downloaded (after registration) from [ip2location](https://lite.ip2location.com/database/ip-country?lang=en_US) and be placed in /srv/incore_auth.

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
