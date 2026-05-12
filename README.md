# myskill

Personal Codex skills managed in Git.

## Layout

- `skills/`: tracked skill directories. Each skill should contain a `SKILL.md`.
- `scripts/sync-to-codex.sh`: installs the tracked skills into `~/.codex/skills`.
- `scripts/sync-from-codex.sh`: refreshes this repository from `~/.codex/skills`.

## Install into Codex

```sh
./scripts/sync-to-codex.sh
```

## Refresh from local Codex skills

```sh
./scripts/sync-from-codex.sh
```

## Publish to GitHub

Create an empty GitHub repository, then run:

```sh
git remote add origin git@github.com:<user>/<repo>.git
git branch -M main
git add .
git commit -m "Track Codex skills"
git push -u origin main
```
