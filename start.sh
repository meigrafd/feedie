#!/bin/bash

rm -f nohup.out
(nohup python3 feedie.py)& 2>&1 >/tmp/pybot
