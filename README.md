# Cooking with ApertureDB

## About ApertureDB
Our flagship product is ApertureDB, a database purpose-built for multimodal AI that combines
fast vector search with a graph database, and allows our users to access data. Head over to
[our documentation](https://docs.aperturedata.io) to learn more.

## About Cookbook Dataset
In order to demonstrate ApertureDB capabilities and provide some hands-on tutorial,
we have curated a dataset comprised of food images, cooking videos, and relevant metadata.
** This repository provides the dataset and notebooks that can take you on a culinary journey
from a beginner to an expert ApertureDB user**.

## Versioning

The root `VERSION` file contains the release version in `MAJOR.MINOR.PATCH`
format. Bump it before merging a new docs-content release into `main`.
On `main`, the docs-content workflow creates the matching Git tag, publishes
an image tagged `<VERSION>`, and sends that same tag to infra to update the
develop component pin. Reruns reuse a Git tag only when it points to the same
commit; an existing tag on another commit requires a version bump.
The release version is embedded in the image for GitHub source and Colab links.
Develop and pull request builds validate the image without publishing it.

## Server compatibility

These examples require ApertureDB server 1.0 and Python SDK `aperturedb>=1.0,<2`.
Media additions use explicit application classes. Descriptor search spaces use
descriptor classes with native vector indexes.

## Offline notebook compatibility check

Run all 23 notebooks against an empty, disposable server 1.0 instance:

```bash
python -m pip install 'aperturedb>=1.0,<2' ipython pandas pillow requests rdflib pypdf
python scripts/test_server1_notebooks.py --port 55555
```

You can select notebooks by name, set `APERTUREDB_JSON` instead of `--port`, and
keep cell logs with `--log-dir`. The harness executes the notebook queries and
cleanup cells unchanged, maps downloads to tracked files, and replaces embedding
providers with deterministic vectors. It downloads no model weights or network
assets and checks query compatibility rather than model relevance. PDF extraction
uses pypdf; `--pdf-text-fixture PATH` can instead supply text extracted locally
from the tracked ButterChicken.pdf fixture.

## Existing data and generated files

These applications target server 1.0. Updating code does not rename stored
application classes. Inspect `GetSchema` (`nodes` and `edges`) before reusing an
existing database: converted built-in categories have names such as `Image`,
`Video` and `Blob`, while these examples use explicit application classes. On a
dedicated application database, use the native `RenameClass` command to align
those categories with the configured names, or reingest through the updated
loaders. Shared databases need an application-specific export/reingestion plan.
Regenerate connection CSVs and cached identifiers against the native schema;
old `_Image@...`/`_Descriptor@...` headers do not identify native categories.
