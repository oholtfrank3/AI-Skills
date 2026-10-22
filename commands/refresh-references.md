---
description: Maintainers - re-research the troubleshooting reference files (docs, forums, versions) and propose updates on a branch
argument-hint: "[optional: one code, e.g. sharc; default all]"
---

Refresh the plugin's per-code reference files so their documentation links, versions and known issues stay current. Run this from a checkout of the plugin repo (oholtfrank3/AI-Skills); check that first. Scope from the user (empty = all files): $ARGUMENTS

1. **List the files** in `skills/troubleshooting/references/*.md` and the "Last researched" date of each. Refresh those older than about 5 months, or the one named in the scope.

2. **For each file, research what changed since its date** (WebSearch / WebFetch; one subagent per file if several are due, run in parallel):
   - New releases of the code, and changed defaults or keywords that affect the file's recipes.
   - Links that now 404 or moved, which should be replaced.
   - New or newly closed GitHub issues and forum threads matching the file's topics. Closed issues may turn "known issue" entries into "fixed in vX".
   - Anything in the file that newer sources contradict.

   Follow the file's existing format. Only add entries from sources actually read, never invent a URL, and keep quotes under 15 words. Mark uncertain items "(unverified)". Update "Last researched".

3. **Check the skills too.** If a refresh changes advice that a skill repeats (e.g. a version-specific bug in `sharc` or `eom-cc`), note the skill line that should change, but do not edit skills in this command.

4. **Put the changes on a new branch** `refresh-references-<date>`, run `claude plugin validate .`, and commit with a summary per file: new entries, fixed or removed entries, changed versions, dead links replaced, and skill lines that may need updating.

5. **Ask before pushing.** Then push the branch and open a pull request against `main`, so a person reviews it before it reaches users. In an unattended (scheduled) run, push the branch and open the pull request without asking: that review is the safeguard. Never push to `main` directly.
