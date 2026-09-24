import ast
import os
import sys

def get_imports(filepath):
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return imports

if __name__ == '__main__':
    all_imports = set()
    for directory in ['app', 'alembic', 'tests']:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    all_imports.update(get_imports(filepath))
    
    # Filter out standard library modules
    import sysconfig
    std_lib = sysconfig.get_paths()['stdlib']
    std_modules = set()
    for f in os.listdir(std_lib):
        if f.endswith('.py'):
            std_modules.add(f[:-3])
        elif os.path.isdir(os.path.join(std_lib, f)):
            std_modules.add(f)
    std_modules.add('sys')
    std_modules.add('os')
    std_modules.add('typing')
    std_modules.add('datetime')
    std_modules.add('enum')
    std_modules.add('json')
    std_modules.add('re')
    std_modules.add('math')
    std_modules.add('random')
    std_modules.add('uuid')
    std_modules.add('time')
    std_modules.add('hashlib')
    std_modules.add('base64')
    std_modules.add('collections')
    std_modules.add('functools')
    std_modules.add('itertools')
    std_modules.add('io')
    std_modules.add('logging')
    std_modules.add('pathlib')
    std_modules.add('contextlib')
    std_modules.add('dataclasses')
    std_modules.add('ast')
    std_modules.add('sysconfig')
    std_modules.add('urllib')

    third_party = all_imports - std_modules
    
    print("Found Third Party Imports:")
    for imp in sorted(list(third_party)):
        print(imp)
