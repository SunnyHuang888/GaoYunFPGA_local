# GaoYunFPGA_local

Local documentation workspace for GaoYun FPGA development.

## Purpose

This repository is intended to keep local, project-specific GaoYun FPGA notes in one place, including:

- device notes (part numbers, package, resources)
- toolchain usage notes
- build/programming flow notes
- board-specific pin and constraint references

## Suggested local documentation structure

Use this structure as documentation grows:

```text
docs/
  devices/
  toolchain/
  boards/
  examples/
```

## Quick start

1. Clone this repository locally.
2. Add markdown documents under `docs/` by topic.
3. Keep hardware-specific details (clock, pinout, constraints, flash/programming flow) in separate files for each board/device.

## Notes

- Keep documents plain Markdown for easy offline reading.
- Prefer one topic per file to keep updates small and traceable.
