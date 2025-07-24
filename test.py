import os

EXCLUDE_DIRS = {'venv','Resume', '__pycache__', '.git', '.idea', '.vscode', 'node_modules'}
EXCLUDE_FILES = {'.DS_Store'}

def print_tree(dir_path, prefix=""):
    entries = sorted(os.listdir(dir_path))
    entries = [e for e in entries if e not in EXCLUDE_FILES]

    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + entry)

        if os.path.isdir(path) and entry not in EXCLUDE_DIRS:
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(path, prefix + extension)

# 🔰 Lance ce script depuis la racine de ton projet :
if __name__ == "__main__":
    print_tree(".")
