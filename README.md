# DrinkingBuddyServer

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv sync
```

## Running

```sh
uv run python -m DrinkingBuddyServer
```

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and fill in the values — `uv run` picks it up automatically.

| Variable | Description | Example |
|---|---|---|
| `DB_PATH` | SQLAlchemy DB URL | `sqlite:////data/drinkingBuddy.db` |
| `SECRET_KEY` | Flask session secret | `python -c "import secrets; print(secrets.token_hex())"` |
| `LDAP_URL` | LDAP server URL | `ldap://freeipa.lan.example.ch` |
| `LDAP_USER_SEARCH_BASE` | DN to search users under | `cn=users,cn=accounts,dc=example,dc=ch` |
| `LDAP_GROUP_SEARCH_BASE` | DN to search groups under | `cn=groups,cn=accounts,dc=example,dc=ch` |

## Admin interface

Available at `/admin`. Login requires membership in the `admins` LDAP group.

## Container

```sh
podman build -f Containerfile -t drinkingbuddyserver .
mkdir -p ./data
podman run -p 5000:5000 --env-file .env -v ./data:/data drinkingbuddyserver
```

The `/data` directory is where the SQLite database is stored. Mount a persistent directory there.
