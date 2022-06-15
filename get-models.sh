#!/bin/bash
test_dir=./test

models_dir=$test_dir/models
mkdir -p $models_dir
python -c "import stanza; stanza.download(lang='fr', model_dir='${models_dir}', logging_level='info')" || echo "failed to download French model"
python -c "import stanza; stanza.download(lang='fr', package='ner', model_dir='${models_dir}', logging_level='info')" || echo "failed to download French model"
python -c "import stanza; stanza.download(lang='es', model_dir='${models_dir}', logging_level='info')" || echo "failed to download Spanish model"
python -c "import stanza; stanza.download(lang='es', package='ner', model_dir='${models_dir}', logging_level='info')" || echo "failed to download Spanish model"
echo "Models downloaded to ${models_dir}."
export STANZA_TEST_HOME=$test_dir

python -m spacy download fr_core_news_md
python -m spacy download es_core_news_md