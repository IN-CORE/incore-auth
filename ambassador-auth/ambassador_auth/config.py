import os 

KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'https://incore-dev-kube.ncsa.illinois.edu/auth/realms/In-core/protocol/openid-connect/userinfo')