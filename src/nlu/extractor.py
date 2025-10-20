import re
from typing import List, Optional

import spacy
from pydantic import BaseModel, Field

from src.models.rules import RuleType

# Lazy load the spacy model to avoid loading it on module import
NLP = None

def get_nlp():
    global NLP
    if NLP is None:
        NLP = spacy.load("en_core_web_sm")
    return NLP


class ExtractionResult(BaseModel):
    """Structured result of the NLU extraction process."""
    rule_type: Optional[RuleType] = Field(None, description="The type of rule to be generated.")
    application_name: Optional[str] = Field(None, description="The name of the target application.")
    source_attributes: List[str] = Field(default_factory=list, description="Source attribute names.")
    identity_attributes: List[str] = Field(default_factory=list, description="Target identity attribute names.")


def _extract_rule_type(text: str) -> Optional[RuleType]:
    """Extracts the rule type based on keywords."""
    text_lower = text.lower()
    if "correlation" in text_lower:
        return RuleType.CORRELATION
    if "build map" in text_lower or "buildmap" in text_lower:
        return RuleType.BUILD_MAP
    if "pre-iterate" in text_lower or "preiterate" in text_lower:
        return RuleType.PRE_ITERATE
    return None


def _extract_application(doc: spacy.tokens.Doc) -> Optional[str]:
    """Extracts application name, often a proper noun after a preposition."""
    for token in doc:
        if token.lower_ in ["for", "from", "on"]:
            # Find the next proper noun chunk
            for child in token.children:
                if child.pos_ == "PROPN":
                    # Span multiple proper nouns like "Active Directory"
                    app_name = [child.text]
                    for right in child.rights:
                        if right.pos_ == "PROPN":
                            app_name.append(right.text)
                    return " ".join(app_name)
    return None


def _extract_attributes(text: str) -> List[str]:
    """Extracts potential attribute names using regex (camelCase, snake_case, or quoted)."""
    # Regex for camelCase, snake_case, or attributes in quotes
    pattern = r"""
        \b[a-z]+[A-Z][a-zA-Z0-9_]*\b | # camelCase
        \b[a-z]+(?:_[a-z]+)+\b |       # snake_case
        '[a-zA-Z0-9_.+' |             # single-quoted
        "[a-zA-Z0-9_.]+"               # double-quoted
    """
    return re.findall(pattern, text, re.VERBOSE)


def extract_entities(text: str) -> ExtractionResult:
    """
    Processes a natural language string to extract IIQ rule components.

    Args:
        text: The natural language input from the user.

    Returns:
        An ExtractionResult object containing the extracted entities.
    """
    nlp = get_nlp()
    doc = nlp(text)

    rule_type = _extract_rule_type(text)
    application = _extract_application(doc)
    attributes = _extract_attributes(text)

    source_attrs = []
    identity_attrs = []

    # Simple logic to differentiate attributes for BuildMap rules
    if rule_type == RuleType.BUILD_MAP and "map" in text.lower() and len(attributes) >= 2:
        source_attrs.append(attributes[0])
        identity_attrs.append(attributes[1])
    else:
        source_attrs = attributes

    return ExtractionResult(
        rule_type=rule_type,
        application_name=application,
        source_attributes=source_attrs,
        identity_attributes=identity_attrs,
    )
