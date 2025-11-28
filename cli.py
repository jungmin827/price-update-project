"""Command-line entrypoint for the project.

Provides a simple `--info` command and a `run` command placeholder.
"""
import argparse
from project.config.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Project CLI")
    parser.add_argument("command", nargs="?", default="info", choices=["info", "run"])
    args = parser.parse_args()
    if args.command == "info":
        print("SPREADSHEET_ID:", settings.SPREADSHEET_ID)
        print("SERVICE_ACCOUNT_FILE:", settings.SERVICE_ACCOUNT_FILE)
    elif args.command == "run":
        try:
            from project.runner import run_once

            print("Starting run_once()...")
            run_once()
            print("Run finished.")
        except Exception as e:
            print("Error running project.runner.run_once:", e)


if __name__ == "__main__":
    main()
