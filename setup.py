from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {
    'packages': ["scrapy", "ankizlet", "chromedriver-win64", "PyQt5",
                 "genanki", "undetected_chromedriver", "selenium",
                 "twisted.internet"], 'excludes': []}

import sys

executables = [
    Executable('run.py', base="Win32GUI")
]

setup(name='ankizlet',
      version='1.3',
      description='Convert Quizlet cards to Anki',
      options={'build_exe': build_options},
      executables=executables)
