# FILE: source_governance/website_onboarding_trust_classifier.py
# MODULE: MODULE-002-03 — Website Onboarding & Trust Classifier
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Validate candidate source sites and classify them into trust states.
# EXPORTS: Website onboarding and trust classification stub.
# DEPENDS_ON: platform/observability.py.
# ACCEPTANCE_CRITERIA:
#   - Candidate source validation remains explicit before eligibility is granted.
#   - Trust classification outcomes remain separate from search execution.
# HUMAN_REVIEW: Yes — external integration and trust decision.

from __future__ import annotations

import re
from urllib.parse import urlparse


_DOMAIN_PATTERN = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


def _normalize_domain(raw_domain: str) -> str:
	value = (raw_domain or "").strip().lower()
	if value.startswith("http://") or value.startswith("https://"):
		parsed = urlparse(value)
		return parsed.netloc.lower()
	return value


def _validate_domain_and_https(domain: str, metadata: dict) -> tuple[bool, list[str], bool]:
	errors: list[str] = []
	normalized_domain = _normalize_domain(domain)

	if not normalized_domain:
		errors.append("domain_missing")
	elif not _DOMAIN_PATTERN.fullmatch(normalized_domain):
		errors.append("domain_format_invalid")

	https_reachable = bool(metadata.get("https_reachable", False))
	if not https_reachable:
		errors.append("https_check_failed")

	is_valid = len(errors) == 0
	return is_valid, errors, https_reachable


def _classify_trust(metadata: dict) -> str:
	signal = str(metadata.get("trust_signal", "")).strip().lower()
	if signal in {
		"blocked",
		"bad",
		"bad-rated",
		"blacklisted",
		"bloqueado",
		"ruim",
		"negativo",
		"lista negra",
		"lista_negra",
	}:
		return "blocked"
	if signal in {
		"allowed",
		"good",
		"trusted",
		"approved",
		"permitido",
		"confiavel",
		"confiável",
		"aprovado",
	}:
		return "allowed"
	return "review_required"


def evaluate_website_onboarding(
	onboarding_request: dict,
) -> dict[str, object]:
	"""
	Validate onboarding request and classify trust state.

	Input contract:
	  onboarding_request = {
	    "domain": str,
	    "label": str,
	    "metadata": {
	      "https_reachable": bool,
	      "trust_signal": str,
	    }
	  }
"""
	domain = str(onboarding_request.get("domain") or "")
	label = str(onboarding_request.get("label") or "")
	metadata = onboarding_request.get("metadata")
	if not isinstance(metadata, dict):
		metadata = {}

	normalized_domain = _normalize_domain(domain)
	is_valid, validation_errors, https_reachable = _validate_domain_and_https(
		domain=domain,
		metadata=metadata,
	)

	if not is_valid:
		trust_status = "blocked"
		activation_eligibility = False
	else:
		trust_status = _classify_trust(metadata)
		activation_eligibility = trust_status in {"allowed", "review_required"}

	return {
		"site_validation_result": {
			"domain": normalized_domain,
			"label": label,
			"is_valid": is_valid,
			"https_reachable": https_reachable,
			"errors": validation_errors,
		},
		"trust_classification_status": trust_status,
		"activation_eligibility": activation_eligibility,
	}
