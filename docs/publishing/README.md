# Complete IntelliVest workspace publication

This repository includes the application and the complete Phase 7–10 research workspace. Local environment credentials, dependency installations, Python caches, OS files and database storage are excluded.

Some original research CSVs exceed GitHub's regular-Git per-file size limit. They are stored as deterministic, lossless `.csv.gz` files alongside their original paths. Every decompressed SHA256 was verified against the source workspace. Original research manifests and reports remain unchanged.

Before running any research replay or integrity check, restore the original CSV bytes:

```sh
python3 scripts/restore_research_artifacts.py
```

To verify archives without writing original CSVs:

```sh
python3 scripts/restore_research_artifacts.py --verify
```

The restored large CSV paths are Git-ignored to prevent accidentally committing files over GitHub's limit. `compressed_artifacts.json` records original sizes, original SHA256 and archive SHA256. `workspace_manifest.json` inventories every source-workspace file included in this publication. The source workspace's original `.gitignore` is retained as `workspace.gitignore`; the repository version adds only the restored-artifact ignore rules.

Research package entry points:

- [Phase 10 final report](../../research/results/phase10-2026-10-25/PHASE10_FINAL_REPORT.md)
- [Phase 10 conference draft](../../research/results/phase10-2026-10-25/PHASE10_CONFERENCE_DRAFT.md)
- [Phase 10 reproduction instructions](../../research/results/phase10-2026-10-25/README.md)
- [Phase 9 final report](../../research/results/phase9-2026-10-25/PHASE9_FINAL_REPORT.md)

The existing GitHub repository history and files present only on GitHub are preserved. The unrelated home-directory Git repository and the original local workspace are unchanged by publication.
