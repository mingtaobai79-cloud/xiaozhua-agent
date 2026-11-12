import unittest
from core.evidence import Evidence, Result, Status
from components.runtime import RuntimeComponent
from components.integration import IntegrationComponent
from components.udc import UdcComponent, UdcRequest


def test_status_supports_all_report_states():
    assert {item.value for item in Status} == {"FACT", "OBSERVATION", "HYPOTHESIS", "UNVERIFIED", "BLOCKED", "DENIED", "UNAVAILABLE", "CONFLICT"}


def test_result_serializes_status_and_evidence_uniformly():
    evidence = Evidence(level=Status.FACT, source="fixture", locator="snapshot.json")
    result = Result(component="runtime", target="pod", status=Status.FACT, evidence=[evidence], snapshot={"pod": "udc"})
    payload = result.to_dict()
    assert payload["component"] == "runtime"
    assert payload["status"] == "FACT"
    assert payload["evidence"][0]["level"] == "FACT"
    assert payload["snapshot"]["pod"] == "udc"


def test_all_components_return_result_compatible_structures():
    reports = [RuntimeComponent().inspect("pod"), IntegrationComponent().inspect("sync"), UdcComponent().inspect("app")]
    assert all(isinstance(report, Result) for report in reports)
    assert all(set(("component", "target", "status", "evidence")).issubset(report) for report in reports)
    assert [report["status"] for report in reports] == ["UNVERIFIED"] * 3


def test_denied_and_unavailable_are_distinct_report_states():
    denied = UdcComponent().execute(UdcRequest(action="publish", target="demo"))
    unavailable = RuntimeComponent().inspect("pod")
    assert denied["status"] == "DENIED"
    assert unavailable["status"] == "UNVERIFIED"
    assert denied["evidence"][0]["level"] == "DENIED"

if __name__ == "__main__":
    unittest.main()

class _Collected(unittest.TestCase):
    def test_status_supports_all_report_states(self):
        globals()["test_status_supports_all_report_states"]()
    def test_result_serializes_status_and_evidence_uniformly(self):
        globals()["test_result_serializes_status_and_evidence_uniformly"]()
    def test_all_components_return_result_compatible_structures(self):
        globals()["test_all_components_return_result_compatible_structures"]()
    def test_denied_and_unavailable_are_distinct_report_states(self):
        globals()["test_denied_and_unavailable_are_distinct_report_states"]()

if __name__ == "__main__":
    unittest.main()


def test_result_has_uniform_evidence_boundary_fields():
    result = Result(
        component="udc",
        target="demo",
        status=Status.FACT,
        evidence=[Evidence(Status.FACT, "fixture", "audit.json")],
        verification_level="FIXTURE",
        environment="offline",
        application_id="app-1",
    )

    assert result["verification_level"] == "FIXTURE"
    assert result["environment"] == "offline"
    assert result["application_id"] == "app-1"
    assert result["facts"] == {}
    assert result["unverified"] == []
    assert result["conflicts"] == []
    assert result["limitations"] == []
    assert result["next_actions"] == []


def test_fixture_result_cannot_claim_live_status():
    result = Result(
        component="udc",
        target="demo",
        status="LIVE",
        evidence=[],
        verification_level="FIXTURE",
    )

    assert result["status"] == "UNVERIFIED"
    assert result["verification_level"] == "FIXTURE"
    assert result["conflicts"][0]["reason"] == "non-live evidence cannot claim LIVE status"
