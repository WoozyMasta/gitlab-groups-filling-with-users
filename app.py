#!/usr/bin/env python3

'''
Copyright 2022 Maxim Levchenko <maxim.levchenko@zyfra.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
'''

import os
import sys
import time
import dotenv
import logging
import gitlab


class env(object):
    def __init__(self, key: str, alt_key: str = None, default: str = None):
        """
        Load environment variable
        """
        self.key = key
        self.alt_key = alt_key
        self.default = default

        if alt_key is not None:
            self.alt_value = os.environ.get(alt_key, None)
        else:
            self.alt_value = None

        self.value = os.environ.get(
            key, self.alt_value if self.alt_value is not None else default)

        pass

    def env(self) -> str:
        """
        Return environment variable value
        """
        return self.value

    def required(self) -> str:
        """
        Return required environment variable value or critical exit
        """
        if self.value is not None:
            return self.value

        logging.fatal(f'Required environment variable "{self.key}" not set!')
        sys.exit()

    def int(self) -> int:
        """
        Return int variable value
        """
        if not self.value:
            return self.default
        return int(self.value)

    def boolean(self) -> bool:
        """
        Return bool variable value
        """
        if not self.value:
            return self.default
        return str(self.value).lower() in ("true", "t", "yes", "y", "on", "1")

    def list(self, separator: str = ',') -> list:
        """
        Return list of char separated string
        """
        if not self.value:
            return []
        return self.value.split(separator)


def load_dotenv(path: str = '.env'):
    """
    Load environmet variables from .env file
    """
    if os.path.isabs(path):
        dotenv.load_dotenv(path)
    else:
        dotenv.load_dotenv(os.path.join(os.getcwd(), path))


def loglevel(default: str = 'info'):
    loglevel = env('LOG_LEVEL', default=default).value.upper()
    if loglevel != 'DEBUG':
        logformat = '%(asctime)-15s [%(levelname)s] %(message)s'
        logging.basicConfig(
            level=loglevel, format=logformat, datefmt='%Y-%m-%d %H:%M')
    else:
        logformat = '%(asctime)-15s [%(levelname)s] %(module)s '
        logformat += '(%(process)d:%(threadName)s) %(message)s'
        logging.basicConfig(level=loglevel, format=logformat)


def login_gitlab(gitlab_url: str, gitlab_token: str) -> object:
    """
    Login in GitLab
    """

    try:
        gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)
        gl.auth()
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logging.fatal(
            f'Can\'t login to GitLab "{gitlab_url}" {e.error_message}')
        sys.exit()
    except Exception as e:
        logging.fatal(f'Can\'t connect to GitLab "{gitlab_url}" {e}')
        sys.exit()

    logging.info(f'Success logged in Gitlab "{gitlab_url}"')
    return gl


def main():
    # Connect to GitLab
    gitlab_url = env('GITLAB_URL', gitlab.const.DEFAULT_URL).value
    gitlab_token = env('GITLAB_PRIVATE_TOKEN').required()
    gl = login_gitlab(gitlab_url, gitlab_token)

    # Load users list
    users = sorted(set(env('GITLAB_FILLING_USERS').list()))
    # Check user exist in gitlab
    for i, val in enumerate(users):
        try:
            u = gl.users.get(val)
            logging.info(f'User "{u.username}" found and will be used')
        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == 404:
                logging.error(f'User "{val}" ignored, is not exist in GitLab')
                users.pop(i)
            else:
                logging.fatal(f'Error check user "{val}" in GitLab {e}')
                sys.exit()

    # Load other env
    exclude_groups = sorted(set(env('GITLAB_EXCLUDE_GROUPS').list()))
    skip_blank = env('SKIP_BLANK_GROUPS', default=True).boolean()
    skip_nested = env('SKIP_NESTED_GROUPS', default=True).boolean()

    # Get acces level
    access_level = env(
        'GITLAB_USERS_ACCESS_LEVEL',
        default=gitlab.const.DEVELOPER_ACCESS).int()
    levels = {
        0: "None",
        10: "Guest",
        20: "Reporter",
        30: "Developer",
        40: "Mainteiner",
        50: "Owner"
    }
    # Check access level is correct
    if access_level not in levels:
        logging.error(f'Unsupporrted access level "{access_level}"')
        sys.exit()
    logging.info(f'For users will be set "{levels[access_level]}" access level')

    # Get groups
    gl_groups = gl.groups.list(all=True)

    # Counter
    success_u = success_g = total_g = 0

    for g in gl_groups:
        group = gl.groups.get(g.id)
        total_g += 1

        # Exclude group by rule
        if group.id in exclude_groups:
            logging.debug(f'Group "{group.full_path}" skipped by rule')
            continue

        # Is child group?
        if skip_nested and group.parent_id is not None:
            logging.debug(f'Nested group "{group.full_path}" skipped')
            continue

        # Is empty projects group?
        if skip_blank and len(group.projects.list()) < 1:
            logging.debug(f'Blank group "{group.full_path}" skipped')
            continue

        logging.info(f'Work with group "{group.full_path}"')
        success_g += 1

        # Iterate over users
        for user in users:
            try:
                # Check alredy exist user
                group.members.get(user)

            except gitlab.exceptions.GitlabGetError as e:
                if e.response_code == 404:
                    # Add user if not exist
                    group.members.create({
                        'user_id': user,
                        'access_level': gitlab.const.DEVELOPER_ACCESS
                    })
                    logging.info(
                        f'Added user "{user}" to group "{group.full_path}"')
                    success_u += 1
                else:
                    logging.error(
                        f'Error get user "{user}" in "{group.full_path}" {e}')

            except Exception as e:
                logging.fatal(f'Error in "{group.full_path}" {e}')
                sys.exit()

    logging.info(
        f'Updated {success_u} users in {success_g} '
        f'matching groups out of {total_g} found groups')

    total_t = round(time.time() - start_t, 2)
    logging.info(f'Done in {total_t}s.')

if __name__ == '__main__':
    start_t = time.time()
    load_dotenv()
    loglevel()
    main()
