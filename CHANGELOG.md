# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [2.2.0] - 2021-05-18

### Added

- Added support for custom HTTP timeouts in Grafana and Prometheus providers

### Fixed

- Fixed crashing on non-semver releases on GitHub, now it silently proceeds instead

## [2.1.0] - 2021-01-20

### Added

- Added check for updates

### Fixed

- Fixed issue with failing to find lock files when current scope is not the configuration root

## [2.0.0] - 2021-01-18

### Added

- Added `destroy` mode — destroys all defined resources
- Added retry and back-off mechanisms to Grafana client
- Added evaluation locking and lock update mode
- Added ability to run from subdirectories, targeting only specific directories
- Added environment variable templating to main configuration file
- Added some new exceptions

### Changed

- Main configuration file is now in TOML format
- Changed template delimiters from `{{ }}` to `{$ $}` to avoid clashing with Grafana templates
- State is now stored in split files and mirrors configuration file structure
- Moved loop item from `item` to `loop.item` variable
- Re-written diff engine
- Re-written CLI interface
- Switched from `boto3` to `s3path` as S3 client

### Removed

- Removed "debug" mode since it was useless
- Removed `file` and `consul` state providers (temporarily)

## [1.4.1] - 2020-12-15

### Fixed

- Fixed `timeout` option in Prometheus provider being mandatory
- Fixed mypy errors caused by `rich` module upgrade

## [1.4.0] - 2020-12-15

### Added

- Added `timeout` option to Prometheus provider

## [1.3.0] - 2020-12-10

### Added

- Added `validate` command to validate the configuration and resources format
- Added debug mode (prints the traceback on error)

### Changed

- Interrupt signals (i.e. SIGINT aka Ctrl-C, SIGTERM, SIGQUIT etc.) are now ignored during apply
- Order change in arrays is now ignored
- Repetitions in arrays are now reported

### Fixed

- Fixed `uid`, `id` and `version` fields being added to the resource state after resource update
- Fixed outcome evaluation logic (erroneously creating/removing resources when adding/removing fields in the model)
- Fixed "other" error messages in S3 provider
- Fixed diff header being printed before diff rendering, causing a delay between printing the header and diff itself

## [1.2.1] - 2020-12-09

### Fixed

- Fixed missing `boto3` dependency

## [1.2.0] - 2020-12-09

### Added

- Added S3 state provider
- Added some missing error handlers

### Changed

- Now state is submitted after every resource modification
- Resource UIDs are now converted to MD5 hash to fit Grafana UID length limit of 40 symbols

## [1.1.0] - 2020-12-07

### Added

- File provider for state

### Fixed

- Minor UI/UX fixes and tweaks
- Fixed `id` field not being ignored

## [1.0.0] - 2020-12-07

### Added

- Initial version

[unreleased]: https://github.com/SupersonicAds/gdbt/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/SupersonicAds/gdbt/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/SupersonicAds/gdbt/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/SupersonicAds/gdbt/compare/v1.4.1...v2.0.0
[1.4.1]: https://github.com/SupersonicAds/gdbt/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/SupersonicAds/gdbt/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/SupersonicAds/gdbt/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/SupersonicAds/gdbt/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/SupersonicAds/gdbt/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/SupersonicAds/gdbt/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SupersonicAds/gdbt/compare/2c07324...v1.0.0
