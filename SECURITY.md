# Security policy

The initial supported public series is 0.1.x. Internal v2.3.x snapshots are not supported public releases. No response-time SLA is promised.

Use the repository's Security > Report a vulnerability flow for a private report. Maintainers must enable GitHub private vulnerability reporting before launch. If that control is unavailable, open an issue asking for a private reporting channel **without including vulnerability details or sensitive material**. Do not send real customer PDFs. Supply a synthetic reproduction, affected version, impact and suggested mitigation when possible.

Pedit is a single-user local editor. It binds to 127.0.0.1 and has no multi-user authentication, sandboxed PDF worker or deployment hardening for public hosting. Do not reverse proxy it or run it on a shared untrusted host. Loopback is not an authentication boundary; malicious local software, browser requests and hostile PDFs remain relevant threats. Only open trusted documents. Full application security assessment remains a pre-release/ongoing task.

Original PDFs, baselines, glyph data and progress JSON are stored locally under `PEDIT_DATA_DIR`, or the OS temporary directory's `pedit-oss-v1` child by default. OCR/render caches and document excerpts can remain there after shutdown. Browser localStorage also retains saved progress and tuning settings. To remove a session, close the editor, delete only its session subdirectory in the configured data directory, and clear site storage for the local editor origin. Preserve anything you still need before cleanup.

Never use a visual overlay as proof of secure redaction. Text, images, metadata or previous content may remain extractable. Use a dedicated audited redaction workflow for irreversible removal of confidential content.
