# UDC Construction Source Inventory

- status: FACT / STATIC
- network: disabled
- scope: UDC platform artifacts and decompiled construction/runtime sources; customer projects excluded

- inventoried files: 1696
- decompiled Java files: 1441

## Domain classification
- application: 257
- entity: 314
- generation: 22
- microflow: 542
- page: 306

## Root evidence
- `<USER_HOME>/...
- `<MAVEN_REPO>`

## Interpretation boundary

- This inventory is the source map for extracting construction rules.
- It does not yet claim that a path name equals a frontend action or a runtime call.
- Next pass reads targeted classes and frontend resources together, then links DTO → Controller → Service → metadata/DB/runtime.