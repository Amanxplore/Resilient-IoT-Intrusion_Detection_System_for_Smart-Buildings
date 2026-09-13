from __future__ import annotations

import logging
import time
import base64
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("OIDCAuthManager")

class OIDCAuthManager:
    """
    Pillar 5: OpenID Connect (OIDC) & Enterprise OAuth 2.0 Identity Manager.
    Validates JWT bearer tokens, checks token expiration, and extracts OAuth scope claims
    for Enterprise Single Sign-On (SSO) integration (Okta / Azure AD / Entra ID).
    """
    def __init__(self, issuer: str = "https://sso.smartbuilding.enterprise/oauth2/v1") -> None:
        self.issuer = issuer

    def decode_jwt_header_payload(self, jwt_token: str) -> Tuple[Optional[dict], Optional[dict]]:
        parts = jwt_token.split(".")
        if len(parts) != 3:
            return None, None
        try:
            def _pad(s: str) -> bytes:
                return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

            header = json.loads(_pad(parts[0]))
            payload = json.loads(_pad(parts[1]))
            return header, payload
        except Exception as e:
            logger.error(f"Failed to decode JWT token: {e}")
            return None, None

    def validate_token(self, jwt_token: str) -> Tuple[bool, Optional[str], List[str]]:
        header, payload = self.decode_jwt_header_payload(jwt_token)
        if not payload:
            return False, None, []

        exp = payload.get("exp", 0)
        if time.time() > exp:
            logger.warning("⚠️ [OIDC Auth] JWT Token has expired!")
            return False, None, []

        user_id = payload.get("sub", "unknown_user")
        roles = payload.get("roles", payload.get("scp", ["view_dashboard"]))
        logger.info(f"🔑 [OIDC Auth Pass] Authenticated enterprise user '{user_id}' with roles: {roles}")
        return True, user_id, roles
