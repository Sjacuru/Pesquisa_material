# FILE: manage.py
# MODULE: support — Django Bootstrap CLI
# EPIC: Architecture — Application Entry Point
# RESPONSIBILITY: Define the local command and server bootstrap entry point for the scaffold.
# EXPORTS: Command-line bootstrap entry point.
# DEPENDS_ON: config/settings.py.
# ACCEPTANCE_CRITERIA:
#   - The file is reserved as the main local bootstrap entry point.
#   - No business logic or module behavior is implemented here.
# HUMAN_REVIEW: No.

import os
import sys


def main() -> None:
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError("Django is not installed or available in the active environment.") from exc
	execute_from_command_line(sys.argv)


if __name__ == "__main__":
	main()
