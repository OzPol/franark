"""Single-tenant JWT verification; local development has a separate identity."""
from dataclasses import dataclass
import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class Principal:
    subject: str
    display_name: str
    roles: frozenset[str]

    @property
    def is_admin(self):
        return "Franark.Admin" in self.roles

    @property
    def can_review(self):
        return self.is_admin or "Franark.Reviewer" in self.roles


LOCAL_PRINCIPAL = Principal("local-pilot", "Local pilot", frozenset({"Franark.Admin"}))


class AuthenticationUnavailable(RuntimeError):
    pass


class EntraAuthenticator:
    def __init__(self, settings, key_client=None):
        self.settings = settings
        self.key_client = key_client or PyJWKClient(
            f"https://login.microsoftonline.com/{settings.tenant_id}/discovery/v2.0/keys", timeout=5)

    def authenticate(self, headers):
        authorization = headers.get("authorization", "")
        token = authorization[7:] if authorization.startswith("Bearer ") else headers.get("x-ms-token-aad-id-token", "")
        if not token or len(token) > 32000:
            raise jwt.InvalidTokenError("An Entra token is required.")
        try:
            key = self.key_client.get_signing_key_from_jwt(token).key
        except jwt.PyJWKClientConnectionError as exc:
            raise AuthenticationUnavailable("Identity key service unavailable.") from exc
        claims = jwt.decode(token, key, algorithms=["RS256"],
            audience=self.settings.client_id,
            issuer=f"https://login.microsoftonline.com/{self.settings.tenant_id}/v2.0",
            options={"require": ["exp", "iat", "iss", "aud", "tid", "oid"]})
        if claims["tid"] != self.settings.tenant_id:
            raise jwt.InvalidTokenError("Tenant mismatch.")
        roles = claims.get("roles", [])
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            raise jwt.InvalidTokenError("Invalid role claims.")
        allowed = frozenset(roles) & {"Franark.Pilot", "Franark.Reviewer", "Franark.Admin"}
        if not allowed:
            raise PermissionError("An assigned Franark app role is required.")
        if not isinstance(claims["oid"], str) or not claims["oid"] or len(claims["oid"]) > 200:
            raise jwt.InvalidTokenError("Invalid identity subject.")
        return Principal(claims["oid"], str(claims.get("name", "SFC employee"))[:200], allowed)
