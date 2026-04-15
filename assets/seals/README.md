# Seal Images

Place your school seal images in this directory:

- **wmsu-seal.png** - Western Mindanao State University seal (main logo)
- **jab-seal.png** - JAB certification seal

These images will be automatically loaded and embedded in:

- Printed forms
- Downloaded PDF files

## Requirements

- Format: PNG or JPG
- Recommended size: 200x200 pixels or larger
- Transparent background recommended for PNG files

## How it works

1. Admin places the seal images in this directory
2. When students access the review/print page, seals are automatically loaded
3. Seals appear in the official form printout and PDF download
4. Students can optionally override with custom images via upload feature

## Configuration

Seal URLs can be modified in `recordkeeping_proj/settings.py`:

```python
WMSU_SEAL_URL = '/static/seals/wmsu-seal.png'
JAB_SEAL_URL = '/static/seals/jab-seal.png'
```
