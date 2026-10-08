"""Run only once against an explicitly selected fresh staging database."""
import os
import sys
from serps_pop.infrastructure.database import SessionLocal
from serps_pop.operations.bootstrap import provision


def main() -> int:
    keys = ('INSTITUTION_CODE', 'INSTITUTION_NAME', 'EMAIL', 'FULL_NAME', 'PASSWORD')
    values = {key.lower(): os.environ.get('SERPS_BOOTSTRAP_' + key, '') for key in keys}
    if os.environ.get('SERPS_BOOTSTRAP_CONFIRM') != 'fresh-database' or not all(values.values()):
        print('Bootstrap refused: supply all SERPS_BOOTSTRAP variables and explicit fresh-database confirmation.', file=sys.stderr)
        return 1
    try:
        with SessionLocal.begin() as db:
            provision(db, **values)
    except Exception:
        # SQL/driver exceptions can contain credentials or bound personal data.
        print('Bootstrap failed; transaction rolled back. Verify migrations, fresh database and provisioning inputs privately.', file=sys.stderr)
        return 1
    print('Initial system administrator provisioned; no candidate, biometric bypass, assignment or examination session created.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
