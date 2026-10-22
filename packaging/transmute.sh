#!/bin/sh
# Installation data are immutable; app/paths.py chooses per-user writable state.
exec /opt/transmute/ConversorDeBases "$@"
