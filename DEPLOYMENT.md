# Deployment

## Overview

The app runs as a Docker container on a single Timeweb VPS. Two environments share the same server:

| Environment | Branch trigger | Port | Firebase project |
|---|---|---|---|
| NOP (staging) | push to `main` | `8502` | `m8-team-stg` |
| PROD | push to `release/**` | `8503` | `m8-team-prod` |

Docker images are built on GitHub Actions and pushed to GitHub Container Registry (GHCR) at `ghcr.io/kuzalex993/m8_team`.
a
The existing `streamlit_app` container (legacy) runs on port `8501` and is untouched.

---

## One-time manual setup

These steps are done once and do not repeat on each deploy.

### 1. Create a deploy SSH user on the server

```bash
# as root on Timeweb
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
```

### 2. Generate a deploy SSH key pair (local machine)

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/m8_deploy -N ""
```

Install the public key on the server:

```bash
# as root on Timeweb
echo "<contents of ~/.ssh/m8_deploy.pub>" >> /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
```

### 3. Place Firebase credentials on the server

```bash
# copy from local machine
scp src/credentials/m8-team-stg-firebase.json deploy@<server-ip>:/tmp/stg-creds.json

# on the server
mkdir -p /opt/m8
mv /tmp/stg-creds.json /opt/m8/stg-firebase.json
```

For PROD, repeat with the prod credentials file:

```bash
scp src/credentials/m8-team-prod-firebase.json deploy@<server-ip>:/tmp/prod-creds.json
# on the server
mv /tmp/prod-creds.json /opt/m8/prod-firebase.json
```

### 4. Create environment files on the server

NOP (`/opt/m8/nop.env`):

```bash
python3 << 'EOF'
lines = [
    'APP_ENV=stg\n',
    'BOT_TOKEN=<nop bot token>\n',
    'T_BOT_ENDPOINT=<nop endpoint>\n',
]
with open('/opt/m8/nop.env', 'w') as f:
    f.writelines(lines)
EOF
```

PROD (`/opt/m8/prod.env`) — same structure with prod values and `APP_ENV=prod`.

> Firebase credentials are **not** stored in env files — they are mounted as files (see step 3).

### 5. Add GitHub repository secrets

Go to: repo → **Settings → Secrets and variables → Actions → Repository secrets**

| Secret | Value |
|---|---|
| `TIMEWEB_HOST` | server IP address |
| `TIMEWEB_USER` | `deploy` |
| `TIMEWEB_SSH_KEY` | contents of `~/.ssh/m8_deploy` (private key) |
| `GHCR_PAT` | GitHub Personal Access Token with `read:packages` scope |

The `GHCR_PAT` is used by the Timeweb server to pull images from GHCR.
Create it at: GitHub → **Settings → Developer settings → Personal access tokens → Tokens (classic)**.

---

## Automated pipeline

### NOP deploy (`deploy-stg.yml`)

**Trigger:** push to `main` (i.e. after a PR is merged)

**Steps:**
1. Run `pytest` as a safety gate
2. Build Docker image from the repo
3. Push image to `ghcr.io/kuzalex993/m8_team:nop`
4. SSH into Timeweb as `deploy`
5. Pull the new image
6. Stop and remove the old `m8-nop` container
7. Start a new `m8-nop` container:
   - port `8502:8080`
   - env file: `/opt/m8/nop.env`
   - Firebase credentials mounted from `/opt/m8/stg-firebase.json`

### PROD deploy (`deploy-prod.yml`)

**Trigger:** push to any `release/**` branch (e.g. `release/1.0`)

**Steps:** same as NOP, but:
- Image tag: `ghcr.io/kuzalex993/m8_team:prod`
- Container name: `m8-prod`
- Env file: `/opt/m8/prod.env`
- Firebase credentials mounted from `/opt/m8/prod-firebase.json`

---

## How environments are differentiated

The same Docker image is used for all environments. The environment is selected at runtime via:

- `APP_ENV` in the env file (`stg` or `prod`) — controls which Firebase credentials file the app reads
- Firebase credentials file mounted from the server into the container at `/app/src/credentials/m8-team-<env>-firebase.json`

The `src/entrypoint.sh` script runs before Streamlit starts. If `FIREBASE_CREDENTIALS` env var is set, it writes the credentials to the expected path. If the file is already mounted (current setup), it skips writing.

---

## Checking container status on the server

```bash
# list running containers
docker ps

# view NOP logs
docker logs m8-nop --tail 50

# view PROD logs
docker logs m8-prod --tail 50
```
