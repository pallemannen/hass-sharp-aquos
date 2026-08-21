# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
follow the integration's `manifest.json` version.

## [Unreleased]

### Changed
- `power_on_enabled` now defaults to `true` - most setups want Home
  Assistant to be able to turn the TV on, and leaving it off by default
  meant that capability was silently missing until someone found the option.

### Fixed
- Device model no longer stays blank forever if the first read fails. It
  was only ever copied into the device's info once, at entity setup; a
  later successful retry never made it back into the UI.
- Fixed dangling un-awaited coroutines in the per-field poll loop (the
  source of a `coroutine '...' was never awaited` warning) - every field's
  coroutine was being constructed upfront in a tuple literal instead of
  right before it was awaited, so a poll cancelled partway through (a
  config reload, a slow/unresponsive TV) silently dropped whichever fields
  the loop hadn't reached yet.
- Per-field read failures (model, volume, mute, etc.) now log a one-time
  warning instead of being silently invisible at debug level, so a
  genuinely failing command is distinguishable from a field just being
  `None`.

## [0.1.0] - 2026-08-21

### Added
- Initial config-flow release, replacing the abandoned core `aquostv`
  integration and its dead `sharp_aquos_rc` dependency with an inline
  async TCP client.
- `media_player` entity: power, volume, deterministic mute, source select
  (4x HDMI + Component), channel control (direct-tune via `play_media`,
  up/down via next/previous track).
- Diagnostic sensors: aspect ratio, AV mode, backlight, signal strength.
- Setup entirely through the UI - no YAML.
