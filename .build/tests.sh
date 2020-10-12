#/bin/bash
set -e

pip install -r requirements.txt
pip install -r requirements-tests.txt
sed -i '' 's/POSTGRESQL_HOST=localhost/POSTGRESQL_HOST=postgres/g' .env.test
pytest
