# Public repository checklist

- [ ] Confirm the right to publish inherited source under AGPL-3.0-or-later and correct any copyright attribution requiring a named rights holder.
- [ ] Include the standard GNU AGPL v3 text, AGPL-3.0-or-later metadata, third-party notices and matching corresponding source/build instructions alongside distributions.
- [ ] Run the hosted Windows/macOS/Linux CI matrix. Local checks do not establish remote CI results.
- [ ] Verify startup with and without saved progress: workspace stays empty until import or explicit restore.
- [ ] Review final archives and staged files: no PDFs, session data, glyph assets, credentials, personal paths or bundled fonts/weights.
- [ ] Enable GitHub private vulnerability reporting and publish monitored maintainer/conduct contacts.
- [ ] Confirm repository owner/name, public visibility, branch protections and required checks.
- [ ] Verify exact optional OCR/model licenses and offline behavior before bundling or advertising an OCR-enabled distribution.
- [ ] Accept target-platform font/CJK handling, scan editing, batch numbering and large/rotated/encrypted documents.
- [ ] Verify matching wheel/sdist/source archive checksums before later publication.

CI builds artifacts only. It does not create a repository, publish a release, upload to an index or need deployment credentials. No paid service or commercial license is part of the release plan.
