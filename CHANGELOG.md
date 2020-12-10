# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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

[unreleased]: https://github.com/SupersonicAds/spotcli/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/SupersonicAds/spotcli/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/SupersonicAds/spotcli/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/SupersonicAds/spotcli/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/SupersonicAds/spotcli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SupersonicAds/spotcli/compare/2c07324...v1.0.0
