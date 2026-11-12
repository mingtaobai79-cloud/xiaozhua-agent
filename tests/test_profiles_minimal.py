from components.profiles import (
    UdcPlatformProfile, StandardProductApplicationProfile,
    CustomerUdcApplicationProfile, ExtensionServiceProfile,
)

def test_profiles_are_separate_typed_objects():
    udc=UdcPlatformProfile(id="udc")
    standard=StandardProductApplicationProfile(id="bpm")
    customer=CustomerUdcApplicationProfile(id="app-1", application_id="app-1")
    ext=ExtensionServiceProfile(id="ext-1")
    assert udc.kind == "udc_platform"
    assert standard.kind == "standard_product_application"
    assert customer.kind == "customer_udc_application"
    assert ext.kind == "extension_service"
    assert standard.kind != udc.kind

def test_profile_serialization_preserves_evidence_and_status():
    p=CustomerUdcApplicationProfile(id="app-1", application_id="app-1", data_ids=["app-1"], status="FACT", evidence_refs=["nacos:app-1"])
    d=p.to_dict()
    assert d["application_id"] == "app-1"
    assert d["data_ids"] == ["app-1"]
    assert d["status"] == "FACT"
    assert d["evidence_refs"] == ["nacos:app-1"]
