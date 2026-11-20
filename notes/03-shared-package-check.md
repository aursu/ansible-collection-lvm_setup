# 03 — The package-name check comes from `aursu.general`

| | |
|---|---|
| Release | 1.6.0 (2026-11-20) |
| PR | `feature/shared-package-check` |
| Commits | `c9325b4` |

## What

`RequiredPackages` no longer has its own `_package_list`; it uses `PackageNames`
from `aursu.general`'s `plugins/plugin_utils/packages.py`.

## Why — the goal

The same rule — "a package name or a list of names, each a non-empty string" —
was needed in `aursu.dockerinstall` as well. Alexander's rule: logic that
appears in more than one collection moves to `aursu.general` and is used from
there. This collection already depended on `aursu.general`.

## How it works

`RequiredPackages.__init__` builds `PackageNames(value, name).names` for the base
list and for each filesystem's packages. The messages are the same text the
private method produced, so behaviour is unchanged.

## Where it is defined

| File | What |
|---|---|
| `plugins/plugin_utils/package_helpers.py` | imports `PackageNames`; `_package_list` removed |
| `galaxy.yml` | 1.6.0; `aursu.general >= 1.9.0` |
| `.github/workflows/test.yml` | installs `aursu.general==1.9.0` next to the collection before the unit tests |
| `.github/workflows/release.yml` | the same, in the release run's unit-test step |
| `CHANGELOG.md` | 1.6.0 |

## Rejected alternatives

- **Keeping the private copy.** Two rules for one thing drift apart.
- **Leaving CI without `aursu.general`.** `package_helpers` now imports it; the
  unit tests would fail at import.

## Verified by

All 107 unit tests pass unchanged against `aursu.general` 1.9.0 — including the
13 `required_packages` tests, whose expected messages were not edited.
`release_preflight.py --tag v1.6.0` passes.
