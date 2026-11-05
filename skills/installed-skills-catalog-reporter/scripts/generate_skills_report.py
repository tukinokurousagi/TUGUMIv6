import os
import glob
import yaml
import datetime
import argparse

def scan_and_generate_report(skills_dir, output_dir):
    skills_dir = os.path.expanduser(skills_dir)
    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    pattern = os.path.join(skills_dir, '*', 'SKILL.md')
    skill_files = sorted(glob.glob(pattern))

    catalog = []
    for filepath in skill_files:
        skill_id = os.path.basename(os.path.dirname(filepath))
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            parts = content.split('---', 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                name = meta.get('name', skill_id)
                desc = meta.get('description', '説明なし')
            else:
                name = skill_id
                desc = 'Frontmatter未定義'
        except Exception as e:
            name = skill_id
            desc = f'パース失敗: {str(e)}'

        catalog.append({'id': skill_id, 'name': name, 'desc': desc, 'path': filepath})

    today = datetime.datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'TUGUMIv6_全SKILL一覧カタログレポート_{today}.md')

    lines = [
        f'# TUGUMIv6 全SKILL一覧カタログレポート ({datetime.datetime.now().strftime("%Y-%m-%d")})',
        '',
        f'- **総スキル数**: {len(catalog)} 種類',
        f'- **走査対象ディレクトリ**: `{skills_dir}`',
        f'- **レポート生成日**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '',
        '## スキル一覧概要',
        '',
        '| # | スキル識別子 | 名称 | 概要 |',
        '|---|---|---|---|'
    ]

    for idx, item in enumerate(catalog, 1):
        lines.append(f'| {idx} | `{item["id"]}` | **{item["name"]}** | {item["desc"]} |')

    lines.append('')
    lines.append('## 詳細定義一覧')
    lines.append('')
    for idx, item in enumerate(catalog, 1):
        lines.append(f'### {idx}. {item["name"]} (`{item["id"]}`)')
        lines.append(f'- **定義ファイル**: `{item["path"]}`')
        lines.append(f'- **説明**: {item["desc"]}')
        lines.append('')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'Report successfully generated: {output_file} (Skills: {len(catalog)})')
    return output_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skills-dir', default='~/.agents/skills')
    parser.add_argument('--output-dir', default='/storage/emulated/0/TUGUMIDesk/AI・エージェント')
    args = parser.parse_args()
    scan_and_generate_report(args.skills_dir, args.output_dir)
