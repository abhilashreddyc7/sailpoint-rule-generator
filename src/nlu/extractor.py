import re
from typing import List, Optional
from enum import Enum

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


class Intent(str, Enum):
    """Enumeration for user intents."""
    GENERATE_RULE = "Generate Rule"
    MODIFY_RULE = "Modify Rule"
    EXPLAIN_RULE = "Explain Rule"


class ExtractionResult(BaseModel):
    """Structured result of the NLU extraction process."""
    intent: Optional[Intent = Field(None, description="The user's primary goal.")
    rule_type: Optional[RuleType] = Field(None, description="The type of rule to be generated.")
    application_name: Optional[str] = Field(None, description="The name of the target application.")
    source_attributes: List[str] = Field(default_factory=list, description="Source attribute names.")
    identity_attributes: List[str] = Field(default_factory=list, description="Target identity attribute names.")


def _extract_intent(text: str) -> Optional[Intent]:
    """Extracts the user's intent based on keywords."""
    text_lower = text.lower()
    if any(verb in text_lower for verb in ["create", "generate", "make", "build"]):
        return Intent.GENERATE_RULE
    if any(verb in text_lower for verb in ["change", "modify", "update", "amend"]):
        return Intent.MODIFY_RULE
    if any(verb in text_lower for verb in ["explain", "describe", "what is"]):
        return Intent.EXPLAIN_RULE
    return None


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


def _extract_application(doc: spacy.tokens.Doc) -> Optional[str:
    """Extracts application name, which is often a noun phrase after a preposition."""
    # Prepositions that often precede an application name
    prepositions = {"for", "from", "on"}

    for chunk in doc.noun_chunks:
        # The 'root' of a noun chunk is its main word (e.g., 'Directory' in 'Active Directory').
        # The 'head' of that root is the word it's attached to (e.g., 'for').
        if chunk.root.head.lower_ in prepositions:
            return chunk.text
    return None
def _extract_attributes(text: str) -> List[str:
    """Extracts potential attribute names using regex (camelCase, snake_case, or quoted)."""
    # Regex with capturing groups for the content we want. Each part is a group.
    pattern = r"""
        \b([a-z]+[A-Z][a-zA-Z0-9_*)\b |      # camelCase (e.g., sAMAccountName)
        \b([a-z]+(?:_[a-z0-9+)+)\b |         # snake_case (e.g., employee_id)
        '([a-zA-Z0-9_.]+)' |                  # single-quoted (e.g., 'name')
        "([a-zA-Z0-9_.]+)"                    # double-quoted (e.g., "uid")
    """
    matches = re.findall(pattern, text, re.VERBOSE)
    # findall with groups returns a list of tuples, e.g., [('sAMAccountName', '', '', ''), ...]
    # We need to flatten the list and remove the empty strings.
    return [item for tpl in matches for item in tpl if item]


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

    intent = _extract_intent(text)
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
        intent=intent,
        rule_type=rule_type,
        application_name=application,
        source_attributes=source_attrs,
        identity_attributes=identity_attrs,
    )