# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-04

### Added

- Initial CO₂ Carbonator custom integration with config flow setup.
- Current tank, lifetime, completed tank, usage, estimate, and timestamp sensors.
- Expected bottles per tank number entity.
- `record_bottle`, `unrecord_bottle`, `replace_tank`, and `initialize_tank` services/actions.
- Device buttons for recording bottles, correcting bottle records, replacing tanks, and initializing the current tank.
- Bottle recorded, bottle unrecorded, and tank replaced events for downstream automations.
