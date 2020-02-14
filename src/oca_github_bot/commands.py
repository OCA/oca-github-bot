# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

from .tasks import merge_bot

BOT_COMMAND_RE = re.compile(
    # Do not start with > (Github comment), not consuming it
    r"^(?=[^>])"
    # Anything before /ocabot, at least one whitspace after
    r".*/ocabot\s+"
    # command group: any word is ok
    r"(?P<command>\w+)"
    # options group: spaces and words, all the times you want (0 is ok too)
    r"(?P<options>[ \t\w]*)"
    # non-capturing group:
    # stop finding options as soon as you find something that is not a word
    r"(?:\W|\r?$)",
    re.MULTILINE,
)


class InvalidCommandError(Exception):
    def __init__(self, name):
        super().__init__(f"Invalid command: {name}")


class InvalidOptionsError(Exception):
    def __init__(self, name, options):
        super().__init__(f"Invalid options for command {name}: {options}")


class BotCommand:
    def __init__(self, name, options):
        self.name = name
        self.options = options
        self.parse_options(options)

    @classmethod
    def create(cls, name, options):
        if name == "merge":
            return BotCommandMerge(name, options)
        else:
            raise InvalidCommandError(name)

    def parse_options(self, options):
        pass

    def delay(self, org, repo, pr, username, dry_run=False):
        """ Run the command on a given pull request on behalf of a GitHub user """
        raise NotImplementedError()


class BotCommandMerge(BotCommand):
    bumpversion = None  # optional str: major|minor|patch
    squash = None  # optional str: squash|autosquash

    def parse_options(self, options):
        if not options:
            return
        if len(options) == 2 and options[1] in ('squash', 'autosquash'):
            self.squash = options[1]
        if len(options) >= 1 and options[0] in ("major", "minor", "patch"):
            self.bumpversion = options[0]
        else:
            raise InvalidOptionsError(self.name, options)

    def delay(self, org, repo, pr, username, dry_run=False):
        merge_bot.merge_bot_start.delay(
            org, repo, pr, username,
            bumpversion=self.bumpversion,
            squash=self.squash,
            dry_run=False
        )


def parse_commands(text):
    """ Parse a text and return an iterator of BotCommand objects. """
    for mo in BOT_COMMAND_RE.finditer(text):
        yield BotCommand.create(
            mo.group("command"), mo.group("options").strip().split()
        )
