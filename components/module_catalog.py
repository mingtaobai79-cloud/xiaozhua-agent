from __future__ import annotations

from typing import Any


MODULES = (
    {"id": "udc", "kind": "udc_platform", "status": "FACT", "verification_level": "STATIC"},
    {"id": "standard-product", "kind": "standard_product_application", "status": "FACT", "verification_level": "STATIC"},
    {"id": "spi", "kind": "spi", "status": "FACT", "verification_level": "STATIC_CONTRACT"},
    {"id": "integration", "kind": "integration", "status": "PARTIALLY_VERIFIED", "verification_level": "SNAPSHOT_ONLY"},
    {"id": "runtime", "kind": "runtime", "status": "PARTIALLY_VERIFIED", "verification_level": "LIVE_READ_ONLY"},
)


RELATIONS = (
    {"source": "udc", "type": "generates", "target": "customer-udc-application", "evidence": "UDC generation boundary; customer details query-on-demand"},
    {"source": "customer-udc-application", "type": "calls", "target": "standard-product", "evidence": "requires exact source/call-site evidence; relation not yet closed"},
    {"source": "customer-extension", "type": "uses", "target": "spi", "evidence": "requires exact dependency plus call-site evidence; relation not yet closed"},
    {"source": "customer-extension", "type": "integrates-with", "target": "integration", "evidence": "requires exact adapter/call-site evidence"},
    {"source": "runtime", "type": "hosts-observes", "target": "udc", "evidence": "Pod/Nacos/storage/log runtime evidence"},
    {"source": "runtime", "type": "hosts-observes", "target": "standard-product", "evidence": "Pod/Nacos/storage/log runtime evidence"},
    {"source": "runtime", "type": "hosts-observes", "target": "spi", "evidence": "deployment/config evidence required"},
    {"source": "runtime", "type": "hosts-observes", "target": "integration", "evidence": "deployment/config/log evidence required"},
)


def build_module_catalog() -> dict[str, Any]:
    return {
        "schema_version": "module-catalog.v1",
        "status": "PARTIALLY_VERIFIED",
        "mode": "offline",
        "network": "disabled",
        "modules": [dict(item) for item in MODULES],
        "relations": [dict(item) for item in RELATIONS],
        "retention_policy": {
            "customer_business_detail": "QUERY_ON_DEMAND_NOT_DURABLE",
            "durable_scope": ["platform mechanisms", "standard contracts", "SPI contracts", "integration/runtime architecture", "artifact/version/evidence rules"],
        },
        "limitations": [
            "Relations are not ownership; each module remains independent.",
            "Standard Product Application and SPI remain separate modules from UDC.",
            "Customer entity/page/microflow/table/ext inventories are excluded from this catalog.",
            "A relation without an exact locator remains a declared dependency to verify, not a FACT of runtime invocation.",
        ],
    }
