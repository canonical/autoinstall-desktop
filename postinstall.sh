#!/bin/sh

# Install language packs for English
apt install -y $(check-language-support -l en)
