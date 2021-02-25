# INCORE Token Verification

This module is used as a gatekeeper for all services. The list of services that require authentication
is controlled by the config.json file. Services listed under `PROTECTED_RESOURCES` require a valid
jwt token. The sections `GROUPS` and `ROLES` are used for authorization. It will check if the jwt token
has the appropriate group for each service.

```json
{
    "PROTECTED_RESOURCES": ["dfr3", "data", "hazard", "space", "semantics", "datawolf", "playbook"],
    "GROUPS": {"incore_user": ["dfr3", "data", "hazard", "space", "semantics", "datawolf", "playbook"]},
    "ROLES": {"incore_user": ["dfr3", "data", "hazard", "space", "semantics", "datawolf", "playbook"]}
}
```

The auth module will track usage in influxdb (if enabled). To track the geolocation you will need
IP2LOCATION-LITE-DB5.BIN.
