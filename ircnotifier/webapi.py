# Module:   webapi
# Date:     10th March 2013
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Web API

This module implements the RESTful Web API.
"""


from json import loads

from circuits.web import JSONController
from circuits.net.protocols.irc import PRIVMSG


class WebAPI(JSONController):

    channel = "/api"

    def index(self):
        methods = [x.names[0] for x in self.handlers()
                   if getattr(x, "exposed", True)]
        return {"success": True, "methods": methods}

    def message(self, channel, payload):
        payload = loads(payload)

        if not all(k in payload for k in ("message", "host", "user",)):
            return {"success": False, "message": "Invalid payload"}

        user = payload.get("user", "nobody")
        host = payload.get("host", "localhost")
        message = payload.get("message", "")

        self.fire(PRIVMSG(channel, "Message from {0:s}@{1:s}: {2:s}".format(
            user, host, message)), "bot")

        return {"success": True}

    def postcommit(self, *args, **kwargs):
        channels = ["#{0:s}".format(x) for x in args[0].split(",")] if args else ["#circuits"]
        payload = loads(kwargs.get("payload", {}))

        if not all(k in payload for k in ("repository", "commits",)):
            return {"success": False, "message": "Invalid payload"}

        name = payload.get("repository", {}).get("name", "Unknown")
        commits = payload.get("commits", [])

        for channel in channels:
            self.fire(
                PRIVMSG(
                    channel,
                    "{0:d} commit(s) pushed to {1:s}".format(
                        len(commits), name
                    )
                ),
                "bot"
            )

            for commit in commits:
                self.fire(PRIVMSG(channel, "{0:s} by {1:s}: {2:s}".format(
                    commit["node"], commit["author"], commit["message"])), "bot")

        return {"success": True}
