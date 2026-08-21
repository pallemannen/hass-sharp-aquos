# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
follow the integration's `manifest.json` version.

## [0.1.4] - 2026-08-21

### Fixed
- `brand/icon.png` and `brand/logo.png` were byte-identical copies of the
  same image. `icon.png` is now a distinct horizontal SHARP/AQUOS lockup;
  `logo.png` stays the original stacked design from the stock Aquos
  integration.

## [0.1.3] - 2026-08-21

### Changed
- Field read failures are now logged differently depending on what kind of
  failure it was, instead of both warning once and then dropping to debug.
  A dropped connection (`AquosConnectionError`) warns on every occurrence -
  these integrations typically talk to older TVs over wifi that was never
  great to begin with, so an occasional drop is expected, ongoing behavior,
  not a one-time fact. A command the TV actively rejects or doesn't support
  (`AquosCommandError`) still only warns once, since that's a stable fact
  about the model that won't change poll to poll.

## [0.1.2] - 2026-08-21

### Fixed
- A TV replying with anything other than `"OK"`/`"ERR"`/a clean integer to
  a numeric field (volume, aspect ratio, backlight, signal strength, etc.)
  raised a bare `ValueError` that wasn't caught anywhere - it wasn't one
  of the `AquosConnectionError`/`AquosCommandError` types the per-field
  poll loop and every caller actually handle. That silently killed the
  rest of that poll cycle (and its `return`), so any field ordered after
  the bad one went dark with no log line at all, and no data from that
  cycle - including fields that succeeded earlier in the same cycle -
  ever made it back to the entities. All numeric reads now go through a
  `_send_int` helper that turns this into a proper `AquosCommandError`.

## [0.1.1] - 2026-08-21

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
