# DoseCare Pet Contract

## Sprite Atlas

- Format: PNG or WebP.
- Dimensions: `1536x1872`.
- Grid: 8 columns x 9 rows.
- Cell: `192x208`.
- Background: transparent after deterministic extraction.
- Unused cells: fully transparent.

This stage-one contract intentionally keeps the original Codex atlas geometry so existing simple sprite players can be reused. The row semantics are DoseCare-specific and should be read from `references/animation-rows.md`.

## Local Pet Package

Place files under:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/
├── pet.json
└── spritesheet.webp
```

Manifest shape:

```json
{
  "id": "pet-name",
  "displayName": "Pet Name",
  "description": "One short sentence.",
  "spritesheetPath": "spritesheet.webp"
}
```
