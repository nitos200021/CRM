#!/usr/bin/env python3
"""
Скрипт для анализа Python файлов в проекте и автоматического обновления/понижения
библиотек до рекомендованных версий для обеспечения совместимости.

Как работает:
1. Рекурсивно проходит по указанной папке и находит все файлы с расширением .py.
2. С помощью модуля ast парсит файлы и собирает все импортируемые модули.
3. Сопоставляет имена модулей с именами пакетов (например, "flask" -> "Flask").
4. Сравнивает установленную версию пакета с рекомендованной.
5. Если пакет не установлен или установлена неверная версия, выполняется команда pip install для установки нужной версии.
"""

import os
import sys
import ast
import subprocess
import pkg_resources

def get_python_files(directory):
    """
    Рекурсивно ищет все файлы с расширением .py в заданной директории.
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(filename):
    """
    Парсит указанный Python файл и возвращает множество импортируемых модулей.
    Если возникла ошибка при парсинге, возвращает пустое множество.
    """
    imported_modules = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        tree = ast.parse(file_contents, filename=filename)
    except Exception as e:
        print(f"Ошибка при разборе {filename}: {e}")
        return imported_modules

    for node in ast.walk(tree):
        # Обработка инструкций import
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Берем только первое слово (например, "flask" из "flask.ext" или "flask_sqlalchemy")
                module_name = alias.name.split('.')[0]
                imported_modules.add(module_name)
        # Обработка инструкций from ... import ...
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                imported_modules.add(module_name)
    return imported_modules

def get_all_imports(directory):
    """
    Собирает все импортируемые модули из всех Python файлов в указанной директории.
    """
    files = get_python_files(directory)
    all_imports = set()
    for file in files:
        imports = extract_imports(file)
        all_imports.update(imports)
    return all_imports

def get_installed_version(package_name):
    """
    Получает версию установленного пакета с помощью pkg_resources.
    Если пакет не найден, возвращает None.
    """
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except pkg_resources.DistributionNotFound:
        return None

def update_package(package, version):
    """
    Выполняет установку указанной версии пакета с помощью pip.
    """
    print(f"Устанавливаю {package}=={version}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', f"{package}=={version}"])
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке {package}: {e}")

def main(project_directory):
# Словарь для сопоставления импортируемых модулей с именами pip-пакетов
module_to_package = {
    'flask': 'Flask',
    'flask_login': 'Flask-Login',
    'flask_wtf': 'Flask-WTF',
    'wtforms': 'WTForms',
    'flask_sqlalchemy': 'Flask-SQLAlchemy'
}

# Словарь с рекомендуемыми версиями для обеспечения совместимости
compatibility_config = {
    'Flask': '2.2.5',
    'Flask-Login': '0.6.2',
    'Flask-WTF': '0.14.3',
    'WTForms': '3.0.1',
    'Flask-SQLAlchemy': '3.0.5',
    # Дополнительно, если в проекте используются эти библиотеки:
    'PyMySQL': '1.0.3',
    'Werkzeug': '3.1.3',
    'MarkupSafe': '2.0.1'
}

    print("Сканирую Python файлы в проекте...")
    imported_modules = get_all_imports(project_directory)
    print(f"Найденные импортируемые модули: {imported_modules}")

    # Формируем множество пакетов для проверки (с учетом сопоставления модуль -> пакет)
    packages_to_check = {}
    for mod in imported_modules:
        pkg = module_to_package.get(mod.lower())
        if pkg:
            packages_to_check[pkg] = True

    print(f"Пакеты для проверки: {list(packages_to_check.keys())}")

    # Проверяем каждую библиотеку и обновляем/устанавливаем её до рекомендованной версии
    for package in packages_to_check.keys():
        rec_version = compatibility_config.get(package)
        if not rec_version:
            print(f"Не указана рекомендуемая версия для {package}. Пропускаю.")
            continue

        installed_version = get_installed_version(package)
        if installed_version is None:
            print(f"{package} не установлен. Устанавливаю версию {rec_version}...")
            update_package(package, rec_version)
        else:
            if installed_version != rec_version:
                print(f"{package} установлен в версии {installed_version}. Обновляю/понижаю до {rec_version}...")
                update_package(package, rec_version)
            else:
                print(f"{package} уже в рекомендуемой версии {rec_version}.")

    print("Обновление завершено. Все проверенные пакеты приведены к рекомендуемым версиям.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python update_deps.py <путь_к_проекту>")
        sys.exit(1)
    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"Указанная директория '{project_dir}' не существует или не является папкой.")
        sys.exit(1)
    main(project_dir)