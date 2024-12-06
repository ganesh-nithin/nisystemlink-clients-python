from typing import Any, Dict, List, Optional
from pydantic import Field

from nisystemlink.clients.core._uplink._json_model import JsonModel


class CreateJobRequest(JsonModel):
    """Model for create job request."""

    arguments: Optional[List[List[Any]]] = Field(None, alias="args")
    """List of arguments to the functions specified in the "fun" property."""

    target_systems: Optional[List[str]] = Field(None, alias="tgt")
    """List of system IDs on which to run the job."""

    functions: Optional[List[str]] = Field(None, alias="fun")
    """Functions contained in the job."""

    metadata: Optional[Dict[str, Any]] = None
    """Additional information of the job."""
