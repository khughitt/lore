## Design & Plan Docs

<!-- rule:ba23ff2fa67041158b9e1df90e9c9440 begin -->
- Where design specs, plans, briefs and handoffs go, and whether they are committed, is the profile's call: the session line's `design docs:` clause names the value or the directory, and the profile's text says the rest. The repository's own instructions override it, and the hook that guards staging names both.
<!-- rule:ba23ff2fa67041158b9e1df90e9c9440 end -->
<!-- rule:30ba737331374ada84282fe41f0faebb begin -->
- A code repository's `docs/` holds reference documents: each describes current behaviour, is named for its subject rather than dated, and is updated by the change that alters that behaviour. A design spec is a decision record, not a reference document; it becomes one only by being rewritten as one, never by being left in place. Which specs a repository rewrites is filed by that project as its own task when it next changes the subsystem they describe, never done as a side task of other work.
<!-- rule:30ba737331374ada84282fe41f0faebb end -->
<!-- rule:fea3f0aa833045f6a40ab83e4932bb6f begin -->
- Verify document status against the code before relying on it; update it and related docs when work lands.
<!-- rule:fea3f0aa833045f6a40ab83e4932bb6f end -->

<!-- rule:e1248095a0c74dd181cbc622c9a3b80b begin -->
- For tracked tasks, file cited documents as explicit task references and declare
  expected outputs, following the tasks skill. On pickup, read the inventory's
  required entries in their listed order before starting. The task's spec and plan
  fields name its governing documents; ordinary references do not acquire those
  workflow roles, and source remains provenance rather than a reading obligation.
  A reference locates current content; reviews and evidence still pin exact revisions.
<!-- rule:e1248095a0c74dd181cbc622c9a3b80b end -->
