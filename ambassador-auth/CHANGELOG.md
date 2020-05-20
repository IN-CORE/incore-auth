# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

## Unreleased
- Added a group check to tokens for validating authorization to resources - [INCORE1-553](https://opensource.ncsa.illinois.edu/jira/browse/INCORE1-553)

## [0.1.4] - 2019-11-22
### Added
- Added a cache to store {token: user-info} to avoid excessive calls to keycloak
- Added a uri decoder for the token
### Fixed
- Fixed bug related to a badly initiated token variable


## [0.1.3] - 2019-10-31
### Added
- Added Authorization header to the response.headers

## [0.1.2] - 2019-10-26

### Added
- Added a healthz route
- Added an instance folder with keycloak userinfo variable in the config file
### Changed
- Changed functionality to check what the request url is to see if it needs authorization


## [0.1.1] - 2019-10-18

### Added

- Implement token verification scheme
