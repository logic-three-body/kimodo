# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [2026-03-31]

### Added
- New `kimodo_convert` CLI tool for converting generated motions between formats (NPZ, BVH, MuJoCo CSV, AMASS NPZ).
- Support for loading and saving BVH, CSV, and NPZ motion files in the interactive demo.

## [2026-03-27]

### Fixed
- Bug fix for foot contact visualization in the interactive demo.
- Patch bug with BVH export for SOMA models.

## [2026-03-19]

### Changed
- **Breaking:** Model inputs/outputs now use the SOMA 77-joint skeleton (`somaskel77`). This affects saved motion formats and constraint files from previous versions.

### Added
- Released timeline annotations for the BONES-SEED dataset on HuggingFace.

## [2026-03-16] - Initial Release

### Added
- Open-source release of Kimodo codebase under Apache-2.0 license.
- Five model variants: Kimodo-SOMA-RP-v1, Kimodo-G1-RP-v1, Kimodo-SOMA-SEED-v1, Kimodo-G1-SEED-v1, Kimodo-SMPLX-RP-v1.
- Command-line interface (`kimodo_gen`) for motion generation with text prompts and kinematic constraints.
- Interactive web-based motion authoring demo (`kimodo_demo`) with timeline editor, constraint tracks, and 3D visualization.
- Support for multiple output formats: default NPZ, MuJoCo qpos CSV (G1), AMASS NPZ (SMPL-X).
- Documentation site with quick start guide, installation instructions, CLI reference, and API docs.
- Compatibility with downstream tools: ProtoMotions (physics-based policy training) and GMR (motion retargeting).
