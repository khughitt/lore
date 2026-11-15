"""Run lore without installing a Python distribution."""
import os
import sys
sys.dont_write_bytecode = True
from .cli import main

raise SystemExit(main(sys.argv[1:], os.environ, os.getcwd()))
