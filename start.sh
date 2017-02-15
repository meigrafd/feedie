#!/bin/bash

rm -f nohup.out
nohup python3 feedie.py start & >/dev/null 2>&1
