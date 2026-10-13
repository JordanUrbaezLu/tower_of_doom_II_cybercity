# tod\music — the map's own music wavs

Drop the game-long ambient track here as `tod_ambient_music.wav`.
**Format is enforced by the bank builder: 48000 Hz, 16-bit PCM** (44.1k is
rejected with "wav is not 48k sample rate" — resample:
`ffmpeg -i in.wav -ar 48000 -sample_fmt s16 -ac 2 out.wav`).
It loops raw, so it should loop reasonably cleanly.
Then point the `tod_ambient_music` alias row in `sound/aliases/tod_ui.csv`
at `tod\music\tod_ambient_music.wav` (FileSpec column) and run a full build.
The sync step copies this tree to the Mod Tools root `sound_assets\`, which
is where alias FileSpec paths resolve at sound-bank build.

Until then the alias points at map 1's calm city track as a placeholder.

## THE END-OF-RUN CUES (2026-10-04, asset pack PK03) — `tools/sfx/end_of_run_music/make_sounds.py`

The two cues a run ends on, GENERATED with ElevenLabs Music (`music_v2_5`, at most three takes per cue: two from a
written composition plan, one from a prompt; every take measured and scored, the pick and the reason it was picked in
`tools/sfx/end_of_run_music/sounds_manifest.json`), mastered with `music_master.py`'s chain (the -6 dB shelf under
200 Hz, gain toward the bands' -11.5 LUFS with the limiter's work capped at 4 dB, true peak -1 dBTP), stereo 48 k / 16-bit:

- `tod_music_gameover.wav` (13.1 s, -11.7 LUFS) - THE LOSS. A G minor defeat cadence: a braam, a cluster hit, Eb -> D ->
  the last G minor hit, then the fall into silence. Played ONCE at end_game from its own emitter
  (`_tod_atmosphere::gameover_play`, right after the channel stops); stock's own "game_over" music state is taken
  (`snd_play_state_override`) so exactly one game-over cue plays. Never on a win (`level.tod_escaped`).
- `tod_house_victory.wav` (17.7 s, -12.9 LUFS integrated; its climax sits at the boss track's short-term level) -
  BEATING THE DEALER (`_tod_arena::arena_win` at the house's level). Near-silent for its first 4.5 s, under his 6.25 s
  death line (it starts ~1.75 s into it; a baked -4 dB tuck until 4.75 s keeps his last word 6.5 dB+ clear in the
  voice band), then Bm -> G -> A -> D with a climbing arpeggio, landing on D major. "115"
  fades under its first second; the channel stays parked for `TOD_HOUSE_VICTORY_SECS` (18.2 = the manifest's
  `hold_secs`, LOCKSTEP) and then the ride home's band plays.

BOTH ARE NONLOOPING ONE-SHOTS ON THEIR OWN EMITTER, on purpose (not the channel's LOOPING-and-stopped shape): a solo
server pause stops the script clock but not the audio (UIN_MOD rows are not pauseable), and the game-over restart menu
IS a pause in solo, so a LOOPING cue would wrap and replay under it. Re-pick a take: `takes/picks.json` in
`tmp/asset_prod/PK03-end-of-run-music/`, `make_sounds.py pick`, then copy the new `hold_secs` into
`TOD_HOUSE_VICTORY_SECS` - the build gate (`make_sounds.py --check`) fails until they agree.

## Band tracks (v9.46, 2026-08-23)

The music changes as the party climbs past the breather floors. Each band is
ONE row in `_tod_atmosphere::register_music_bands()` — `add_music_band( <first
floor>, "<alias>" )` — plus an alias row in `sound/aliases/tod_ui.csv` (clone
`tod_ambient_music`, change only Name and FileSpec) plus the wav here.

**The floors below were STALE for a week** (20/30/40 — the pre-2026-08-25
split). Read `register_music_bands()`, not this table, if the two ever
disagree again; the code is the only place a band floor is decided.

## SOURCES, LOSSLESS OR NOT (2026-10-01, user: "Can we do the lossless upgrade?")

Lossless now: Falling To Pieces (the user's FLAC), 115 and Deep Mystery (the user's wavs), and
METEOR HERD since 01:05: `tmp/music_bass/src/sa2_meteor_herd_instrumental_attempt.flac` from the
Internet Archive item `sonic-adventure-2-hip-hop-soundtrack` (an UNOFFICIAL fan compilation, like
the CG Instrumentals YouTube upload it replaces; 44.1 k / 16-bit, measured 6 dB more energy above
16 kHz and 11 dB more above 19 kHz than the Opus; same arrangement, trailing silence at 208.91 s =
the same 208.9 s trim). `music_master.py --source tod_music_relay=<that flac>` builds it; the
YouTube-sourced master is kept at `tmp/music_bass/onepass/` history and on the comparison page's
"source check" row. STILL LOSSY (YouTube Opus 251, the best copy obtainable without a purchase):
La Clé des Champs, Cornfield Chase, Una Mattina, With You, Reykjavik. WHERE TO BUY THEM LOSSLESS
(the user's step; drop the file into `tmp/music_bass/src/` and pass `--source name=path`):
La Clé des Champs: Bandcamp (ntogd.bandcamp.com, album) / Qobuz / Beatport; Reykjavik: Beatport
(Hungry Music, track 8225820; Qobuz is streaming-only for it); Una Mattina: Qobuz (24-bit) or
Beatport; Cornfield Chase: Qobuz (the original 2:22) - the artists' free pumpyoursound gate gives
the EXTENDED mix for a SoundCloud/Spotify/Instagram follow; With You: Beatport (The Night Drive,
release 4247082 = the original + extended). On Beatport pick WAV/AIFF/FLAC, never MP3. No
stream-ripper or pirate copy is ever used here.

## WITH YOU: THE SEPARATION IS A TWO-MODEL ENSEMBLE (2026-10-01 01:20)

Four separators were run on the same source (`scratchpad/withyou/sep_*`): demucs htdemucs_ft
(rejected by ear), BS-RoFormer ep_317, Mel-Band RoFormer inst v2, MDX23C-8KFFT-InstVoc_HQ_2.
Measured on the loudest sung stretch (70-90 s, 300-3400 Hz band RMS: lower = less voice left):
demucs -24.5 dB, Mel-Band -24.7, BS-RoFormer -25.3, MDX23C -25.3, the three-way average -25.2.
The three RoFormer/MDX outputs agree to within -36..-41 dB of each other, so an ensemble buys
little bleed reduction; SHIPPING = the AVERAGE OF BS-RoFormer AND MDX23C (the two cleanest, equal
weights, `amix normalize=0, volume 0.5`) - averaging two agreeing estimates cancels their
independent artefacts without adding the Mel-Band's extra voice. That file is
`tmp/music_bass/src/withyou_plain.wav`; the melody layer goes over it as described below.

## WITH YOU: THE VOCAL'S MELODY, KEPT ON A SYNTH (2026-10-01) — `tools/music_vocal_melody.py`

User, on the vocal-free version: "the vocals give it another layer of melody that I still want to
keep, but I don't want the vocals". So: the BS-RoFormer VOCAL stem (the cleanest isolation) is
transcribed to MIDI with Spotify basic-pitch (435 notes, D3..E6, pitch bends kept, blips under 110 ms
dropped, slurs made legato), rendered by the script's own synth (three band-limited saws detuned +/-9
cents, a sine sub, amp + filter envelopes, delayed vibrato, chorus, a 2.2 s convolution reverb from a
synthetic IR, high-passed at 150 Hz so it stays out of the cut bass) and blended 7 LU under the
RoFormer instrumental (`mix` measures both and sets the gain; the sung vocal sat ~5 LU under). That mix
is `tmp/music_bass/src/withyou_instrumental.wav`, which `music_master.py` masters as `tod_music_withyou`
(the plain instrumental is `withyou_plain.wav` beside it). ENVIRONMENTS: basic-pitch needs TensorFlow,
which has no Python 3.12+ wheels on Windows, so it lives in a uv Python 3.11 venv
(`scratchpad/bpenv`, with `setuptools<81` for resampy's pkg_resources); the separators live in the
3.12 venv (`scratchpad/sepenv`, audio-separator 0.47). Knobs the user may ask for: `mix --under-lu`
(how far under the band the melody sits), `render --reverb-db` / `--detune`, `transcribe --onset`
/ `--frame` (fewer or more notes). Comparison page row: WITH VOCAL / NO VOCAL / MELODY KEPT.

## THE ONE-PASS REMASTER (2026-10-01, SHIPPING) — `tools/music_master.py`

User, after approving the 50% cut: "I want max quality ... Time it takes is not a problem." The
50% set below had stacked a second limiter on masters that were already limited once (bass-heavy
peaks limited, then EQ'd, then limited again). SHIPPING NOW: every track re-mastered FROM ITS
ORIGINAL SOURCE in ONE pass by `python tools/music_master.py` (sources: the five YouTube Opus
251 downloads re-fetched into `tmp/music_bass/src/` by video id; `Downloads/01. Falling To
Pieces.flac` (lossless, better than the wav used before); `Downloads/115_Remastered_Extended.wav`;
`Downloads/Deep Mystery.wav`; the finale's Downloads wav): soxr 48 k -> trim to the proven loop
length -> `lowshelf f=200 g=-6 q=0.7` -> makeup gain converged on the target (two correction
passes, because a limiter with level=disabled costs loudness) -> ONE true-peak limiter (4x
oversampled, attack 5 / release 200, ceiling -0.2 dBTP), capped at `--max-lim` -> dither 16-bit.
Targets: the five bands -11.5 LUFS (`--band-target`), boss -12.2, intro -12.9, ee -5.6, finale -7.7.
RESULT: bands -11.5 / -11.6 / -11.5 / -11.5 / -11.9 (0.4 LU spread), every peak -0.2 dBTP; limiter
work eclipse 2.8 dB, relay 6.5, cornfield 3.2, city 1.4, ambient 7.5 (the cap: Reykjavik and Meteor
Herd are QUIET, DYNAMIC sources, -16/-17 LUFS after the shelf, so this is ordinary mastering gain
reduction on transients, not squash on a brick wall; the old two-stage chain had spent about the
same total on them); boss 0 (it is attenuated 3.5 dB), intro 3.3, ee 1.5, finale 4.2. Bass vs the
rest of the mix -4.1..-4.9 dB. Re-run: `python tools/music_master.py --band-target -11.5 --max-lim
7.5` (add `--measure` to see the cost of any target first). Buying the five tower songs LOSSLESS
(Bandcamp / Beatport WAV or FLAC) is the one upgrade left: drop them in `tmp/music_bass/src/` under
the same names, re-run, nothing else changes.

## THE BASS PASS, SECOND CUT (2026-10-01) — 50% LESS BASS, LEVELLED (TWO-STAGE; SUPERSEDED BY THE ONE-PASS REMASTER ABOVE)

The user A/B'd the 25% set on the comparison page and heard almost nothing ("i dont
notice much in the bass between the 2": a 2 dB relative shift is near the ear's
threshold), then "Maybe we need 50%". SHIPPING NOW: the shelf at -6 dB (same corner,
200 Hz, Q 0.7), then MAKEUP GAIN - the five bands levelled to a common -11.0 LUFS, the
other tracks back toward their original loudness - capped so a TRUE-PEAK limiter
(4x oversampled: `aresample=192000`, `alimiter limit 0.977 level=disabled latency=1`,
`aresample=48000` soxr) never takes more than 2.5 dB; 16-bit dither last:

    lowshelf=f=200:g=-6:width_type=q:w=0.7  ->  volume=<g>dB  ->  192 k  ->  alimiter  ->  48 k

Measured (`tools/music_measure.sh`): bass band vs the rest of the mix -4.2..-5.1 dB
(the 25% pass was -1.6..-2.1), every peak -0.2 dBTP. Gain / limiter work per track:
eclipse +1.2 / 1.7 dB, relay +0.5 / 0.7, cornfield +2.5 / 2.2, city -0.2 / 0.1,
ambient +1.8 / 2.5 (the most bass-heavy master: it lands at -11.8, the cap bound),
boss +1.3 / 0, intro +2.3 / 2.5, ee +1.3 / 2.3, finale +1.9 / 2.5. Final LUFS: the
five bands -11.0 / -11.0 / -11.1 / -11.0 / -11.8, boss -12.2, intro -13.0, ee -6.4,
finale -8.4. The 25% set is parked in `tmp/music_bass/quarter/`, the 50% set is
`tmp/music_bass/half/` = what sits in this folder now. Comparison page (BEFORE /
25% / 50% in lock-step): https://claude.ai/artifact/WRcaP3CgAzFNh3gXEmBTsP

## THE BASS PASS, FIRST CUT (2026-09-30) — 25% LESS BASS (SUPERSEDED BY THE 50% CUT ABOVE)

User: "lower the base on all of them by 25% ... the songs have too much bass which
are not optimal for a zombies map. They need a bit more color." Applied to all
nine wavs in this folder (the five bands, the boss track, the intro, the teddy-bear
song and the parked finale), in place, from the parked originals:

    ffmpeg -i <original> -af "lowshelf=f=200:g=-2.5:width_type=q:w=0.7,alimiter=limit=0.977:attack=5:release=150:level=disabled:latency=1,aresample=48000:dither_method=triangular_hp" -ar 48000 -sample_fmt s16 -ac 2 <out>

25% in amplitude is -2.5 dB; the shelf's corner sits at 200 Hz (Q 0.7, no bump) so
the whole bass band is on the plateau. MEASURED with `tools/music_measure.sh`
(RMS of the <= 150 Hz band vs the rest): the bass band fell 2.34-2.42 dB on every
track (24-25%), the rest moved 0.3-0.9 dB (the shelf's taper through 150-400 Hz, the
"mud" region, which is what buys the colour), peaks capped at -0.2 dBFS (the shelf's
phase shift pushed three masters past full scale; the limiter touches a handful of
samples, flat factor <= 0.5 against the old finale's 1630 clipped samples). NOT
RE-GAINED: the overall loudness fell 0.7-1.7 LU (bass carried that much of these
masters' energy) and the alias rows are already at 100, so a louder set means
re-limiting; the user judges first. Originals: `tmp/music_bass/originals/` (and git).
Before -> after, integrated LUFS: eclipse -9.2 -> -10.6, relay -10.0 -> -10.8,
withyou (new) -11.4, cornfield -10.6 -> -12.0, city -9.2 -> -10.0, ambient -9.9 ->
-11.6, boss -12.2 -> -12.9, intro -12.9 -> -14.1, ee -5.6 -> -6.3, finale -7.7 -> -8.7.

## "WITH YOU" (2026-09-30) — THE SIXTH BAND, VOCALS SEPARATED

User: "I also like the song With You by Lynnic but I dont want vocals ... use
whatever tools you need so we can keep the quality at the max." No instrumental
exists (searched YouTube: only the original, the Afro House mixes and the extended
mix, all with Dinia's vocal), so the vocal was SEPARATED with demucs 4.1
`htdemucs_ft` (the fine-tuned four-model bag, `--two-stems=vocals`, CPU, ~5 min)
from the official upload on Lynnic's channel (YWTrmXf0Uxs, Opus 141k, 168 s). The
vocal stem measured -18.7 LUFS against the instrumental's -11.5 (a secondary
element in the mix, so the separation has little to hide). Then: trailing silence
cut at 166.3 s (the song fades out from 160 s; 0.3 s fade at the cut), the same bass
shelf, +1.8 dB to -11.4 LUFS (the midpoint of its neighbours relay -10.8 and
cornfield -12.0 after the bass pass), limiter -0.2 dBFS AFTER the soxr 44.1 -> 48 k
resample (before it, the resampler overshot the ceiling), 16-bit dither. Residual
vocal artefacts are a listening call the user makes. The band split is 9/8/8/8/9/8
going down (see register_music_bands); the slot is an assumption, see the comment there.

## TOD II TRACKS (2026-09-28) — THIS SUPERSEDES THE BAND SOURCES IN THE TABLE BELOW

The run goes DOWN (docs/160), so the first band heard after the crown seals is the TOP row.
Same aliases, new wavs; the four band aliases went 95 -> 100 (the gap to TOD1's -8.5 LUFS bands).

| floors | alias | song | source | final |
|---|---|---|---|---|
| 50-42 | `tod_music_eclipse` | "La Clé des Champs" — N'to | YT Music Topic 7CodDq8GKpk (Opus 161k) | -9.2 LUFS, 410.0 s (-10.6 after the bass pass) |
| 8-1 + the ground (41-34 on 2026-09-30, 40-31 before; moved to the BOTTOM 2026-10-01, user) | `tod_music_relay` | "Meteor Herd" instrumental — SA2 | YouTube az2LslUsw5o, CG Instrumentals (Opus 143k) | -10.0 LUFS, 208.9 s (-10.8 after the bass pass) |
| 41-34 (33-26 on 2026-09-30) | `tod_music_withyou` | "With You" — Lynnic, ItsArius & Dinia, VOCALS REMOVED (demucs htdemucs_ft) | YouTube YWTrmXf0Uxs, official upload on Lynnic's channel (Opus 141k, 168 s) | -11.4 LUFS, peak -0.2 dB, 166.3 s |
| 33-26 (25-18 on 2026-09-30, 30-21 before) | `tod_music_cornfield` | "Cornfield Chase" — ItsArius & Lynnic (added 2026-09-29; the user placed it in the MIDDLE, the bands became five even tens) | YouTube TFEdFXArQz0, official upload on Lynnic's channel (Opus 251, 141.9 s, measured -10.3 LUFS / +0.8 dBTP) | -10.6 LUFS, peak -0.8 dB, 141.5 s (gain +2.0 dB; +3.0 dB only reached -10.3 = the master's ceiling, so stopped there; trailing 0.4 s silence cut for the loop) |
| 25-18 (17-9 on 2026-09-30, 20-11 before) | `tod_music_city` | "Una Mattina" — Lynnic | YT Music Topic Fod9QOQppKg (Opus 140k) | -9.2 LUFS, 199.4 s (-10.0 after the bass pass) |
| 17-9 (8-1 on 2026-09-30, 10-1 before; its alias is still the literal fallback name, now unreachable) | `tod_ambient_music` | "Reykjavik" — Joachim Pastor | YT Music Topic admmPKa6lok (Opus 152k) | -9.9 LUFS, 455.4 s (-11.6 after the bass pass) |
| boss (THE BATTLE ARENA) | `tod_boss_music` | "115" extended | user's `Downloads/115_Remastered_Extended.wav` (44.1k -> 48k soxr) | -12.2 LUFS, 850.3 s (-12.9 after the bass pass) |

Recipe: `yt-dlp -f bestaudio`, then `aresample=48000:resampler=soxr:precision=28,volume=<g>dB,alimiter=limit=0.86:attack=5:release=150:level=disabled`, 16-bit; trailing silence trimmed (these loop). WHY NOT -8.0 LIKE TOD1: Champs and Mattina are ALREADY brick-wall mastered at ~-9.4 — 4 dB of limiting bought +0.1 LUFS. Meteor/Reykjavik past -10 cost 6-8 dB of limiting. Each sits at its clean ceiling (2-4 dB of limiting). The boss matches TOD1's boss exactly (-12.2 at alias 100). THE ARENA TRIGGER: `tod_atmosphere::arena_music_start/end` (TOD II spawns no Panzers, so the Panzer refcount never fires). Log `[TOD_MUSIC] ARENA_START / ARENA_END` (dev).

| band | alias | wav | source |
|---|---|---|---|
| 1–9 (base) | `tod_ambient_music` | `tod_ambient_music.wav` | "Password Infinity" — Evgeny Bardyuzha |
| 10–22 | `tod_music_city` | `tod_music_city.wav` | "Cyberpunk Futuristic City" — lnplusmusic |
| 23–36 | `tod_music_relay` | `tod_music_relay.wav` | "Cyber Relay" — Psychronic |
| 37–50 | `tod_music_eclipse` | `tod_music_eclipse.wav` | "Cyber Eclipse" — bykenneth |
| boss (any floor) | `tod_boss_music` | `tod_boss_music.wav` | "Data Spike" — Psychronic |
| the finale run | `tod_music_finale` | `tod_music_finale.wav` | "You See Big Girl" — Hiroyuki Sawano / Gemie |
| THE TEDDY BEAR SONG (v18.96 — shoot the three bears; NOTHING overtakes it, `channel_play` parks other requests) | `tod_music_ee` | `tod_music_ee.wav` | "Falling To Pieces" (user-supplied 2026-09-13, `Downloads/01. Falling To Pieces.wav` 44.1k) — measured -4.6 LUFS / 0.0 dB peak, v18.96g: +3 dB over the bands (user: "Volume is a knob") — `volume=-0.4dB,alimiter=limit=0.891` → -5.6 LUFS, peak -0.6 dB (the limiter takes the last 0.6 dB; pushing harder only squashes the mix), 279.33 s = `TOD_MUSIC_EE_SECS` |

**The boss, finale and teddy-bear tracks are not bands** — nothing in
`register_music_bands()` names them; each is a plain `channel_play( alias )`
call, which is all a non-band track needs. (The Endless Spire's three tracks -
the spire, the Warden Trials and the Warden King - were removed with the spire,
2026-09-29.)

**The finale track is a CLOCK, not a mood.** `_tod_finale.gsc` ends the game
when it ends, so its length is load-bearing: `TOD_FINALE_SONG_SECS` +
`TOD_FINALE_DEPART_SECS` must equal the measured wav length (currently
191 + 6 = 197, wav 197.395s). Every alias here is LOOPING — it has to be, a
non-looping streamed one-shot is engine-unstoppable — so a timer that runs
LONGER than the wav plays the ending over the song's second intro. If this
track is ever swapped, re-measure and re-derive both numbers in the same
commit.

**The floor 10 breather has no track** and that is the design: the user's bands
are 20 / 30 / 40, with the base ambient carrying everything below 20. A band
with no row simply isn't in the table, so the previous one keeps playing.

**LOUDNESS MATTERS MORE THAN THE ALIAS VOLUME.** The bands hard-swap the
stream, so a track mastered quieter than its neighbour reads as a bug. Match
integrated loudness to the base track (measure, don't guess):
`ffmpeg -i x.wav -af ebur128=framelog=quiet -f null -` then gain + limit:
`ffmpeg -i in.mp3 -af "volume=<target - measured>dB,alimiter=limit=0.891" -ar 48000 -sample_fmt s16 -ac 2 out.wav`.
Current set: ambient −8.0, city −8.9, relay −7.8, eclipse −9.1 LUFS (1.3 dB
spread). The ALIAS-100 boss track sits lower and always has: −12.2.

**MATCH THE TRACK YOU REPLACE, not the loudest one in the table** (v17.8). The
(since removed) Warden Trial track arrived at −15.9 LUFS and took `volume=3.7dB`
to land on the boss track's −12.2 — because it REPLACED the boss track in that exact
moment, at the same alias volume, so matching it makes the swap inaudible as a
level change. Pushing it to the band tracks' −8.0 would have wanted +7.9 dB
against only 5.4 dB of peak headroom, which is the squash the paragraph above
warns about. Peak landed at −1.7 dB and the limiter never engaged.

⚠️ `alimiter` AUTO-LEVELS BY DEFAULT and will overshoot your target by about a
dB. The first pass here asked for +3.7 and measured +4.7. Use
`alimiter=limit=0.891:level=disabled` and then re-measure — always re-measure,
the filter chain is not the receipt. Watch for diminishing returns: the eclipse master already peaked at
0 dB, so past about +5 dB of gain the limiter absorbs everything and you buy
squash instead of loudness. If a track will not come up, that is the signal to
stop, not to push harder.
Credit every track before publish.
