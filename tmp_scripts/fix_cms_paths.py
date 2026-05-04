from pathlib import Path

files = [
    Path('admin_app/static/admin_app/js/admin_cms_scripts.js'),
    Path('admin_app/templates/admin_app/cms_settings.html')
]
for path in files:
    text = path.read_text(encoding='utf-8')
    new_text = text.replace('/admin/api/cms/', '/admin-panel/api/cms/')
    if text != new_text:
        path.write_text(new_text, encoding='utf-8')
        print(f'Updated {path}')
    else:
        print(f'No change needed for {path}')
