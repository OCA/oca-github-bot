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


class OptionsError(Exception):
    pass


class InvalidOptionsError(OptionsError):
    def __init__(self, name, options):
        super().__init__(f"Invalid options for command {name}: {options}")


class RequiredOptionError(OptionsError):
    def __init__(self, name, option, values):
        values_text = ", ".join(values)
        super().__init__(
            f"Required option {option} for command {name}.\n"
            f"Possible values : {values_text}"
        )


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
    bumpversion_mode = None
    bumpversion_mode_list = ["major", "minor", "patch", "nobump"]

    def parse_options(self, options):
        if not options:
            raise RequiredOptionError(
                self.name, "bumpversion_mode", self.bumpversion_mode_list
            )
        if len(options) == 1 and options[0] in self.bumpversion_mode_list:
            self.bumpversion_mode = options[0]
        else:
            raise InvalidOptionsError(self.name, options)

    def delay(self, org, repo, pr, username, dry_run=False):
        merge_bot.merge_bot_start.delay(
            org, repo, pr, username, self.bumpversion_mode, dry_run=False
        )


def parse_commands(text):
    """ Parse a text and return an iterator of BotCommand objects. """
    for mo in BOT_COMMAND_RE.finditer(text):
        yield BotCommand.create(
            mo.group("command"), mo.group("options").strip().split()
        )
