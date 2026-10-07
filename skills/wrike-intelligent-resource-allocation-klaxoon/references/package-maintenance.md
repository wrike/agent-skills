# Skill package maintenance

Read this only when changing or distributing the skill package. Python 3.9 or newer is required.

- Keep every Python script standalone and limited to the standard library. Do not add relative imports or local module dependencies.
- Preserve the input contract or update its reference in the same change.
- Validate the complete package with site packages disabled:

  ```text
  <python> -I -S scripts/validate_skill.py
  ```

The packaged validator has no external dependencies. It checks Python 3.9 syntax, portable `SKILL.md` frontmatter, naming, TODO placeholders, local reference links, and all Python imports, then runs both compiler self-tests. The board test exercises single- and multi-option output, batch limits, links, symbols, counts, and file writing. The assignment test exercises complete-read checks, current-position parsing, option selection, moved task cards, valid overflow below option frames, attention-card exclusion, missing identifiers, update grouping, and file writing.
