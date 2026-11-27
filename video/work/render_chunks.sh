#!/usr/bin/env bash
# Render từng đoạn 60 s; mỗi đoạn dùng bản index riêng, ẩn (data-hidden) các cảnh không giao với đoạn
# để renderer không phải tách khung những clip nằm ngoài đoạn.
cd /f/Project_Nhom_MSE/video/hf || exit 1
export TMP=F:/tmp_hf TEMP=F:/tmp_hf
TOTAL=$(python -c "import re;print(re.search(r'data-composition-id=\"main\" data-start=\"0\" data-duration=\"([0-9.]+)\"',open('index.html',encoding='utf-8').read()).group(1))")
OUT=/f/Project_Nhom_MSE/video/out
mkdir -p "$OUT/chunks"
s=0; i=0
while python -c "import sys;sys.exit(0 if $s < $TOTAL - 0.01 else 1)"; do
  e=$(python -c "print(min($s+60,$TOTAL))")
  f=$(printf "%s/chunks/c%02d.mp4" "$OUT" $i)
  if [ ! -s "$f" ]; then
    PYTHONUTF8=1 python - "$s" "$e" <<'EOF'
import re, sys
s, e = float(sys.argv[1]), float(sys.argv[2])
h = open("index.html", encoding="utf-8").read()
def fix(m):
    tag = m.group(0)
    a = float(re.search(r'data-start="([0-9.]+)"', tag).group(1)); d = float(re.search(r'data-duration="([0-9.]+)"', tag).group(1))
    if a + d <= s - 0.5 or a >= e + 0.5:
        return tag.replace("<div ", '<div data-hidden="true" ', 1)
    return tag
h = re.sub(r'<div id="s[0-9]+" data-composition-id="s[0-9]+"[^>]*>', fix, h)
open("index_chunk.html", "w", encoding="utf-8").write(h)
EOF
    echo "CHUNK $i $s-$e start $(date +%T)"
    npx hyperframes render -c index_chunk.html -o "$f" --start $s --end $e --crf 18 --sdr --workers ${WORKERS:-3} > "/f/Project_Nhom_MSE/video/work/render_c$i.log" 2>&1
    rc=$?
    if [ $rc -ne 0 ] || [ ! -s "$f" ]; then echo "CHUNK $i FAILED rc=$rc"; exit 1; fi
    echo "CHUNK $i done $(date +%T) $(du -h "$f" | cut -f1) free=$(df -h /f | tail -1 | awk '{print $4}')"
  fi
  s=$e; i=$((i+1))
done
echo "ALL CHUNKS DONE"
