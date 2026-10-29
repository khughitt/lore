## Profiles

<!-- rule:1d70a6a4c5e842579156e56e9be27f5f begin -->
Every checkout has a profile — `personal`, `work`, `external`, or one the user
defined — that carries the instructions and settings that differ between
kinds of project. Your session starts with a `profile:` line followed by the
profile's instructions; if it did not, run `ops-profile session` and read
its output before any other work — the profile says what to read and do
before touching a repository. Later layers win: core, then the profile, then
this repository's own instructions, then the user in the session.
<!-- rule:1d70a6a4c5e842579156e56e9be27f5f end -->
