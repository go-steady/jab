from invoke import task, run


@task
def mutmut_test(path):
    run(f"python -m  pytest test/ && mypy jab/ --strict --ignore-missing-imports")
