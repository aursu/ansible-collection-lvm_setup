# Development notes — aursu.lvm_setup

One note per change: what it is, why it was made, how it works, where each part
is defined, and the alternatives that lost. Numbered in the order the changes
landed. Notes start with 1.4.0; earlier history is in `CHANGELOG.md`.
Not part of the published collection (`build_ignore`).

| # | Release | Subject |
|---|---|---|
| [01](01-pvs-pinning.md) | 1.4.0 | `pvs:` pins an LV to named PVs; free space counted on them |
| [02](02-role-packages.md) | 1.5.0 | Each role installs the packages it calls; filter `required_packages` |
| [03](03-shared-package-check.md) | 1.6.0 | The package-name check comes from `aursu.general` |
