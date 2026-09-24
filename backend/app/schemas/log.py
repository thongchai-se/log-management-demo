from pydantic import BaseModel, Field
from typing import Optional, Any


class LogIngestRequest(BaseModel):
    timestamp: Optional[str] = Field(default=None, alias="@timestamp")
    tenant: str = "default"
    source: Optional[str] = "api"
    vendor: Optional[str] = None
    product: Optional[str] = None
    event_type: Optional[str] = None
    event_subtype: Optional[str] = None
    severity: int = 0
    action: Optional[str] = None
    ip: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    user: Optional[str] = None
    host: Optional[str] = None
    process: Optional[str] = None
    url: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    rule_name: Optional[str] = None
    rule_id: Optional[str] = None
    cloud: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, alias="_tags")

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }
