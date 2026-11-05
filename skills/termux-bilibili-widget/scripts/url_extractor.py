import sys
import re

def smart_extract_url(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^(https?://)+', r'https://', text)
    m = re.search(r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+', text)
    if m:
        return m.group(0).rstrip('.,;:!?')
    m = re.search(r'(?:^|[\s【\[（(])(b23\.tv/[a-zA-Z0-9]+)', text)
    if m:
        return f'https://{m.group(1).rstrip(".,;:!?")}'
    m = re.search(r'(?:^|[\s【\[（(])((?:www\.)?bilibili\.com/[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)', text)
    if m:
        return f'https://{m.group(1).rstrip(".,;:!?")}'
    m = re.search(r'\b(BV1[0-9a-zA-Z]{9}|av\d+)\b', text, re.IGNORECASE)
    if m:
        return f'https://www.bilibili.com/video/{m.group(1)}'
    return ''

if __name__ == '__main__':
    raw_input = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    extracted = smart_extract_url(raw_input)
    if not extracted:
        sys.exit(1)
    print(extracted)