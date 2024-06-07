# Blender Export Helper

[![Latest Release](https://gitlab.com/setherizor/blender-export-helper/-/badges/release.svg)](https://gitlab.com/setherizor/blender-export-helper/-/releases)
[![pipeline status](https://gitlab.com/setherizor/blender-export-helper/badges/main/pipeline.svg)](https://gitlab.com/setherizor/blender-export-helper/-/commits/main)

## Related Software
- [**Blender 4.1**](https://www.blender.org/download/)
- [**Better FBX Importer & Exporter 5.4.0**](https://blendermarket.com/products/better-fbx-importer--exporter)

## Installation

1. Download the lastest [**BEH-[version].zip** release](https://gitlab.com/setherizor/blender-export-helper/-/releases/permalink/latest), DO NOT UNZIP
6. In Blender click `Edit -> Preferences -> Addons -> Install` and select the downloaded zip.
7. You may now delete the zip from your downloads.

## Development Guide
1. clone this repo  to `\AppData\Roaming\Blender Foundation\Blender\<version>\scripts\addons`
2. restart blender & enable this addon in blender's addon settings
3. open a project in blender as usual, make changes/tweaks to the python, use `F3` then `Reload Scripts` to apply changes within blender (sometimes to see changes you have to close and open blender)

### Tips
> Use blender's scripting view, code windows, & [api docs](https://docs.blender.org/api/current/index.html) to learn more about what is possible

> Use the blender option "Toggle System Console" (press F3, then type) to get more detailed output from the addon
