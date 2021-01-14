# GDBT (Grafana Dashboard Templater)

**GDBT** is an infrastructure-as-code tool for Grafana dashboards. This is similar to Terraform, but specializes on templating dashboards based on various evaluations.

## Table of Contents

- [Installation](#installation)
- [Reference](#reference)
  - [Configuration](#configuration)
  - [CLI](#cli)
- [Development](#development)
  - [Prerequisites](#prerequisites)
  - [Using Poetry](#using-poetry)
  - [Build](#build)
  - [Releases](#releases)
  - [CI/CD](#cicd)

## Installation

To install GDBT you can use this one-liner:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/SupersonicAds/gdbt/main/install.sh)"
```

If you prefer manual installation, start with downloading wheel file from the [release](https://github.com/SupersonicAds/gdbt/releases/latest) page.

*Note:* make sure you keep the wheel file name as is, otherwise you won't be able to install it.

The wheel can be installed by running:

```bash
pip3 install ./gdbt-1.0.0-py3-none-any.whl
```

Refer to *[CLI reference](#cli)* for further info.

## Reference

### Configuration

Configuration is written in YAML, and there are 2 kinds: global configuration stored in `config.yaml` file and resources stored in `resources` directory.

#### Global configuration

Here's an example of `config.yaml`:

```yaml
kind: config
providers:
  example-grafana:
    kind: grafana
    endpoint: https://grafana.example.com
    token: ZXhhbXBsZQ==
  example-prometheus:
    kind: prometheus
    endpoint: http://prometheus.example.com:8248
  s3:
    kind: s3
    bucket: example-gdbt-state
    path: state.json
state: s3
```

- `kind`: should be `config`
- `providers`: provider definitions:
  - `kind`: provider kind, one of `grafana`, `prometheus` (for evaluations), `s3`, `consul`, `file` (for state storage)
  - *other provider-specific parameters*
- `state`: name of provider that will be used for state storage

#### Resources

There are 2 kinds of resources: `dashboard` and `folder`, each of these corresponding to relevant Grafana entities.

##### Concepts

- **Lookups**: a static key-value configuration, available as `lookups` dictionary in templates. Useful for mapping or easy template variable modification.
- **Evaluations**: a dynamic variant of lookups, available as `evaluations` dictionary in templates. Can retrieve values dynamically, for example — a list of label values from a metric in Prometheus.
- **Loop**: a mechanism to iterate over a specific variable, making a separate resource for each item. The item itself is available in template as `item` variable.

##### Configuration

Resource file name (without extension) is designated as the resource *uid*.

Example `dashboard` resource:

```yaml
kind: dashboard
provider: example-grafana
folder: example-folder
evaluations:
  example-services:
    kind: prometheus
    source: example-prometheus
    metric: "sum(cpu_user_usage) by (service)[30m]"
    label: service
loop: evaluations.example-services
lookups:
  service_notification_channel:
    service1: victorops-team1
    service2: victorops-team1
    service3: slack-team2
    DEFAULT: mail-all
model: |
  {
    "panels": [
      {
        "alert": {
          "name": "CPU usage high in {{ item }} service",
          "notifications": [
            {
              "uid": "{{ service_notification_channel[item] | default(service_notification_channel.DEFAULT) }}"
            }
          ]
        },
        "targets": [
          {
            "expr": "avg by (service)(cpu_user_usage{service='{{ item }}'})",
          }
        ]
      }
    ],
    "tags": ["example", "cpu", "{{ item }}"],
    "title": "System CPU usage ({{ item }})"
  }
```

*Note: `model` in the above example was stripped and only relevant fields were left. Please refer to Grafana documentation for valid resource model JSON format.

Example `folder` resource:

```yaml
kind: folder
provider: example-grafana
model: |
  {
    "title": "Example Folder"
  }
```

- `kind`: either of `folder`, `dashboard`
- `provider`: name of Grafana provider this resource will be applied to
- `folder` *(only for `dashboard` kind)*: uid of folder the dashboard will be created in
- `evaluations` *(optional)*: dynamic lookups:
  - `kind`: evaluation kind, only `prometheus` is supported at the moment
  - `source`: provider name to run the evaluation against
  - `metric`: metric to evaluate
  - `label`: name of label to extract from received metric set
- `lookups` *(optional)*: static lookups, a simple key-value
- `loop` *(optional)*: loop against specified variable, will generate a resource for each item in provided variable
- `model`: Jinja2 template of Grafana resource model JSON

See [Jinja2 documentation](https://jinja.palletsprojects.com/en/2.11.x/templates/) for more info about templates.

##### Caveats

Grafana forbids creating resources with identical titles. Because of this, be extra careful when using `loop`, ensure that you include `{{ item }}` as a part of `title` — otherwise you will get unexpected cryptic errors from Grafana.

### CLI

```text
gdbt [command] [parameters] [options]
```

Use `--help` for information on specific command. The synopsis for each command shows its parameters and their usage.

#### Commands

- `validate`: Validates the configuration syntax.
- `plan`: Generates an execution plan for GDBT.
- `apply`: Builds or changes Grafana resources according to the configuration.
- `version`: Prints GDBT version.

#### Options

- `-c`, `--config-dir`: Configuration directory. Defaults to current working directory.
- `--debug`: Enables debug mode.

## Development

Before starting, please read [Contributing guidelines](https://github.com/SupersonicAds/gdbt/blob/main/.github/CONTRIBUTING.md).

*Note:* This repo uses *main* as a default branch. Make sure you don't use *master* accidentally.

### Prerequisites

To work on this project you need:

- Python 3.8+ (using [pyenv](https://github.com/pyenv/pyenv#installation) is heavily recommended)
- [Poetry](https://python-poetry.org/docs/#installation)
- IDE with [Black](https://github.com/psf/black#installation-and-usage) formatter, [flake8](https://flake8.pycqa.org/en/latest/#installation) linter and [isort](https://pycqa.github.io/isort/#installing-isort) tool installed

### Using Poetry

This project uses Poetry as a dependency management tool. It has a lot of advantages before plain pip, for example:

- automatic virtual env management
- better dependency management
- build system
- integration with test frameworks

Here are some example actions you should know:

```bash
# Activate the virtual environment and get a shell inside
poetry shell

# Install the app with all dependencies
poetry install

# Add a new dependency (identical to pip install x when not using Poetry)
poetry add x

# Remove a dependency
poetry remove x

# Bump package version (level is one of patch, minor, major)
poetry version level

# Run a command in the virtual environment
poetry run x

# Update dependencies
poetry update

# Build package wheel
poetry build -f wheel
```

All dependencies should be added using Poetry: `poetry add x`. Please try to reuse existing dependencies to avoid bloating the package; you can find the list of these in `pyproject.toml` or by running `poetry show`.

Please specify any additional dependencies in module docstring.

#### Documentation

This tool uses Python docstrings for documentation purposes. Those docstrings should follow [Google's docstrings style guide](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). You should use docstrings module documentation, reference, TODOs etc.

### Build

This package is distributed as a [wheel](https://realpython.com/python-wheels/). This simplifies installation and dependency management on target systems.

Normally you should use stable CI-built wheels, available on Releases page. In case you need a development wheel for testing, you can always build one yourself:

```bash
poetry build -f wheel
```

You can find the built wheel in *dist* directory. *Note:* wheel file name contains package metadata, so do not rename the file, otherwise you might not be able to install it!

### Releases

**GDBT** follows [semantic versioning](https://semver.org) guidelines. Version numbers don't include *v* prefix *unless* it is a tag name (i.e., tags look like `v1.2.3`, everything else — `1.2.3`).

All changes are kept track of in the changelog, which can be found in *CHANGELOG.md* file. This file follows *[keep-a-changelog](https://keepachangelog.com/en/1.0.0/)* format. Please make yourself familiar with it before contributing.

Generally, you should test your changes before creating a release. After that, create a *release candidate* pre-release, using the instruction below. Version number should be `1.2.3-rc.1` — an upcoming release version number with RC suffix. After extensively testing the release candidate, you can proceed to creating a release.

#### Release process

0. Checkout *main* branch.
1. Run `poetry version minor` (or `major` or `patch`, depending on severity of changes in the release). This will bump project version in `pyproject.toml`.
2. Change `[Unreleased]` H2 header in *CHANGELOG.md* to the new release version (e.g., `[1.2.3]`).
3. Add current date in ISO format (`YYYY-DD-MM`) after the header (e.g., `[1.2.3] - 2011-12-13`).
4. Add new `[Unreleased]` H2 header above all version headers.
5. Add compare link at the bottom of *CHANGELOG.md* as follows:
`[1.2.3]: https://github.com/SupersonicAds/gdbt/compare/v1.2.2...v1.2.3` right below `[unreleased]` link (replace `1.2.3` with the new release version, `1.2.2` with the previous release version).
6. Change version in `[unreleased]` link at the bottom of *CHANGELOG.md* to the new release version (e.g., `[unreleased]: https://github.com/SupersonicAds/gdbt/compare/v1.2.3...HEAD`).
7. Commit the changes to *main* branch. Commit message should be `Release v1.2.3`.
8. Create a release tag: `git tag v1.2.3`. This should be a *lightweight* tag, not an annotated one.
9. Push the changes and tag to GitHub: `git push && git push --tags`.

If you find the above instructions unclear, take a look at previous releases or contact project maintainers.

### CI/CD

This repo uses GitHub Actions as CI/CD tool. Pipeline config can be found in *.github/workflows/ci-release.yaml* file.

As of now, the only pipeline is *Release*: it builds the wheel and creates a release in GitHub. It is triggered on tags that start with *v* prefix.

