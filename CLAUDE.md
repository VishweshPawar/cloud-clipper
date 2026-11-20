# CLAUDE.md — Working Rules

- **Spec before build**: before doing or building anything, write a spec, then walk through each step showing the key decisions and what I would default to. Don't build yet. State how I would verify. Enable needed tools and launch subagents as appropriate.
- Think carefully and read every file relevant to the task before changing anything.
- Make the smallest change that fully solves the problem.
- After a change, verify it by running or testing it. Never say it works without checking.
- Be clear and complete, without padding or repetition.
- If unsure, say so and ask one short question instead of guessing.
- Never delete files or run destructive commands without asking.
- Show me any command that downloads or modifies things before running it.
- Never read, search, or list files inside C:\claudepro\ghidra unless I specifically ask.