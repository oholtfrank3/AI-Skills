# Getting started with the compchem plugin

For group members who have never used Claude Code. It takes about 15 minutes. Ask Owen if you get stuck.

## 1. What this is

Claude Code is an AI assistant that runs in a terminal (or in the Claude desktop app). It can read files, run commands and write inputs for you, and it asks before doing anything risky. The **compchem plugin** gives it the group's know-how: which method to use, how to set up Q-Chem, PySCF, TiDES, SHARC and pyopencap jobs, how PACE works, and the mistakes that have already cost us weeks.

You don't need to know the right keywords. Describe what you want in plain words.

## 2. Install Claude Code (on your own computer)

1. You need a Claude account with Claude Code access. Ask Owen or Prof. Kretchmer which account to use.
2. Install it. Pick one:
   - **Desktop app:** download Claude from <https://claude.ai/download>, open it, and use the **Code** tab.
   - **Terminal** (macOS / Linux / WSL):
     ```bash
     curl -fsSL https://claude.ai/install.sh | bash
     ```
     Then run `claude` in any folder and follow the login prompt.
3. Check it works: in a Claude session, type `hello`.

## 3. Install the plugin

In a Claude session, type:

```
/plugin install compchem --marketplace oholtfrank3/AI-Skills
```

If that fails on an older Claude Code, use these two commands instead:

```
/plugin marketplace add oholtfrank3/AI-Skills
/plugin install compchem@kretchmer-ai-skills
```

Then type `/compchem:start`. Claude should greet you and ask what you'd like to model.

## 4. Connecting to PACE

**Never start Claude on a PACE login node** (`login-phoenix-*`). It has killed people's whole login session, and login nodes are not for heavy work. There are two safe set-ups.

### Option A (recommended to start): Claude on your computer, commands sent to PACE over ssh

Claude runs on your laptop and sends each PACE command over one shared ssh connection. You do the Duo login once a day.

1. Open a normal terminal (not Claude) and start a shared connection that lasts 24 h. Replace `<gt-username>` with yours:
   ```bash
   ssh -fNM -S ~/.ssh/cm-pace -o ControlPersist=24h -o ServerAliveInterval=60 <gt-username>@login-phoenix.pace.gatech.edu
   ```
   Approve the Duo push.
2. Tell Claude at the start of a session: "Use `ssh -S ~/.ssh/cm-pace <gt-username>@login-phoenix.pace.gatech.edu` to run commands on PACE."
3. Rerun step 1 when Claude says the connection is gone (after ~24 h).

Claude will only run light commands on the login node (editing, `squeue`, `sbatch`). Calculations always go through Slurm.

### Option B (for long-running agents): Claude inside a Slurm job on a compute node

This is how the group's long-running agents work. Set it up with Owen the first time.

1. Submit a long, small job that just holds a compute node (example shape: 4 cores, 32 GB, up to 7 days; use the account and QOS your project uses):
   ```bash
   sbatch -J claude_agents -A <account> -q inferno -c 4 --mem=32G -t 7-00:00:00 --wrap="sleep infinity"
   ```
2. On the login node, start `tmux` (it keeps things alive if your laptop disconnects). Inside it, open a shell on the job's node:
   ```bash
   srun --jobid=<jobid> --overlap -n1 -c4 --mem=0 --pty bash
   ```
3. Run `claude` there. Slurm commands work from inside the job.

## 5. Using it

- **Start with `/compchem:start`** and describe your system and question in your own words. Claude asks one question at a time and then writes a short plan (`PLAN_<name>.md`). Nothing runs until you approve.
- **Something broke?** Paste the key error line or describe what looks wrong. Claude checks the group notes, the manuals and the forums before suggesting a fix.
- **Safety:** before Claude submits, cancels or changes a Slurm job, you get a prompt to approve or reject it. Read it, and say no if you're unsure.
- **Solved a problem?** Type `/compchem:log-fix`. Claude drafts a short note on what went wrong and how it was fixed, shows it to you, and (with your OK) adds it to the group's shared list, so the next person doesn't lose a day to it.

## 6. Good habits

- Check numbers before you put them in a talk or paper. Ask Claude "how sure are you, and what would check this?"
- Start every new kind of calculation with the small test case Claude suggests. It catches most setup mistakes in minutes.
- Claude can be wrong. If something sounds off, ask it to show where the advice comes from.
