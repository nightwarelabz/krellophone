#!/bin/bash
# Chunked parallel render of livecount: 1728 frames, 960x960, 24 fps.
cd ~/workspace/livecount || exit 1
mkdir -p chunks
TOTAL=1728
CHUNK=144
NCHUNKS=$(( TOTAL / CHUNK ))

chunk_ok() {
  [ -f "$1" ] || return 1
  local got
  got=$(ffprobe -v error -count_frames -select_streams v:0 \
        -show_entries stream=nb_read_frames -of csv=p=0 "$1" 2>/dev/null)
  [ "$got" = "$2" ]
}

render_chunk() {
  local idx=$1
  local start=$(( idx * CHUNK ))
  local out; out=$(printf 'chunks/chunk_%02d.mp4' $idx)
  if chunk_ok "$out" "$CHUNK"; then echo "[chunk $idx] done, skipping"; return 0; fi
  ( for ((i=start; i<start+CHUNK; i++)); do ./livecount $i $TOTAL 960 || exit 1; done ) \
    | ffmpeg -v error -y -f image2pipe -vcodec ppm -r 24 -i - \
        -c:v libx264 -preset veryfast -crf 12 -pix_fmt yuv420p "$out.tmp.mp4" \
    && mv "$out.tmp.mp4" "$out"
  if chunk_ok "$out" "$CHUNK"; then echo "[chunk $idx] OK"; else echo "[chunk $idx] BAD"; return 1; fi
}

worker() {
  local w=$1
  local c
  for ((c=w; c<NCHUNKS; c+=4)); do render_chunk $c || echo "[worker $w] chunk $c failed"; done
  echo "[worker $w] finished"
}

date +%s > render_start.txt
worker 0 & worker 1 & worker 2 & worker 3 &
wait
date +%s > render_end.txt
missing=0
for ((c=0; c<NCHUNKS; c++)); do
  out=$(printf 'chunks/chunk_%02d.mp4' $c)
  chunk_ok "$out" "$CHUNK" || { echo "MISSING/BAD: chunk $c"; missing=1; }
done
[ $missing -eq 0 ] && echo "CENSUS: all $NCHUNKS chunks verified" || echo "CENSUS: FAILURES PRESENT"
