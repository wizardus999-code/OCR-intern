import platform
from invoke import task

@task
def format(c):
    c.run("python -m black .")
    c.run("python -m ruff --fix .")

@task
def lint(c):
    c.run("python -m ruff .")

@task
def test(c):
    c.run("python -m pytest -q")

@task
def fetch_tessdata(c):
    if platform.system() == "Windows":
        c.run("powershell -ExecutionPolicy Bypass -File scripts/fetch_tessdata.ps1")
    else:
        print("Install tesseract + ara/fra via your package manager.")
