#!/bin/bash

FIREBASE_STORAGE=gs://umaaji-calculator.appspot.com

if [ -e result.json ]; then
  rm result.json
  echo removed old result.json
fi

scrapy crawl umaaji_calculator -o result.json

if [ -s result.json ]; then
  gsutil cp result.json ${FIREBASE_STORAGE}/result.json
fi
