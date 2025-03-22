import os

def print_tree(startpath):
    for root, dirs, files in os.walk(startpath):
        # 'migrations' ve '__pycache__' ve .git dizinlerini dışarıda bırakıyor (tree çalışmıyor diye yazdım)
        dirs[:] = [d for d in dirs if d not in ['migrations', '__pycache__','.git']]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}{os.path.basename(root)}/")
        
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

print_tree(".")


# TODO: Bu dosya set project finish demeden önce silincek