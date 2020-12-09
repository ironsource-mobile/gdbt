# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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

[unreleased]: https://github.com/SupersonicAds/spotcli/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/SupersonicAds/spotcli/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/SupersonicAds/spotcli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/SupersonicAds/spotcli/compare/2c07324...v1.0.0
