import os
import sys
import argparse

def audit_skills(skills_dir, local_dir=None):
    skills_dir = os.path.expanduser(skills_dir)
    if not os.path.isdir(skills_dir):
        print(f"Error: Directory not found: {skills_dir}")
        return False

    valid_skills = []
    missing_skill_md = []
    for d in sorted(os.listdir(skills_dir)):
        if d.startswith("."):
            continue
        path = os.path.join(skills_dir, d)
        if os.path.isdir(path):
            md_path = os.path.join(path, "SKILL.md")
            if os.path.isfile(md_path):
                valid_skills.append(d)
            else:
                missing_skill_md.append(d)

    print(f"[Audit] Found {len(valid_skills)} valid skills in {skills_dir}")
    if missing_skill_md:
        print(f"[Warning] Missing SKILL.md in: {missing_skill_md}")

    if local_dir:
        local_dir = os.path.expanduser(local_dir)
        if os.path.isdir(local_dir):
            broken_links = []
            for item in sorted(os.listdir(local_dir)):
                lpath = os.path.join(local_dir, item)
                if os.path.islink(lpath) and not os.path.exists(lpath):
                    broken_links.append(item)
            if broken_links:
                print(f"[Warning] Broken symlinks in {local_dir}: {broken_links}")
    return len(missing_skill_md) == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="~/.agents/skills")
    parser.add_argument("--local", default=None)
    args = parser.parse_args()
    success = audit_skills(args.target, args.local)
    sys.exit(0 if success else 1)
