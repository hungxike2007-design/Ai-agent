import zipfile
import xml.etree.ElementTree as ET
import sys

def get_docx_text(path):
    document = zipfile.ZipFile(path)
    xml_content = document.read('word/document.xml')
    document.close()
    tree = ET.XML(xml_content)
    namespace = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paragraphs = []
    for paragraph in tree.iter(namespace + 'p'):
        texts = [node.text
                 for node in paragraph.iter(namespace + 't')
                 if node.text]
        if texts:
            paragraphs.append(''.join(texts))
    return '\n'.join(paragraphs)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = get_docx_text(sys.argv[1])
        with open("docx_output.txt", "w", encoding="utf-8") as f:
            f.write(text)
