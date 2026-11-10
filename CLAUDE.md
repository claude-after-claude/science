# science: guide for agents

This repo lists results that Claude instances worked out and that someone outside can check.
Public, under the claude-after-claude account. Read this before adding or changing anything.

## Layout

```
README.md                      human-facing index: one table row and one BibTeX entry per result
CLAUDE.md                      this file
results/YYYY-MM-<slug>/
    README.md                  the note (structure below)
    citation.bib               the BibTeX entry, identical to the one in the root README
    sessions/                  code and notes exactly as the instances that did the work left them
    verify/                    independent checks: separate code, comparison scripts, their outputs
```

## Bar for listing a result

All of these, or it does not go in the table.

1. **One-sentence statement** that a specialist could confirm or refute.
2. **Independent recomputation.** Code that shares nothing with the original reproduces the number or
   the object. "Reran the same script" does not count. Put the code and its output in `verify/`.
3. **You ran it yourself.** Rerun every search the note cites and keep the logs. Do not cite a count you
   have only seen in another instance's notes.
4. **Primary sources read.** List each source, how it was obtained, and what it says on the point, with
   a quote. A search snippet is not a reading. List what was not read.
5. **Honest status.** Use "not found in the sources read", never "new", "novel" or "first". If part of
   the result is known, say which part and where.
6. **A section on what could be wrong.** Software bugs, bounds that were argued and not proved,
   assumptions shared between the checks.

Results that turn out to be known stay out of the table. Mention them in the note they belong to.

## Structure of a note

Statement. Background and prior work. Method. Results. How it was checked. What could be wrong.
Sources read and not read. Provenance (which sessions did what, on what date). How to rerun. Corrections.

## Rules

- **Never edit files under `sessions/`.** They are the record. Put corrections beside them or in the
  note's Corrections section, dated.
- **Counts come from scripts.** Any number in a note must be reproducible by a command in the note.
- **Authors are the models that did the work**, written `Claude (<model>)`, for example
  `{{Claude (Fable 5.2)}}` in BibTeX. Add a model to the author list of an existing entry only if an
  instance of it contributed work that is in the folder. Humans are authors only if they reviewed the
  result; otherwise they go in Acknowledgements.
- **Corrections are appended**, with the date and what changed. If a result is retracted, strike the
  table row and keep the folder.
- **Session files may contain a model's remarks about itself.** Leave them. Do not add private paths,
  names of people other than those already acknowledged, or anything from Clément's research.
- **Commits** are made as `Claude after Claude <330195502+claude-after-claude@users.noreply.github.com>`
  and end with the signature the account uses:

  ```
  claude-after-claude (<model>)
  Claude-Session: <session link>
  ```

- After cloning: `git config core.hooksPath .githooks` (stops a commit that contains a secret).
- Pushing: a plain `git push` on Clément's machines authenticates as his own account and is refused.
  Use the account's token without printing it:
  `GH_TOKEN=$(gh auth token --user claude-after-claude) git -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main`
- Publishing here needs Clément's ok for the result, recorded with a session link in the commit that
  adds it. The two November 2026 results have it.

## Open leads recorded in the notes

Each note ends with loose ends the instances named. If you take one up, work in a new `sessions/`
subfolder, leave the earlier ones untouched, and add your check under `verify/`.
