# AIDA64 SensorPanel Import Strategy

Goal: help users migrate layouts they personally own from AIDA64 SensorPanel into OpenSensorPanel without bundling or redistributing copyrighted templates, icons, logos, or proprietary assets.

## What public docs confirm

AIDA64's own SensorPanel documentation says exported `.SENSORPANEL` files contain the graphics and settings used in a panel and are intended for sharing/importing inside AIDA64. The AIDA64 forum also describes exporting through SensorPanel Manager.

## Safe legal/product rules

OpenSensorPanel should:

1. Import only files the user provides locally.
2. Treat imported graphics as user-owned local assets.
3. Never ship AIDA64 templates, paid templates, brand packs, game logos, manufacturer logos, fonts, or copied icon sets.
4. Preserve source/license metadata for every imported asset.
5. Warn the user that imported assets are for their personal use unless they have redistribution rights.
6. Export OpenSensorPanel `.ospanel` packages only with assets marked as project-created, user-created, public-domain, open-license, or explicitly redistributable.
7. Refuse or warn on unknown-license imported assets during public/share export.

This is not legal advice, but it is a practical clean-room policy that avoids copying templates into the project or redistributing third-party artwork.

## Import approach

Build an importer with two modes:

### 1. Personal migration mode

Input: user's local `.sensorpanel` file.

Output: local OpenSensorPanel template stored on that same machine.

Behavior:
- Parse whatever layout metadata can be read.
- Copy embedded or adjacent images into the user's local template asset folder.
- Mark every imported asset:
  - `license: user-imported-personal-use`
  - `source: AIDA64 SensorPanel import: <filename>`
  - `redistributable: false`
- Do not upload/share/export those assets publicly by default.

### 2. Share/export mode

Input: OpenSensorPanel template.

Output: `.ospanel` package.

Behavior:
- Include only assets with safe licenses:
  - `project-created`
  - `user-created`
  - `CC0`
  - `MIT`
  - `Apache-2.0`
  - `OFL`
  - other explicit user-entered redistributable license
- Exclude or warn on:
  - `user-imported-personal-use`
  - `unknown`
  - brand/game/manufacturer assets without permission

## Technical mapping

Map AIDA64 concepts into OpenSensorPanel schema where possible:

- Panel size -> `template.panel.width`, `template.panel.height`
- Background color/image -> `template.panel.background` or `assets` background image
- Sensor text item -> `widgets[]` sensor widget
- Image/logo/icon item -> `assets[]` plus widget `icon_asset_id` or future image widget
- Font family/size/color -> widget style fields
- Position/size -> widget `x`, `y`, `width`, `height`

Sensor IDs will need remapping because AIDA64 sensor names do not equal Linux/OpenSensorPanel sensor IDs. Use a mapping UI instead of guessing silently.

## Next implementation tasks

1. Add `.ospanel` ZIP package format with `template.json` and `assets/`.
2. Add asset license metadata and export filtering.
3. Add a local-only AIDA64 import command that inspects file type/contents without redistributing assets.
4. Add a sensor-mapping screen for imported templates.
5. Add user-facing license warnings before export/share.
