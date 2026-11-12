import json
from pathlib import Path
class UdcOperationCatalog:
    def __init__(self, root): self.root=Path(root)
    def summary(self):
        result={"status":"UNVERIFIED","frontend_unique_calls":0,"backend_endpoints":0}
        try:
            front=json.loads((self.root/"udc_frontend_core_api_mapping.json").read_text(encoding="utf-8"))
            back=json.loads((self.root/"udc_web_controller_contracts.json").read_text(encoding="utf-8"))
            result.update(status="FACT", frontend_unique_calls=front.get("counts",{}).get("unique_calls",0), backend_endpoints=back.get("endpoint_count",0))
        except (OSError,json.JSONDecodeError): pass
        return result
