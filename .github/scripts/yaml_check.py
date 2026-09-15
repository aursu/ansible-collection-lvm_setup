#!/usr/bin/env python3
"""Parse every YAML file in the collection, and fail on any that will not load.

This exists because of a specific escape. A botched line-based edit left an
orphaned fragment in roles/process_volumes/tasks/create_lv.yml:

    when:
      - debug_mode | default(false)
      - lv.mountpoint is defined
    | default(false)                 <- orphan
      - lv.mountpoint is defined     <- duplicate

That file is unparseable, and 1.3.0 shipped it to Galaxy anyway.

CI did detect it. ansible-lint reported ``load-failure[yaml]`` at
``create_lv.yml:79:3`` and exited 2 - and the lint job carries
``continue-on-error: true``, added because a dozen style violations would
otherwise have made every run red. So a file that cannot be parsed at all was
discarded alongside naming-convention warnings, and the build went green.

Nothing else was positioned to notice either: the unit tests exercise the Python
filters and never read a task file; ``ansible-playbook --syntax-check`` parses a
play and what it *statically* includes, and ``create_lv.yml`` is reached through
``include_tasks``, which is dynamic; and ``ansible-galaxy collection build``
copies files without parsing them.

So the first thing to object *audibly* was a live run against a real host, after
the partition and the volume group had already been created.

Hence this script rather than simply making the lint blocking. A file that cannot
be read is not a style opinion, and it should not share a gate with one: this
check is small, blocking, and has nothing to say about style, so the lint ratchet
can stay advisory without hiding the one class of failure it must never hide.

Usage::

    python .github/scripts/yaml_check.py [root]

Exit codes: ``0`` every file parsed, ``1`` at least one did not, ``2`` the check
itself could not run.
"""

import os
import sys

# Directories whose contents are not collection YAML and have their own tooling.
SKIP_DIRS = {".git", ".github", "tests", "__pycache__", ".pytest_cache", "dist"}

ON_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


def annotate(path, message):
    """Report a failure as a workflow annotation on Actions, plain text elsewhere."""
    if ON_ACTIONS:
        sys.stderr.write("::error file=%s::%s\n" % (path, message))
    else:
        sys.stderr.write("FAIL %s\n     %s\n" % (path, message))


def yaml_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith((".yml", ".yaml")):
                yield os.path.join(dirpath, name)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = argv[0] if argv else "."

    try:
        import yaml
    except ImportError:
        # Exit 2, not 1: "the check could not run" must not read the same as
        # "a file is broken". Ordering this step ahead of the toolchain
        # install is exactly how those two got confused once already.
        sys.stderr.write("PyYAML is required: pip install ansible-core\n")
        return 2

    checked = failed = 0
    for path in yaml_files(root):
        checked += 1
        try:
            with open(path, "r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            failed += 1
            # A YAMLError's str() spans several lines and names the position;
            # keep it whole, it is the useful part.
            annotate(path, str(exc).replace("\n", " "))
        except (IOError, OSError) as exc:
            failed += 1
            annotate(path, "could not be read: %s" % exc)

    if failed:
        sys.stderr.write("\n%d of %d YAML file(s) failed to parse.\n" % (failed, checked))
        return 1

    sys.stdout.write("All %d YAML files parse.\n" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
