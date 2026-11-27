#!/bin/bash
# Chạy tiếp train U-Net; nếu tiến trình crash thì tự chạy lại từ checkpoint (tối đa 6 lần).
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
python -u unet_wall.py train 3000 --from-weights=1000 >> output/unet_train.log 2>&1
for i in 1 2 3 4 5 6; do
  grep -q '"train_sec"' output/unet_train.log && break
  echo "### restart $i (exit code truoc: $?)" >> output/unet_train.log
  if [ -f models/unet_wall_ckpt.pt ]; then python -u unet_wall.py train 3000 >> output/unet_train.log 2>&1
  else python -u unet_wall.py train 3000 --from-weights=1000 >> output/unet_train.log 2>&1; fi
done
tail -30 output/unet_train.log
