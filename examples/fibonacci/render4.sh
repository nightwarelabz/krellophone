#!/bin/bash
# Resumable chunked render of fibfilm4: 6696 frames in 168-frame chunks.
# A chunk counts as done only when ffprobe confirms its exact frame count.
# Re-running this script skips finished chunks.
cd ~/workspace/fibonacci || exit 1
mkdir -p film4
TOTAL=6696
CHUNK=168
NCHUNKS=$(( (TOTAL + CHUNK - 1) / CHUNK ))

chunk_frames() { # $1=chunk idx -> expected frame count
  local start=$(( $1 * CHUNK ))
  local n=$(( TOTAL - start ))
  [ $n -gt $CHUNK ] && n=$CHUNK
  echo $n
}

chunk_ok() { # $1=file $2=expected
  [ -f "$1" ] || return 1
  local got
  got=$(ffprobe -v error -count_frames -select_streams v:0 \
        -show_entries stream=nb_read_frames -of csv=p=0 "$1" 2>/dev/null)
  [ "$got" = "$2" ]
}

render_chunk() { # $1=chunk idx
  local idx=$1
  local start=$(( idx * CHUNK ))
  local n; n=$(chunk_frames $idx)
  local out; out=$(printf 'film4/chunk_%03d.mp4' $idx)
  if chunk_ok "$out" "$n"; then
    echo "[chunk $idx] already done ($n frames), skipping"
    return 0
  fi
  rm -f "$out.tmp.mp4"
  local attempt=1
  while [ $attempt -le 3 ]; do
    echo "[chunk $idx] rendering frames $start..$((start+n-1)) (attempt $attempt)"
    ( for ((i=start; i<start+n; i++)); do ./fibfilm4 $i $TOTAL 960 || exit 1; done ) \
      | ffmpeg -v error -y -f image2pipe -vcodec ppm -r 24 -i - \
          -c:v libx264 -preset veryfast -crf 12 -pix_fmt yuv420p "$out.tmp.mp4"
    if [ -f "$out.tmp.mp4" ]; then
      mv "$out.tmp.mp4" "$out"
      if chunk_ok "$out" "$n"; then
        echo "[chunk $idx] OK ($n frames)"
        return 0
      fi
    fi
    echo "[chunk $idx] attempt $attempt failed verification"
    rm -f "$out"
    attempt=$((attempt+1))
  done
  echo "[chunk $idx] FAILED after 3 attempts"
  return 1
}

worker() { # $1=worker id 0..3 : contiguous quarter of chunks
  local w=$1
  local per=$(( (NCHUNKS + 3) / 4 ))
  local c0=$(( w * per ))
  local c1=$(( c0 + per ))
  [ $c1 -gt $NCHUNKS ] && c1=$NCHUNKS
  local c
  for ((c=c0; c<c1; c++)); do
    render_chunk $c || echo "[worker $w] chunk $c failed permanently"
  done
  echo "[worker $w] finished its range $c0..$((c1-1))"
}

worker 0 &
worker 1 &
worker 2 &
worker 3 &
wait
echo "ALL WORKERS DONE"
# Final census
missing=0
for ((c=0; c<NCHUNKS; c++)); do
  out=$(printf 'film4/chunk_%03d.mp4' $c)
  n=$(chunk_frames $c)
  if ! chunk_ok "$out" "$n"; then echo "MISSING/BAD: chunk $c"; missing=1; fi
done
[ $missing -eq 0 ] && echo "CENSUS: all $NCHUNKS chunks verified" || echo "CENSUS: FAILURES PRESENT"
