# Client intake questionnaire (Google Form source)

Use two separate forms:

1. Pilot intake form
1. Full implementation intake form

Do not send technical/internal operator questions to clients.

## Pilot intake form (short)

Ask only:

1. Company legal name
1. Product name
1. Primary docs owner email
1. Technical fallback contact email
1. Weekly schedule confirmation:
   - default is Monday, 10:00 local client time
   - timezone auto-detected from host
1. Required documentation languages (multi-select):
   - English (always on)
   - Plus any required locales (for example: German, Spanish, French, Japanese)
1. Client confirms pilot scope:
   - pilot only
   - no PR auto-fix/automerge
   - no Ask AI runtime add-on unless separately purchased
   - no external mock provider setup unless explicitly requested

## Full implementation intake form

Ask only:

1. Company legal name
1. Product name
1. Primary docs owner email
1. Technical fallback contact email
1. Docs URL (production), if already exists
1. Required documentation languages (multi-select):
   - English (always on)
   - Plus any required locales (for example: German, Spanish, French, Japanese)
1. Optional integrations needed now:
   - Algolia
   - TestRail
   - Zephyr
   - Ask AI runtime add-on (paid add-on)
1. Scheduler OS:
   - Linux
   - Windows
   - macOS
1. Any compliance constraints:
   - strict-local only
   - no external data egress
   - custom security policy requirements

## Operator-only notes (not for client form)

1. `client_id` slug can be auto-generated from company name + product name.
1. Path discovery (`docs/api/sdk`) should be auto-detected during bootstrap.
1. Glossary, knowledge extraction, retrieval prep, and verification are enabled by plan/policy defaults.
1. Weekly schedule defaults to Monday 10:00 local time unless overridden by operator.
1. Ask AI runtime is a paid add-on and should not be enabled by default in SaaS bundles.
