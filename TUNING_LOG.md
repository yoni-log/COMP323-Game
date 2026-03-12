# Don't Crumble — Tuning Notes (Control Feel)
---------------------------------------------

## Parameters (Current Values)
------------------------------
player speed       — 320.0 px/s
invincibility time — 0.85 s  (after taking a hit)
knockback force    — 540.0 px/s
hitstop duration   — 0.06 s
screen shake time  — 0.18 s  (hit), 0.10 s (coin), 0.20 s (game over)
flash duration     — 0.18 s
collect duration   — 0.50 s



## Cue Toggles (Keys 1–4 in game)
---------------------------------
[1] Flash    — white overlay on player when hit
[2] Shake    — screen shake on hit, coin pickup, and game over
[3] Hitstop  — brief freeze on hit for impact feel
[4] Particles — burst of particles on hit and coin pickup



## What Each Cue Contributes to Feel
------------------------------------

Flash: Makes damage immediately readable — the player character briefly turns white so the hit registers visually even without sound.

Shake: Adds physical weight to hits and pickups. The shake strength scales with time remaining, so it eases out naturally rather than cutting off abruptly.

Hitstop: The 0.06 s freeze on hit is subtle but makes collisions feel impactful. Removing it makes the game feel floatier and hits feel cheaper.

Particles: Coin pickups emit 18 particles, hazard hits emit 26. The higher count on hits reinforces that damage is more significant than a collect.



## Playtest Observations
------------------------

All cues on: "Hits feel punchy and readable — I always knew when I got damaged. The coin pickups had satisfying feedback without feeling over the top."

Hitstop off: "Collisions felt softer, like the hazards had less weight. Easy to miss that you took damage."

Particles off: "The game felt quieter and harder to read — especially coin pickups, which blended into movement."



## Summary

- Speed at 320.0 px/s feels deliberate; increasing above 400 makes the playfield feel cramped given the wall layout.
- Knockback at 540.0 gives a strong push without sending the player through walls.
- Invincibility at 0.85 s is long enough to recover positioning after a hit but short enough that hazard clusters are still dangerous.
- The four cue toggles are independent — each can be turned off individually to isolate its contribution to game feel.
- Tone playback is gated with get_busy() on coin pickup to prevent audio overlap; hit and game over tones play unconditionally.
