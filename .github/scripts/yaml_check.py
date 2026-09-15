#!/usr/bin/env python3
"""Parse every YAML file in the collection, and fail on any that will not load.

This exists because of a specific escape. A botched line-based edit left an
orphaned fragment in roles/process_volumes/tasks/create_lv.yml:

    when:
      - debug_mode | default(false)
      - lv.mountpoint is defined
    | default(false)                 <- orphan
      - lv.mountpoint is defined     <- duplicate

That file is unparseable, and 1.3.0 shipped it to Galaxy anyway. Nothing in CI
was in a position to notice:

* the unit tests exercise the Python filters, and never read a task file;
* ``ansible-playbook --syntax-check`` parses a play and what it *statically*
  includes, and ``create_lv.yml`` is reached through ``include_tasks``, which is
  dynamic - so it is not read until the task actually runs;
* ``ansible-galaxy collection build`` copies files without parsing them.

So the first thing to object was a live run against a real host, after the
partition and the volume group had already been created. A YAML error is the
cheapest possible defect to detect and one of the more expensive to discover
half-way through provisioning a disk.

Usage::

    python .github/scripts/yaml_check.py [root]

Exit codes: ``0`` every file parsed, ``1`` at least one did not.
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
        sys.stderr.write("PyYAML is required: pip install ansible-core\n")
        return 1

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
