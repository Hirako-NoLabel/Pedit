# Publication hygiene

The public tree contains application source, documentation, test code and packaging/CI configuration. No PDFs, saved sessions, glyph libraries, screenshots, private reports, fonts or OCR weights are included. Tests generate minimal synthetic PDFs at runtime exclusively through tests/fixtures/pdf_factory.py.

Production comments describe behavior without retired replacement-case identifiers. Startup does not import a document, retrieve a saved session or display previous filenames/edits. Progress remains available through explicit restoration.

The release gate checks document/binary assets, credential patterns, personal absolute paths, retired identifier patterns, project license metadata and sample directories. Pattern matching is a hygiene check, not proof that every possible secret or ownership issue has been ruled out.

Publish only this clean tree and reviewed distributions. Private source inputs, working directories and old artifacts outside the tree are not publication inputs. Build artifacts are stored separately from the source deliverable. Source ownership remains a maintainer responsibility.
