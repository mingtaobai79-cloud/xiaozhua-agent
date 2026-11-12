import json
from pathlib import Path
class UdcVersionRegistry:
    def __init__(self, root): self.root=Path(root)
    def resolve(self, version):
        try:
            data=json.loads((self.root/"udc_version_samples_manifest.json").read_text(encoding="utf-8"))
            if version in data.get("versions", []): return {"status":"FACT","version":version}
        except (OSError,json.JSONDecodeError): pass
        return {"status":"UNVERIFIED","version":version}
