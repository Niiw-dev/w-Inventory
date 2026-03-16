#!/bin/bash
echo "BUILD START"

python3.9 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# instalar node si existe package.json
if [ -f package.json ]; then
    npm install
    npx gulp
fi

python manage.py collectstatic --noinput --clear

echo "BUILD END"