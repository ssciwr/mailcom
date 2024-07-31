#!/bin/bash
test_dir=./mailcom/test

models_dir=$test_dir/models
mkdir -p $models_dir
python -m spacy download fr_core_news_md
python -m spacy download es_core_news_md