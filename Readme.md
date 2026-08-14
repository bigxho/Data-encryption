# Protection Data

A small Django application for storing private documents in an encrypted, user-scoped vault.

> [!IMPORTANT]
> This repository is an educational, early-stage prototype. It is **not production-ready** and must not be used to store real personal, medical, financial, or otherwise sensitive data until the issues in [Security and current limitations](#security-and-current-limitations) have been addressed.

## Overview

Protection Data lets authenticated users upload and retrieve private documents. Uploaded files are encrypted before they are written to local storage, while access is restricted to the account that owns each document.

The project demonstrates several useful security-oriented patterns:

- per-user document ownership;
- authenticated encryption of uploaded files with Fernet;
- encrypted storage of the Italian tax code (`codice_fiscale`);
- SHA-256 fingerprints for integrity checks;
- configurable download limits;
- login rate limiting;
- security-event logging model;
- upload validation for file type and size;
- Django admin integration;
- a Bootstrap-based responsive interface.

## Technology stack

- Python 3.10+
- Django 5.2
- SQLite for local development
- `cryptography` / Fernet
- `django-fernet-fields`
- `django-ratelimit`
- `python-dotenv`
- Bootstrap 5
- Optional Docker Compose and Traefik deployment template

## How it works

1. A user signs in through Django authentication.
2. The user uploads a PDF, JPG, or PNG file of up to 5 MB.
3. The application calculates the SHA-256 digest of the original content.
4. The file is encrypted in memory with Fernet and stored under a randomized path.
5. The database stores the owner, encrypted tax code, file path, digest, upload date, and download counters.
6. On an authorized download, the file is decrypted in memory and returned to its owner.

Fernet provides authenticated symmetric encryption: confidentiality and tamper detection are checked together. It should be described as **Fernet encryption**, not simply as “AES-256.”

## Project structure

```text
.
├── manage.py
├── genkeyf.py
├── docker-compose.yml
├── project_encryption/          # Django project configuration
├── patient_encryption/          # Models, forms, views, URLs and admin
│   ├── management/commands/     # File-integrity audit command
│   └── migrations/
├── templates/                   # Authentication and vault templates
└── staticfiles/                 # Collected Django admin assets
```

## Local setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd encryption_data_main
```

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install the dependencies

Install the project dependencies from the included requirements file:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project currently relies on the legacy `django-fernet-fields` package and compatibility shims. A future release should migrate the encrypted model field to a maintained Django 5.2-compatible package and remove those shims.

### 4. Create the environment file

Generate a Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Generate a Fernet key:

```bash
python genkeyf.py
```

Create `.env` in the project root:

```dotenv
SECRET_KEY=replace-with-a-new-django-secret-key
FERNET_KEY=replace-with-a-new-fernet-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

Never commit `.env`, the Fernet key, a production database, or uploaded documents. Losing `FERNET_KEY` makes files encrypted with that key unrecoverable.

### 5. Normalize the package references

The archive currently contains the Django project package `project_encryption` and the app package `patient_encryption`, but some imports still refer to earlier names (`pro_enc`, `paz_enc`, and `patient_ecryption`). Update those references consistently before running Django:

- use `project_encryption.settings`, `project_encryption.urls`, `project_encryption.wsgi`, and `project_encryption.asgi`;
- import application code from `patient_encryption`;
- include `patient_encryption.urls` in the root URL configuration.

### 6. Create migrations and initialize the database

```bash
python manage.py makemigrations patient_encryption
python manage.py migrate
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The administration area is available at <http://127.0.0.1:8000/admin/>.

## Integrity audit

The repository includes a custom Django management command intended to scan stored documents:

```bash
python manage.py audit_files
```

The current implementation needs correction before it is reliable: stored files are encrypted, while the saved digest is calculated from the original plaintext. The audit must therefore decrypt each file before comparing its SHA-256 digest, or store and explicitly verify a separate ciphertext digest.

## Docker and Traefik

`docker-compose.yml` is currently a deployment template, not a complete build configuration. It expects:

- an existing image named `p_enc:latest`;
- an external Docker network named `proxy`;
- a configured Traefik instance and certificate resolver;
- the `MY_DOMAIN` environment variable.

A production-ready container setup still needs a `Dockerfile`, a WSGI server such as Gunicorn, correct persistent paths for the database and media, static-file handling, health checks, and secure runtime configuration.

## Security and current limitations

Before any real-world deployment, address at least the following:

- remove the commented Django secret from `settings.py` and rotate it if it has ever been used;
- fix the inconsistent project/app module names described above;
- add reproducible dependency metadata and verify Django 5.2 compatibility;
- add the missing initial application migration;
- configure encrypted-field key management explicitly and document key rotation;
- never expose decryption exception details to clients;
- validate file content using MIME/signature inspection, not only the extension;
- sanitize download filenames and preserve the original filename separately;
- make download-limit updates atomic to prevent concurrent bypasses;
- complete and enable security logging for successful and denied operations;
- configure trusted reverse-proxy headers before accepting `X-Forwarded-For`;
- enable HTTPS, secure cookies, HSTS, CSRF trusted origins, and production host settings;
- review the duplicate download view and duplicated model properties;
- implement real integrity verification in the model/admin/audit command;
- add automated tests for authorization, encryption, tampering, rate limiting, and concurrency;
- replace SQLite with an appropriate managed database for multi-user production use;
- keep encrypted media outside any directly served public directory;
- establish backups that protect the database, ciphertext, and encryption keys separately.

The `docker-compose.yml` file also uses Node-oriented variables and an invalid persistence mapping for this Django layout; review it before deployment.

## Testing

The test module is currently only a placeholder. Once tests are added, run them with:

```bash
python manage.py test
```

Recommended first test cases:

- users cannot list or download another user’s documents;
- invalid formats and files larger than 5 MB are rejected;
- ciphertext cannot be read as plaintext from storage;
- modified ciphertext fails authentication;
- the download limit cannot be exceeded by concurrent requests;
- missing or incorrect encryption keys fail safely;
- login throttling returns a controlled response.

## Roadmap

- [ ] Correct package names and make the application start cleanly
- [ ] Add `requirements.txt` or `pyproject.toml`
- [ ] Add the initial migration
- [ ] Add a complete Docker image and production Compose configuration
- [ ] Implement reliable integrity auditing
- [ ] Add atomic download counters and complete audit logging
- [ ] Add automated security and authorization tests
- [ ] Add key rotation and recovery procedures
- [ ] Restore and test optional WebAuthn/MFA support
- [ ] Add continuous integration and dependency scanning

## Contributing

Contributions are welcome. Please open an issue before a large change, keep pull requests focused, and include tests for security-sensitive behavior.

When reporting a vulnerability, avoid posting exploit details or sensitive data in a public issue. Add a private security contact or GitHub Security Policy (`SECURITY.md`) before accepting external reports.

## License

This project is free and open source under the MIT License. See [`License.md`](License.md) for the complete license text.

## Disclaimer

This software is provided for learning and experimentation. Encryption features alone do not make a system compliant with GDPR, healthcare regulations, or other legal and security requirements. Operators remain responsible for threat modeling, access control, key management, backups, monitoring, privacy obligations, and independent security review.
