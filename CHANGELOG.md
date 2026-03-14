# Changelog

## 0.8.6
- remove .gitlab-ci.yml and _header.md files

## 0.8.5 
- remove build.sh

## 0.8.4
- animations are no longer simplified with native fbx exporter

## 0.8.3
- bugfixes for blender 5 addon install

## 0.8.0
- compatibility fixed for new blender version & plugin updates

## 0.7.9
- hide better_fbx if addon not available

## 0.7.8
- fix action options being reset on settings changes
- return to previously selected animation after export
- add animation framerate overrides (applies during export)

## 0.7.7
- exposed more options for native and better fbx exporters
- fixed some typos

## 0.7.6
- fix for rare export cases losing/deleting actions if "Action" action exists
- fix for armature objects losing their names
- fix for error cases from view layer excluded collections for armatures
- removed "Bake Frame" start/end overrides

## 0.7.5
- fix for better fbx exporter option not using configured scene frames
- moved export button to own panel

## 0.7.3
- fix for native fbx exporter script "misplacing" an action named the defalt name "Action"

## 0.7.0
- added support for selecting & exporting multiple armature & control rig pairs at once
  - native fbx option transparently combines armatures during export

## 0.6.0
- added support for exporting directly from armatures without control rig

## 0.5.0
- removed Source Tools support

## 0.4.0
- setup betterfbx to use the frame overrides

## 0.3.0
- better naming for exported files
- fixed first-run export for betterfbx

## 0.2.0
- added optional selection & exporting of actions marked as assets

## 0.1.0
- added bulk exporting animation actions
- made UI elements hide/show based on the export_method & selection state
- got Source Tools Export functioning

## 0.0.0
- initial commit
