# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## 0.2.0 - 2026-10-30

### Added

- Include the API's `errorType` and message in error logs.

### Changed

- Switch to the new Vandebron green energy mix API (`https://api.vandebron.tech/green-energy-mix-kotlin`), using the `/v1/forecast/{date}` and `/v1/window/{date}` endpoints.
- Request dates by the Amsterdam local date instead of the UTC date.
- Limit the number of forecast days to 4 (today up to today+3), the range the new API supports. Existing entries configured with more days are capped at 4.
- The `timestamps` attribute of the Vandebron Forecast sensor now contains UTC timestamps (e.g. `2026-10-30T11:00:00Z`) instead of Amsterdam local times.
- Move the integration files to `custom_components/vandebron_green_energy/`, the repository layout HACS expects.
- The `documentation` link in `manifest.json` now points to this repository.

### Fixed

- Installing or updating through HACS failed with "The version … for this integration can not be used with HACS", because the repository had no `hacs.json`. Added `hacs.json` and the `issue_tracker` link HACS requires in `manifest.json`.
- Window start and end times are now correct during winter time; previously a fixed `+02:00` offset was assumed.
- When data for one day is unavailable, the per-day sensors of later days no longer show the wrong day's data.

## 0.1.0 - 2025-05-30

### Added

- Initial release with greenest window and green energy forecast sensors for Vandebron.
- UI config flow with a default setup and an advanced setup to choose the number of days to retrieve.
