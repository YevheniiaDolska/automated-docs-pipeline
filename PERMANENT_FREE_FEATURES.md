---
title: "Permanent free features and licensing operations"
description: "Operator guide for permanent free feature grants, capability pack keys, and license plan bypass gating in the bundle pipeline."
content_type: reference
last_reviewed: "2026-07-04"
---

# Permanent free features and licensing operations

This note is internal operator documentation (not client docs). It covers
four licensing capabilities in the bundle pipeline: permanent free grants,
the signing keypair, auto-generated capability pack keys, and env bypass
gating.

## 1. Permanent free feature grants

You can grant a client selected features or protocols permanently at no charge.
These grants live inside the signed license JWT (`free_features` and
`free_protocols` claims) and survive:

- license expiry (past grace) and degradation to Community Mode,
- pilot trial expiry,
- server-side revocation,
- restarts and redeployments (grants are re-embedded on every bundle rebuild
  from the client profile).

They do NOT survive bundle cloning to another repository path (repo binding
still degrades a moved bundle to plain community) or a forged/tampered token
(signature verification runs before grants are read).

### How to grant

Wizard: `python3 scripts/onboard_client.py` (or `provision_client_repo.py
--interactive`) asks:

- `Permanent free features (comma-separated, kept forever even without payment)`
- `Permanent free protocols (comma-separated, e.g. rest)`

Profile YAML equivalent:

```yaml
licensing:
  plan: professional
  days: 365
  max_docs: 0
  permanent_free_features:
    - seo_geo_scoring
    - gap_detection_code
  permanent_free_protocols:
    - rest
```

Manual JWT generation:

```bash
python3 build/generate_license.py --client-id acme --plan professional \
  --days 365 --free-features seo_geo_scoring,gap_detection_code \
  --free-protocols rest --output docsops/license.jwt
```

Valid feature names are the keys of `PLAN_FEATURES` in
`scripts/license_gate.py`. Valid protocols: rest, graphql, grpc, asyncapi,
websocket.

### Behavior details

- While the license is valid, grants are force-enabled even if the plan tier
  or a `features` restriction would disable them.
- After expiry past grace, `validate()` returns Community Mode with the
  granted features/protocols still enabled (`LicenseInfo.free_features`).
- Pilot-expiry proprietary-asset cleanup is skipped entirely when grants
  exist, so the scripts that power granted features are never deleted.

## 2. Signing keypair requirement

Bundles only get a signed license when
`docsops/keys/veriops-licensing.key` exists in this (vendor) repository.
Generate it once:

```bash
python3 build/generate_license.py --generate-keypair \
  --client-id bootstrap --plan pilot --days 1 --output /tmp/bootstrap.jwt
```

The private key is gitignored; the public key ships in every bundle so the
client-side gate verifies signatures offline. Without the keypair, bundle
builds print a WARNING and the client would run in Community Mode.

## 3. Capability pack keys are auto-generated per client

Bundle builds no longer require you to pre-set `VERIOPS_LICENSE_KEY`. When the
profile has `auto_generate_capability_pack: true` (the default) and no key is
configured, the build:

1. Generates a per-client key (`VDOC-<PLAN>-<client-id>-<hex>`), or reuses the
   existing one so rebuilds/upgrades do not rotate keys.
1. Stores it vendor-side at `generated/client_keys/<client-id>.license-key.txt`
   (gitignored; never shipped in the bundle).
1. Encrypts the capability pack into `docsops/.capability_pack.enc`.

Deliver the key to the client out-of-band. The client sets
`VERIOPS_LICENSE_KEY` in `.env.docsops.local`; the runtime resolves the client
id automatically from `BUNDLE_INFO.yml` (or `VERIOPS_CLIENT_ID` env). Without
the key the pack degrades to baseline scoring weights -- nothing breaks.

## 4. VERIOPS_LICENSE_PLAN env bypass is now gated

The `VERIOPS_LICENSE_PLAN` env override (skip JWT validation) is honored only:

- inside this vendor repository (detected via `build/generate_license.py`), or
- in bundles that ship a `docsops/.dev_mode` marker
  (`build_free_enterprise_bundle.py` writes it automatically).

Licensed client bundles do not ship the marker, so clients cannot
self-upgrade to enterprise by setting an environment variable.

## Next steps

- [Pricing cheat sheet](PRICING_CHEATSHEET_RU.md)
- [Security operations](SECURITY_OPERATIONS.md)
