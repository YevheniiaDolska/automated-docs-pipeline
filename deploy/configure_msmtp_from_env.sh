#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('/opt/veridoc/.env')
vals = {}
if p.exists():
    for ln in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = ln.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        vals[k.strip()] = v.strip().strip('"')
keys = [
    'VERIDOC_SMTP_HOST',
    'VERIDOC_SMTP_PORT',
    'VERIDOC_SMTP_USER',
    'VERIDOC_SMTP_PASSWORD',
    'VERIDOC_SMTP_FROM',
]
missing = [k for k in keys if not vals.get(k)]
if missing:
    Path('/opt/veridoc/deploy/SMTP_SETUP_REQUIRED.txt').write_text(
        'Missing SMTP env vars in /opt/veridoc/.env: ' + ', '.join(missing) + '\n'
        'Add them and re-run /opt/veridoc/deploy/configure_msmtp_from_env.sh\n',
        encoding='utf-8',
    )
    print('SMTP_ENV_MISSING:' + ','.join(missing))
else:
    host = vals['VERIDOC_SMTP_HOST']
    port = vals['VERIDOC_SMTP_PORT']
    user = vals['VERIDOC_SMTP_USER']
    pwd = vals['VERIDOC_SMTP_PASSWORD']
    sender = vals['VERIDOC_SMTP_FROM']
    cfg = (
        'defaults\n'
        'auth on\n'
        'tls on\n'
        'tls_trust_file /etc/ssl/certs/ca-certificates.crt\n'
        'logfile /var/log/msmtp.log\n\n'
        'account default\n'
        f'host {host}\n'
        f'port {port}\n'
        f'user {user}\n'
        f'password {pwd}\n'
        f'from {sender}\n'
    )
    Path('/etc/msmtprc').write_text(cfg, encoding='utf-8')
    Path('/etc/msmtprc').chmod(0o600)
    print('SMTP_CONFIGURED')
PY
if [ -f /opt/veridoc/deploy/SMTP_SETUP_REQUIRED.txt ]; then
  cat /opt/veridoc/deploy/SMTP_SETUP_REQUIRED.txt
fi
