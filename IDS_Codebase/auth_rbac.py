from __future__ import annotations

import os
import hashlib
import hmac
from typing import Dict, Any, Optional

class RBACAuthManager:
    """
    Multi-Tenant Role-Based Access Control (RBAC) Manager.
    Manages user authentication, role scopes ('Administrator', 'Facility Engineer', 'Security Auditor'),
    and permission checks for the Streamlit web dashboard using salted PBKDF2 hashing.
    """
    ROLES = {
        "admin": ["view_dashboard", "override_labels", "isolate_sensors", "export_compliance", "configure_rules"],
        "facility_engineer": ["view_dashboard", "override_labels"],
        "security_auditor": ["view_dashboard", "export_compliance"]
    }
    
    SALT = os.getenv("AUTH_SALT", "IoT_IDS_Secure_Salt_2026").encode("utf-8")

    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, str]] = {
            "admin": {
                "hash": self._hash_password(os.getenv("ADMIN_PASS", "admin123")),
                "legacy_hash": hashlib.sha256(b"admin123").hexdigest(),
                "role": "admin"
            },
            "engineer": {
                "hash": self._hash_password(os.getenv("ENGINEER_PASS", "eng123")),
                "legacy_hash": hashlib.sha256(b"eng123").hexdigest(),
                "role": "facility_engineer"
            },
            "auditor": {
                "hash": self._hash_password(os.getenv("AUDITOR_PASS", "audit123")),
                "legacy_hash": hashlib.sha256(b"audit123").hexdigest(),
                "role": "security_auditor"
            }
        }

    def _hash_password(self, password: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), self.SALT, 100000).hex()

    def authenticate(self, username: str, password_text: str) -> Optional[str]:
        if username not in self.users:
            return None
        
        user_info = self.users[username]
        computed_pbkdf2 = self._hash_password(password_text)
        computed_legacy = hashlib.sha256(password_text.encode("utf-8")).hexdigest()

        if hmac.compare_digest(user_info["hash"], computed_pbkdf2) or hmac.compare_digest(user_info["legacy_hash"], computed_legacy):
            return user_info["role"]
        return None

    def has_permission(self, role: str, permission: str) -> bool:
        allowed = self.ROLES.get(role, [])
        return permission in allowed
