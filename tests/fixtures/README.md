# Test fixture generators

pdf_factory.py generates minimal synthetic electronic and image-only PDFs in memory. Tests write them only to temporary directories. TEST-A, 123 and 456 have no business meaning. There are no real names, companies, product identifiers, customer data or input PDFs.

The generator uses standard PDF Base-14 font references without embedded font programs and original geometric digit shapes. It needs no external files, font downloads, OCR models or network service. Fixtures are not imported, packaged or presented by the application UI.
