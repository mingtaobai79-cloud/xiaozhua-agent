# UDC design-time Artifact availability evidence

## Scope

This check targets the requested UDC design-time modules and distinguishes Maven declarations from physical artifacts.

## Parent POM facts

Source:

```text
<MAVEN_REPO>/com/seeyon/udc-parent/5.3.517/udc-parent-5.3.517.pom
```

Resolved properties:

```text
udc.version = 5.3.517
boot-extend.version = 5.3.318
```

The dependency declarations resolve to:

| module | exact coordinate | declared version | local artifact |
|---|---|---:|---|
| udc-biz | `com.seeyon:udc-biz` | `5.3.517` | MISSING |
| udc-web | `com.seeyon:udc-web` | `5.3.517` | MISSING |
| udc-assemble | `com.seeyon:udc-assemble` | `5.3.517` | MISSING |
| udc-cicd | `com.seeyon:udc-cicd` | `5.3.517` | MISSING |
| udc-upgrade | `com.seeyon:udc-upgrade` | `5.3.517` | MISSING |
| udc-extend | `com.seeyon:udc-extend` | `5.3.517` | MISSING |
| udc-starter-autocode | `com.seeyon:udc-starter-autocode` | `5.3.517` | MISSING |

`udc-biz` is declared with `${udc.version}` in the parent POM; the earlier broad parser output that associated it with `boot-extend.version` was a context-window parsing error, not the actual dependency block.

## Repository checks

Checked physical paths:

```text
<MAVEN_REPO>
<EVIDENCE_ROOT>
<USER_HOME>/...
<USER_HOME>/...
<USER_HOME>/...
```

No requested UDC design-time JAR was found in `<MAVEN_REPO>`, `<EVIDENCE_ROOT>`, or Desktop. A targeted scan of the user home found a real downloaded generated Java source file, but it is a customer/generated artifact and not one of the missing UDC design-time modules:

```text
<USER_HOME>/...com_xiaozhua_9000000000000000001_dto_HetongdanganDto.java
```

Its presence proves a generated-source delivery artifact exists locally, but does not prove which generator produced it or connect it to `udcEntityPost`. The only matching files under Temp are pytest-generated fixtures, not product artifacts:

```text
.../pytest-*/test_cli_artifact_inventory_wr0/com/seeyon/udc-web/5.3.517/udc-web-5.3.517.jar
.../pytest-*/test_cli_artifact_inventory_wr0/com/seeyon/udc-web/5.3.517/udc-web-5.3.517.pom
```

These are test fixtures and are excluded from evidence.

## Available same-version UDC artifacts

Present under `<MAVEN_REPO>/com/seeyon`:

```text
udc-common-5.3.517.jar
udc-facade-5.3.517.jar
udc-starter-runtime-5.3.517.jar
udc-starter-lowcode-5.3.517.jar
udc-starter-dataflow-5.3.517.jar
udc-starter-customplan-5.3.517.jar
```

## Conclusion

The local Maven repository does not contain the requested 5.3.517 design-time modules. Parent POM declarations are not treated as implementation evidence. The missing design-time artifacts are the current blocker for proving `EntityAppService.create(EntityDto)` implementation and code-generation trigger from local artifacts.

Status: `BLOCKED / UNVERIFIED` for design-time Artifact availability.
