# GitLab groups filling with users

Automatically recursively adding a list of users to all GitLab groups.

This can be useful for GitLab administration when you need to add service
accounts to all groups, such as dependabot, sonarqube, and other robot
accounts for automation.

You are expected to run once or run on a schedule.

## Environment Variables

* **`GITLAB_URL`**=`https://gitlab.zyfra.com` - GitLab server URL
* **`GITLAB_PRIVATE_TOKEN=`**=`None` - Private access token. Normal access will
  allow you to grant rights no higher than the existing one and only for
  available groups. To manage an entire GitLab instance, it is better
  to use a token with sudo rights
* **`GITLAB_FILLING_USERS`**=`[]` Comma-separated list of GitLab user
  IDs to add to groups.  
  Example: `GITLAB_FILLING_USERS=13,14,22`
* **`GITLAB_USERS_ACCESS_LEVEL`**=`30` - Access level to be assigned to users
  * 10 - Guest
  * 20 - Reporter
  * 30 - Developer _(default)_
  * 40 - Mainteiner
  * 50 - Owner
* **`GITLAB_EXCLUDE_GROUPS`**=`[]` Comma-separated list of GitLab groups to be
  ignored at run time.  
  Example: `GITLAB_EXCLUDE_GROUPS=10,42`
* **`SKIP_BLANK_GROUPS`**=`True` - Skip adding users to empty groups
  (groups that have no projects)
* **`SKIP_NESTED_GROUPS`**=`True` - Skip adding users to nested groups, the
  user will inherit access from the parent group anyway.
* **`LOG_LEVEL`**=`INFO`

## Container Image

* [`docker pull ghcr.io/woozymasta/gitlab-groups-filling-with-users:latest`](https://github.com/WoozyMasta/gitlab-groups-filling-with-usersp/pkgs/container/gitlab-groups-filling-with-users)
* [`docker pull quay.io/woozymasta/gitlab-groups-filling-with-users:latest`](https://quay.io/repository/woozymasta/gitlab-groups-filling-with-users)
* [`docker pull docker.io/woozymasta/gitlab-groups-filling-with-users:latest`](https://hub.docker.com/r/woozymasta/gitlab-groups-filling-with-users)

## Run Locally

Clone this repository and go into it, run:

```bash
python -m venv .venv
pip install --upgrade pip
pip install --upgrade wheel
pip install --upgrade --requirement requirements.txt
. .venv/bin/activate
cp .env .env.example
editor .env
./app.py
```
