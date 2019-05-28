# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

from .tasks import merge_bot

BOT_COMMAND_RE = re.compile(
    r"/ocabot +(?P<command>\w+)( +(?P<options>.*?))? *$", re.MULTILINE
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

    def parse_options(self, options):
        if not options:
            return
        if options in ("major", "minor", "patch"):
            self.bumpversion = options
        else:
            raise InvalidOptionsError(self.name, options)

    def delay(self, org, repo, pr, username, dry_run=False):
        merge_bot.merge_bot_start.delay(
            org, repo, pr, username, bumpversion=self.bumpversion, dry_run=False
        )


def parse_commands(text):
    """ Parse a text and return an iterator of BotCommand objects. """
    for mo in BOT_COMMAND_RE.finditer(text):
        yield BotCommand.create(mo.group("command"), mo.group("options"))
