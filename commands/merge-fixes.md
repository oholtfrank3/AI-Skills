---
description: Maintainers - fold open known-issue reports from GitHub into the skills and reference files
---

You are helping a maintainer of the compchem plugin. The current folder should be a checkout of the plugin repo (oholtfrank3/AI-Skills). Check that first, and stop if it isn't.

1. List the open issues labelled `known-issue`:
   `gh issue list --repo oholtfrank3/AI-Skills --label known-issue --state open --json number,title,body,url`
2. For each issue, decide where it belongs (the skill named in the issue, or `skills/troubleshooting/references/<code>.md` under "Known issues and fixes"). Also check that it doesn't duplicate or contradict an existing entry. A contradiction is worth flagging to the maintainer, not silently resolving.
3. Show the maintainer a short table: issue number → target file → one-line summary → add / merge with existing / needs more info. Wait for their OK.
4. On OK, edit the files. Use the existing style: bold lead-in, then symptom → cause → fix, with the source (issue URL and date). Keep entries short.
5. Run `claude plugin validate .`. Then propose a commit on a branch (not main) whose message lists the issue numbers. Commit, push and close the issues only after the maintainer says yes, closing each with a comment linking the commit.
