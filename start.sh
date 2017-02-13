#!/bin/bash

rm -f nohup.out
nohup python feedie.py start & >/dev/null 2>&1
