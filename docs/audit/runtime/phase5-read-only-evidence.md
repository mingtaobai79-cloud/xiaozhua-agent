# Phase 5 Read-only Runtime Evidence

- Environment/context/namespace: `test2` / `low-code` / `low-code`
- Application: `app9000000000000000001`
- Writes performed: `0`

## Live facts

- Nacos is ready; seven expected data IDs return HTTP 200 and retain the stored hashes.
- Customer application Deployment exists with image tag `...9000000000000000001-1.0.1884`, but desired/ready replicas and endpoints are all zero. This is deployment metadata, not a running application.
- UDC Platform is a separate Deployment named `udc`, image tag `udc:5.3.477`; it is not merged into the customer application profile.
- Ingress `lowcode-test.客户方.com/service/(.*)` routes through `ctp-webapi-gateway`; target request success is not proven because the customer application has no live endpoint.
- MySQL authentication succeeded with SELECT-only access. Platform, standard-product, and customer schemas were distinguished; customer business inventories are not retained.

## Blocked

- Redis AUTH/PING timed out; no cache-key claim is made.
- Pod logs and runtime JAR hashes are unavailable because the target Deployment is scaled to zero.
- Image digest remains unverified; an image tag is not a content hash.

No secret, token, credential value, private key, or kubeconfig content is persisted.

## Retention correction

Customer-specific entity/page/microflow/table/controller inventories are excluded from durable facts and are queried only for a concrete customer incident or delivery task.
