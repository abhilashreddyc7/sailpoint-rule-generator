from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Enumeration for different SailPoint IIQ Rule types."""
    CORRELATION = "Correlation"
    BUILD_MAP = "BuildMap"
    PRE_ITERATE = "PreIterate"
    # Add other rule types here as needed


class RuleParameter(BaseModel):
    """Defines an input parameter for a SailPoint IIQ Rule."""
    name: str = Field(..., description="The name of the parameter, e.g., 'log' or 'context'.")
    param_type: str = Field(..., description="The Java type of the parameter, e.g., 'Log', 'SailPointContext'.")
    description: Optional[str] = Field(None, description="A brief description of the parameter's purpose.")


class RuleDefinition(BaseModel):
    """Represents a complete SailPoint IIQ Rule definition."""
    name: str = Field(..., description="The name of the rule in SailPoint IIQ.")
    rule_type: RuleType = Field(..., description="The type of the rule.")
    description: Optional[str] = Field(None, description="A high-level description of what the rule does.")
    parameters: List[RuleParameter] = Field(default_factory=list, description="List of input parameters for the rule.")
    source_code: Optional[str] = Field(None, description="The Java source code of the rule.")
