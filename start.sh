#!/bin/bash

rm -f nohup.out
nohup nice -n 19 python feedie.py start & >/dev/null 2>&1
