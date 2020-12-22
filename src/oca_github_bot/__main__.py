# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

""" OCA GitHub Bot

This is the main program, which provides the dispatching
mechanisms for webhook calls from github.
"""
import logging

import aiohttp
from aiohttp import web
from gidgethub import aiohttp as gh_aiohttp, sansio as gh_sansio

from . import config
from .router import router

_logger = logging.getLogger(__name__)


async def webhook(request):
    """This is the main webhook dispatcher

    Handlers are declared with the @router.register decorator.
    See https://gidgethub.readthedocs.io/en/latest/routing.html
    """
    body = await request.read()

    event = gh_sansio.Event.from_http(
        request.headers, body, secret=config.GITHUB_SECRET
    )
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(
            session, config.GITHUB_LOGIN, oauth_token=config.GITHUB_TOKEN
        )
        await router.dispatch(event, gh)

    return web.Response(status=200)


def main():
    # configure logging
    logging.basicConfig(level=logging.DEBUG)
    # launch webhook app
    app = web.Application()
    app.router.add_post("/", webhook)
    web.run_app(app, host=config.HTTP_HOST, port=config.HTTP_PORT)


if __name__ == "__main__":
    main()
