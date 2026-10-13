#!/usr/bin/env bash
# Measure a music wav: integrated LUFS, true peak, and the RMS of the bass band
# (<= 150 Hz, 4th-order lowpass) vs the rest (>= 150 Hz). Used by the 2026-09-30
# bass pass to prove "25% less bass" by measurement.
# usage: tools/music_measure.sh file.wav [more.wav ...]
for f in "$@"; do
  lufs=$(ffmpeg -nostats -i "$f" -af ebur128=framelog=quiet:peak=true -f null - 2>&1 | grep -E "^ +I:|Peak:" | tr -s ' ' | tr '\n' ' ')
  bass=$(ffmpeg -nostats -i "$f" -af "lowpass=f=150:p=2,astats=measure_overall=RMS_level:measure_perchannel=none" -f null - 2>&1 | grep "RMS level dB" | awk '{print $NF}')
  rest=$(ffmpeg -nostats -i "$f" -af "highpass=f=150:p=2,astats=measure_overall=RMS_level:measure_perchannel=none" -f null - 2>&1 | grep "RMS level dB" | awk '{print $NF}')
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  echo "$(basename "$f") | dur=${dur}s | $lufs | bass_rms=${bass} dB | rest_rms=${rest} dB"
done
