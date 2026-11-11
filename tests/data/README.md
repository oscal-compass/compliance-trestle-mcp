# Test fixtures: where they came from

## NIST-derived OSCAL fixtures

`test-catalog.json` and `test-profile.json` are **modified excerpts** of the
OSCAL content NIST publishes at
[usnistgov/oscal-content](https://github.com/usnistgov/oscal-content):

| File | Derived from | How it was modified |
|---|---|---|
| `test-catalog.json` | `nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` | Trimmed to two controls, `ac-1` and `ac-2`. New document `uuid` and `last-modified`. |
| `test-profile.json` | `nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_PRIVACY-baseline_profile.json` | `imports[].href` rewritten to a workspace-relative path. New document `uuid` and `last-modified`. |

### Licensing

The upstream content is a work of the United States government, so it is in the
public domain in the United States, and NIST additionally waives copyright
worldwide through the
[CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
Copying, modifying and redistributing it — including in this Apache-2.0
repository — needs no permission and imposes no attribution requirement. See
[`LICENSE.md`](https://github.com/usnistgov/oscal-content/blob/main/LICENSE.md)
in the upstream repository.

### These are not authoritative copies

Each file still carries NIST's own attribution inside its OSCAL `metadata`
(publisher, creator, contact addresses, title, version), which is the honest
record of where the content came from. But the files have been cut down and
edited for testing, and CC0 asks that use of the work not imply endorsement by
NIST, so:

- Do not cite them as NIST content, or treat them as a source of control text.
  `test-catalog.json` keeps the title of the full SP 800-53 Rev 5.2.0 catalog
  while containing two of its controls.
- Fetch the current upstream file if you need the real thing. The version here
  was taken from an earlier snapshot and is not kept in step with upstream.

### Why they are bundled rather than fetched

So that the test suites need no network. `tests/e2e` previously resolved a
control source over HTTPS, which downloaded roughly 10 MB from a third party on
every run and failed whenever that host was unreachable. The fixtures being
local is what lets the end-to-end job run in CI at no cost beyond runner time.

## Task fixtures

`task/csv-to-oscal-cd/` and `task/csv-to-oscal-mc/` are written for this
repository; nothing in them is third-party content. Their `Profile_Source` and
resource columns use `trestle://` or workspace-relative hrefs, so the tasks they
drive resolve everything inside the workspace. Keep it that way — a URL in one
of these columns puts the test suite back on the network.
