# DoseCare Animation Rows

DoseCare stage-one pets use a fixed atlas: 8 columns, 9 rows, 192x208 pixels per cell.

| Row | State | Used columns | Durations |
| --- | --- | ---: | --- |
| 0 | idle | 0-5 | 280, 110, 110, 140, 140, 320 ms |
| 1 | happy | 0-5 | 120, 120, 120, 140, 140, 240 ms |
| 2 | sad | 0-5 | 180, 180, 180, 180, 180, 320 ms |
| 3 | greeting | 0-3 | 140 ms each, final 280 ms |
| 4 | jumping | 0-4 | 140 ms each, final 280 ms |
| 5 | sick | 0-5 | 180, 180, 180, 180, 180, 320 ms |
| 6 | levelup | 0-7 | 100, 100, 100, 120, 120, 140, 140, 260 ms |
| 7 | eating | 0-5 | 140, 140, 140, 140, 160, 280 ms |
| 8 | sleeping | 0-5 | 320, 240, 240, 320, 240, 420 ms |

Unused cells after each row's final used column must be fully transparent.

## Row Purposes

- `idle`: calm baseline loop; breathing, blinking, subtle head or tail motion.
- `happy`: on-time-care success; bright expression, perked posture, small bounce, tail wag.
- `sad`: missed-care or low mood; drooping head/ears, slow motion, tender disappointment.
- `greeting`: home open or tap greeting; friendly paw raise or lean-in.
- `jumping`: tap feedback or light celebration; anticipation, lift, peak, descent, settle.
- `sick`: low-health state; curled/slumped posture, tired eyes, weak motion.
- `levelup`: growth milestone; proud joyful upgrade celebration with body-attached accents only.
- `eating`: reward after care completion; tiny treat held close, gentle chewing, satisfied finish.
- `sleeping`: night or long-idle rest; closed eyes, slow breathing, tiny ear or tail twitch.
