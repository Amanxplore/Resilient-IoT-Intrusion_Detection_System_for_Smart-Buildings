from __future__ import annotations

import hashlib
from typing import Dict, Any, Optional

class RBACAuthManager:
    """
    Multi-Tenant Role-Based Access Control (RBAC) Manager.
    Manages user authentication, role scopes ('Administrator', 'Facility Engineer', 'Security Auditor'),
    and permission checks for the Streamlit web dashboard.
    """
    ROLES = {
        "admin": ["view_dashboard", "override_labels", "isolate_sensors", "export_compliance", "configure_rules"],
        "facility_engineer": ["view_dashboard", "override_labels"],
        "security_auditor": ["view_dashboard", "export_compliance"]
    }

    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, str]] = {
            "admin": {"hash": hashlib.sha256(b"admin123").hexdigest(), "role": "admin"},
            "engineer": {"hash": hashlib.sha256(b"eng123").hexdigest(), "role": "facility_engineer"},
            "auditor": {"hash": hashlib.sha256(b"audit123").hexdigest(), "role": "security_auditor"}
        }

    def authenticate(self, username: str, password_text: str) -> Optional[str]:
        if username not in self.users:
            return None
        hashed = hashlib.sha256(password_text.encode("utf-8")).hexdigest()
        if self.users[username]["hash"] == hashed:
            return self.users[username]["role"]
        return None

    def has_permission(self, role: str, permission: str) -> bool:
        allowed = self.ROLES.get(role, [])
        return permission in allowed
