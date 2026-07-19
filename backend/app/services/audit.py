from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.system_models import AuditLog


def log_action(
    db: Session,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Writes a lightweight audit trail entry. Never logs full financial
    record contents -- only the action taken and which resource it touched,
    per the security requirement to avoid logging sensitive financial data."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
