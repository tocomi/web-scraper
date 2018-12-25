#!/bin/bash

if [ -e result.json ]; then
  rm result.json
  echo removed old result.json
fi

scrapy crawl umaaji_calculator -o result.json

gsutil cp result.json ${FIREBASE_STORAGE}/result.json
