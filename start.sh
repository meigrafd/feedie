#!/bin/bash

rm -f nohup.out
(nohup python3 feedie.py start)& 2>&1 >/tmp/pybot
