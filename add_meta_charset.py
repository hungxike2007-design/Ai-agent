import os
import re

for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if meta charset exists
            if not re.search(r'<meta\s+charset=[\"\'\s]?UTF-8[\"\'\s]?', content, re.IGNORECASE):
                # Insert right after <head>
                content = re.sub(r'(<head[^>]*>)', r'\1\n    <meta charset="UTF-8">', content, count=1, flags=re.IGNORECASE)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Added meta charset to {filepath}')
