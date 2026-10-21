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
