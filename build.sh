#!/usr/bin/env bash
set -o errexit

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Creating superuser if not exists..."
python manage.py create_superuser

echo "==> Creating media directories on disk..."
python manage.py shell -c "
import os
from django.conf import settings
for d in [
    settings.MEDIA_ROOT,
    os.path.join(str(settings.MEDIA_ROOT), 'profiles'),
    os.path.join(str(settings.MEDIA_ROOT), 'kyc', 'id'),
    os.path.join(str(settings.MEDIA_ROOT), 'kyc', 'address'),
    os.path.join(str(settings.MEDIA_ROOT), 'kyc', 'selfie'),
    os.path.join(str(settings.MEDIA_ROOT), 'loans', 'income'),
    os.path.join(str(settings.MEDIA_ROOT), 'loans', 'statements'),
    os.path.join(str(settings.MEDIA_ROOT), 'loans', 'utility'),
]:
    os.makedirs(d, exist_ok=True)
    print(f'  Created: {d}')
print('Media directories ready.')
"

echo "==> Build complete!"
