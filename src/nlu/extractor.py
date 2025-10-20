import re
from typing import List, Optional
from enum import Enum

import spacy
from pydantic import BaseModel, Field

from src.models.rules import RuleType

# Lazy-load the spaCy model so importing this module is cheap.
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
    intent: Optional[Intent] = Field(None, description="The user's primary goal.")
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
    if any(phrase in text_lower for phrase in ["explain", "describe", "what is"]):
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


def _extract_application(doc: "spacy.tokens.Doc") -> Optional[str]:
    """
    Extract application name: often the object of a preposition like
    'for <APP>', 'from <APP>', 'on <APP>'.
    """
    prepositions = {"for", "from", "on"}
    # Prefer prepositional objects (pobj) headed by a preposition we care about
    for token in doc:
        if token.dep_ == "pobj" and token.head.text.lower() in prepositions:
            # return the full noun chunk containing this token if possible
            for chunk in doc.noun_chunks:
                if token.i >= chunk.start and token.i < chunk.end:
                    return chunk.text
            return token.text
    # fallback: scan noun chunks whose head is a preposition
    for chunk in doc.noun_chunks:
        if chunk.root.head.text.lower() in prepositions:
            return chunk.text
    return None


# Precompile a more robust attribute pattern:
# - camelCase / Pascal with at least one uppercase transition
# - snake_case with at least one underscore
# - single or double quoted tokens (strip quotes later)
_ATTR_PATTERN = re.compile(
    r"""(?x)
    (?:\b[a-z]+[A-Z][A-Za-z0-9_]*\b)        # camelCase like sAMAccountName
    |
    (?:\b[a-z0-9]+(?:_[a-z0-9]+)+\b)         # snake_case like employee_id
    |
    (?:'([A-Za-z0-9_.]+)')                   # 'quoted'
    |
    (?:"([A-Za-z0-9_.]+)")                   # "quoted"
    """
)

def _extract_attributes(text: str) -> List[str]:
    """Extract potential attribute names (camelCase, snake_case, or quoted tokens)."""
    results: List[str] = []
    for match in _ATTR_PATTERN.finditer(text):
        s = match.group(0)
        # If matched from quoted groups, strip quotes via captured groups
        g1, g2 = match.group(1), match.group(2)
        if g1:
            results.append(g1)
        elif g2:
            results.append(g2)
        else:
            results.append(s)
    return results


def extract_entities(text: str) -> ExtractionResult:
    """Processes a natural language string to extract IIQ rule components."""
    nlp = get_nlp()
    doc = nlp(text)

    intent = _extract_intent(text)
    rule_type = _extract_rule_type(text)
    application = _extract_application(doc)
    attributes = _extract_attributes(text)

    source_attrs: List[str] = []
    identity_attrs: List[str] = []

    # Simple logic to differentiate attributes for BuildMap rules
    if rule_type == RuleType.BUILD_MAP and len(attributes) >= 2:
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
