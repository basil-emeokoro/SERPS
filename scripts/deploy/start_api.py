"""Portable Docker start: platform PORT, optional single-run migrations, no URL logs."""
import os
import subprocess
import sys


def main() -> int:
    try:
        port = int(os.environ.get('PORT', os.environ.get('SERPS_API_PORT', '8000')))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print('Invalid API port.', file=sys.stderr)
        return 1
    if os.environ.get('SERPS_RUN_MIGRATIONS', 'true').lower() == 'true':
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], check=True)
    command = [sys.executable, '-m', 'uvicorn', 'apps.api.app.main:app', '--host', '0.0.0.0',
               '--port', str(port), '--no-access-log', '--proxy-headers',
               '--forwarded-allow-ips', os.environ.get('SERPS_TRUSTED_PROXY_IPS', '127.0.0.1')]
    os.execv(sys.executable, command)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
