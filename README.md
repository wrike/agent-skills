# Wrike Agent Skills

Official Agent Skills for [Wrike](https://www.wrike.com), built to help AI
agents turn conversations, documents, and Wrike context into structured,
actionable work.

These skills equip any skills-compatible agent to work effectively with Wrike:
capturing work from meetings and briefs, keeping projects up to date, and
identifying risks across projects, programs, and portfolios.

These skills work with the Wrike MCP Server to securely access and update your
Wrike workspace.

## Installing

These skills work with agents that support the Agent Skills standard, including
Claude Code, OpenAI Codex, Cursor, and other compatible agents.

### npx skills

Install all available Wrike skills:

```sh
npx skills add wrike/agent-skills
```

Install a specific skill:

```sh
npx skills add wrike/agent-skills --skill wrike-meeting-sync
```

### Clone / Copy

You can also clone this repository and copy individual skill folders into your
agent’s skills directory:

```sh
git clone https://github.com/wrike/agent-skills.git

# Example: Claude Code
cp -r skills/wrike-meeting-sync ~/.claude/skills/

# Example: OpenAI Codex
cp -r skills/wrike-meeting-sync ~/.codex/skills/
```

## Skills

<!-- skills:start -->
| Skill | Useful for |
|---|---|
| `wrike-meeting-sync` | Turn meeting transcripts into clear notes and actionable Wrike updates. Capture decisions and action items, connect them to relevant Wrike work, and keep owners, dates, statuses, and details up to date. |
| `wrike-work-creation` | Turn ideas, briefs, and documents into ready-to-go Wrike work. Find and use relevant request forms and blueprints when available, or create the right work structure from scratch. |
<!-- skills:end -->

## How it works

Wrike Skills provide agents with workflow-specific instructions for getting
work done in Wrike. The skills handle the reasoning and workflow, while the
Wrike MCP Server provides access to your workspace and the tools needed to
find, create, and update work.

Install the skills you need to bring Wrike workflows directly into your AI
agent.
