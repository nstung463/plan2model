#!/usr/bin/env bash
# Ghép các đoạn (chỉ hình) + track âm thanh tổng -> video cuối nhẹ, phát được mọi nơi.
set -e
cd /f/Project_Nhom_MSE/video/out
ls chunks/c*.mp4 | sort | sed "s#^#file '#; s#\$#'#" > chunks/list.txt
ffmpeg -v error -y -f concat -safe 0 -i chunks/list.txt -i audio_mix.m4a -map 0:v -map 1:a \
  -c:v copy -c:a copy -movflags +faststart -shortest Plan2Model_video.mp4
ffprobe -v error -show_entries format=duration,size,bit_rate -of default=nw=1 Plan2Model_video.mp4
