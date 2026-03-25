# FILE: tests/unit/source_governance/test_website_onboarding_trust_classifier.py
# MODULE: MODULE-002-03 — Website Onboarding & Trust Classifier
# EPIC: EPIC-002 — Brand Handling & Source Trust
# RESPONSIBILITY: Reserve unit tests for onboarding and trust-classification acceptance criteria.
# EXPORTS: Unit test stub.
# DEPENDS_ON: source_governance/website_onboarding_trust_classifier.py.
# ACCEPTANCE_CRITERIA:
#   - Candidate validation and trust outcomes remain testable from this unit boundary.
#   - Eligibility is not implicitly granted by test setup.
# HUMAN_REVIEW: No.

from source_governance.website_onboarding_trust_classifier import evaluate_website_onboarding


def test_ac1_domain_and_https_checks_execute_for_each_request() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "example.com",
			"label": "Example",
			"metadata": {"https_reachable": True, "trust_signal": "trusted"},
		}
	)

	validation = result["site_validation_result"]
	assert validation["domain"] == "example.com"
	assert validation["is_valid"] is True
	assert validation["https_reachable"] is True


def test_ac1_invalid_domain_fails_validation() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "bad domain",
			"label": "Bad",
			"metadata": {"https_reachable": True, "trust_signal": "trusted"},
		}
	)

	validation = result["site_validation_result"]
	assert validation["is_valid"] is False
	assert "domain_format_invalid" in validation["errors"]


def test_ac1_https_failure_fails_validation() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "example.com",
			"label": "Example",
			"metadata": {"https_reachable": False, "trust_signal": "trusted"},
		}
	)

	validation = result["site_validation_result"]
	assert validation["is_valid"] is False
	assert "https_check_failed" in validation["errors"]


def test_ac2_trust_classification_returns_allowed() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "allowed-site.com",
			"label": "Allowed",
			"metadata": {"https_reachable": True, "trust_signal": "allowed"},
		}
	)

	assert result["trust_classification_status"] == "allowed"


def test_ac2_trust_classification_returns_review_required() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "unknown-site.com",
			"label": "Unknown",
			"metadata": {"https_reachable": True, "trust_signal": "unknown"},
		}
	)

	assert result["trust_classification_status"] == "review_required"


def test_ac2_trust_classification_returns_blocked() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "blocked-site.com",
			"label": "Blocked",
			"metadata": {"https_reachable": True, "trust_signal": "blocked"},
		}
	)

	assert result["trust_classification_status"] == "blocked"


def test_trust_classification_accepts_portuguese_allowed_signal() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "site-br.com",
			"label": "Confiável",
			"metadata": {"https_reachable": True, "trust_signal": "confiável"},
		}
	)

	assert result["trust_classification_status"] == "allowed"


def test_trust_classification_accepts_portuguese_blocked_signal() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "site-br-bad.com",
			"label": "Bloqueado",
			"metadata": {"https_reachable": True, "trust_signal": "bloqueado"},
		}
	)

	assert result["trust_classification_status"] == "blocked"


def test_ac3_failed_onboarding_prevents_activation() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "not a domain",
			"label": "Invalid",
			"metadata": {"https_reachable": False, "trust_signal": "allowed"},
		}
	)

	assert result["site_validation_result"]["is_valid"] is False
	assert result["activation_eligibility"] is False


def test_ac3_blocked_classification_prevents_activation() -> None:
	result = evaluate_website_onboarding(
		{
			"domain": "valid-site.com",
			"label": "Valid but blocked",
			"metadata": {"https_reachable": True, "trust_signal": "blocked"},
		}
	)

	assert result["site_validation_result"]["is_valid"] is True
	assert result["trust_classification_status"] == "blocked"
	assert result["activation_eligibility"] is False
