import io
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = {'PNG', 'JPEG', 'WEBP', 'GIF'}
MAX_PIXELS = 40_000_000


def sanitize_image(uploaded_file):
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f'Arquivo maior que {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB.'
        )

    try:
        probe = Image.open(uploaded_file)
        image_format = (probe.format or '').upper()
        if image_format not in ALLOWED_FORMATS:
            raise ValidationError('Formato de imagem nao permitido.')
        if probe.width * probe.height > MAX_PIXELS:
            raise ValidationError('Dimensoes da imagem excedem o limite permitido.')
        probe.verify()
    except (UnidentifiedImageError, OSError):
        raise ValidationError('Arquivo corrompido ou nao e uma imagem valida.')
    finally:
        uploaded_file.seek(0)

    try:
        image = Image.open(uploaded_file)
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValidationError('Arquivo corrompido ou nao e uma imagem valida.')

    if image.mode not in ('RGB', 'RGBA', 'L'):
        image = image.convert('RGB')

    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)

    name = default_storage.save(f'avatars/{uuid.uuid4().hex}.png', ContentFile(buffer.read()))
    return name
