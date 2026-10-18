# STOP AT NOTHING — Logo

Premium minimalist streetwear logo lockup.

- **File:** `assets/stop-at-nothing-logo.png` (1280 × 1280, sRGB)
- **Palette:** black `#000000` · metallic silver · pure white `#FFFFFF`
- **Lockup:** custom chrome infinity mark, hairline rule, stacked uppercase wordmark
- **Usage:** centered, on black; keep clear space of at least the cap height around the lockup

## Motion

- `stop-at-nothing-sting.mp4` — 1080 × 1080, 30 fps, 5 s, H.264 (yuv420p, faststart)
- `stop-at-nothing-sting.gif` — 620 × 620 loop, 20 fps, palette-optimized

The sting: chrome mark settles in, hairline rule draws from the centre outward,
`STOP AT / NOTHING` fades up line by line, then a highlight travels across the metal.

Rebuild with `python3 tools/logo_motion.py 0 150` (needs Pillow + numpy), then encode
the PNG sequence in `$MOTION_FRAMES` with ffmpeg.
