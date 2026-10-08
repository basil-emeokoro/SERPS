"""Compatibility entry point: provision staff access, never fake candidate enrolment.

Migrate first. Supply SERPS_BOOTSTRAP_* variables; the historical shared demo
password/account seeder is retired. Candidates must use normal registration,
facial enrolment, institutional approval and assignment workflows.
"""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'deploy' / 'bootstrap.py'), run_name='__main__')
