FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src/ src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    uv pip install --no-deps .

# Required environment variables:
#   DB_PATH                 SQLAlchemy DB URL         e.g. sqlite:////data/drinkingBuddy.db
#   SECRET_KEY              Flask session secret       (generate with: python -c "import secrets; print(secrets.token_hex())")
#   LDAP_URL                LDAP server URL            e.g. ldap://ldap.lan.posttenebraslab.ch
#   LDAP_USER_SEARCH_BASE   DN to search users under   e.g. ou=users,dc=posttenebraslab,dc=ch
#   LDAP_GROUP_SEARCH_BASE  DN to search groups under  e.g. ou=groups,dc=posttenebraslab,dc=ch

EXPOSE 5000
ENTRYPOINT ["uv", "run", "python", "-m", "DrinkingBuddyServer"]
