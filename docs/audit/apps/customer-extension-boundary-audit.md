# Customer Extension Boundary Audit

- status: FACT / STATIC
- network: disabled
- scope: boundary-only; business inventories excluded

## Findings

- All existing generated application projects with @BootApp(... udcApp=true) are classified as customer UDC application/extension samples, not UDC Platform Core.
- UDC references in customer projects are static imports/configuration evidence; they do not prove runtime loading or invocation.
- BPM references found in one customer project are customer-to-standard-product candidate evidence; concrete call contracts and runtime execution remain unverified.
- No SPI relation is advanced from these scans without an exact SPI dependency, FQCN, call site, and runtime loading evidence.
- The scan retains architectural signals only and excludes customer entity/page/microflow/table/business inventories from durable evidence.

## Project signal summary

| project | exists | text files | UDC BootApp | UDC refs | BPM refs | SPI refs | integration refs |
|---|---:|---:|---:|---:|---:|---:|---:|
| `datamigration9000000000000000001` | True | 97 | 1 | 0 | 0 | 0 | 5 |
| `datamigration9000000000000000001` | True | 80 | 2 | 0 | 0 | 0 | 5 |
| `sanfangricheng7417152852034669760` | True | 64 | 2 | 0 | 0 | 0 | 5 |
| `xiangmuguanli9000000000000000001` | True | 109 | 2 | 3 | 2 | 0 | 11 |
| `yuexin-cat` | True | 6 | 0 | 0 | 0 | 0 | 0 |

## Evidence boundary

- FACT: static source/configuration signals only.
- UNVERIFIED: runtime loading, live invocation, SPI relation, frontend contract.
- Excluded: customer-specific entities, pages, microflows, tables, business rules, and endpoint inventories.
