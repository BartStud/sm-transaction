import logging

from keycloak.keycloak_admin import KeycloakAdmin

from app.core.config import (
    KEYCLOAK_HOST,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET_KEY,
    KEYCLOAK_REALM,
)

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("keycloak")
logger.setLevel(logging.DEBUG)

keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_HOST,
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret_key=KEYCLOAK_CLIENT_SECRET_KEY,
    realm_name=KEYCLOAK_REALM,
    verify=False,
)
# ustawiwnia admin-cli
#   - Client authentication - on
#   - Authorization Enabled - on
#   - Direct Access Grants - on
#   - Service Accounts Roles Enabled - on
# client_secret_key -> Clients -> admin-cli -> Credentials -> Client Secret
# dodanie ról:
#   Clients -> admin-cli -> Service Account Roles -> view-users
#   Clients -> admin-cli -> Service Account Roles -> manage-users
