#!/bin/bash
set -e

mkdir -p /app/data/
chown -R sesame:sesame /app/data/

su sesame -s /app/sesame