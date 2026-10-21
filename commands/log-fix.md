---
description: Save a solved problem to the group's shared known-issues backlog (a GitHub issue on the plugin repo)
argument-hint: "[optional: short description of the problem]"
---

Record a problem that was just solved, so the next person who hits it finds the fix. Extra description from the user (may be empty): $ARGUMENTS

1. **Draft the entry from this conversation.** Use what actually happened; do not invent anything. Fill in:
   - **Code and version** (e.g. Q-Chem 6.3.1, SHARC 3.0.2, PySCF 2.x, TiDES commit) and the method or keyword involved.
   - **Symptom:** what the user saw (the key error line, or what looked wrong), in one or two sentences.
   - **Cause:** what was really going on. If it was not confirmed, say "suspected".
   - **Fix:** exactly what was changed (keywords, values, script lines), and how you know it worked.
   - **Source:** a manual section, forum or issue link, paper, or "found by us" with the date and job ID if any.
   - **Cost if missed:** e.g. "a 2–5 h job", "silently wrong widths".
   - **Where it belongs:** the skill (`eom-cc`, `sharc`, `tides`, `pyopencap`, `pace-slurm`, `method-selection`) or `troubleshooting/references/<code>.md`.

   Leave out anything private: usernames, account names, home-directory paths, unpublished numbers the user wouldn't want shared. Use placeholders such as `<account>`.

2. **Show the draft to the user** in a short block and ask: "Shall I post this to the group's fix backlog on GitHub?" Wait for a clear yes. Posting is public to everyone who can see the repo.

3. **On yes,** check `gh auth status`. If gh works, file it:
   ```bash
   gh issue create --repo oholtfrank3/AI-Skills --label known-issue \
     --title "[<code>] <short symptom>" --body-file <draft file>
   ```
   Write the body to a temporary file first. Give the user the issue link.

4. **If gh is not available or not logged in,** save the draft to `known-issue-draft.md` in the current folder. Then tell the user they can paste it into the "Known issue" form at https://github.com/oholtfrank3/AI-Skills/issues/new/choose.

Do not edit the plugin's own files from here. A maintainer folds the issues into the skills (`/compchem:merge-fixes`).
