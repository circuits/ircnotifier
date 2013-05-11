#!/usr/bin/env python

"""IRC Notifier Daemon

For usage type:

   ./ircnotifier.py --help
"""


import sys
from os import environ, path
from socket import gethostname
from optparse import OptionParser

import circuits
from circuits.app import Daemon
from circuits.web import Logger, Static, Server
from circuits import Component, Debugger, Event, Timer
from circuits.net.sockets import Connect, TCPClient, Write
from circuits.net.protocols.irc import IRC, USER, NICK, JOIN

from . webapi import WebAPI
from . import __name__, __version__

USAGE = "%prog [options] <host> [<port>]"
VERSION = "%prog v" + __version__

DOCROOT = path.abspath(path.join(path.dirname(__file__), "htdocs"))
PIDFILE = path.join(path.dirname(__file__), "{0:s}.pid".format(__name__))


def parse_options():
    parser = OptionParser(usage=USAGE, version=VERSION)

    parser.add_option(
        "-b", "--bind", action="store", default="0.0.0.0:8000",
        dest="bind", metavar="INT", type=str,
        help="Listen on interface INT"
    )

    parser.add_option(
        "-d", "--daemon",
        action="store_true", default=False, dest="daemon",
        help="Enable daemon mode"
    )

    parser.add_option(
        "-c", "--channel",
        action="append", default=None, dest="channels",
        help="Channel to join (multiple allowed)"
    )

    parser.add_option(
        "-n", "--nick",
        action="store", default=environ["USER"], dest="nick",
        help="Nickname to use"
    )

    parser.add_option(
        "-l", "--access-log", action="store", default=None,
        dest="accesslog", metavar="FILE", type=str,
        help="Store web server access logs in FILE"
    )

    parser.add_option(
        "-p", "--pidfile",
        action="store", default=PIDFILE, dest="pidfile",
        help="Path to store PID file"
    )

    parser.add_option(
        "-v", "--verbose",
        action="store_true", default=False, dest="verbose",
        help="Enable verbose debugging mode"
    )

    parser.add_option(
        "--disable-logging", action="store_true", default=False,
        dest="disable_logging",
        help="Disable access logging"
    )

    opts, args = parser.parse_args()

    if not opts.channels:
        print("ERROR: Must specify at least one channel")
        parser.print_help()
        raise SystemExit(2)

    if len(args) < 1:
        print("ERROR: Must specify a host to connect to")
        parser.print_help()
        raise SystemExit(1)

    return opts, args


class Bot(Component):

    channel = "bot"

    def init(self, host, port=6667, opts=None):
        self.host = host
        self.port = port
        self.opts = opts
        self.hostname = gethostname()

        self.nick = opts.nick
        self.ircchannels = opts.channels

        # Debugger
        Debugger(events=opts.verbose).register(self)

        # Add TCPClient and IRC to the system.
        self += (TCPClient(channel=self.channel) + IRC(channel=self.channel))

        # Add Web Server and API
        self += (Server(opts.bind) + Static(docroot=DOCROOT) + WebAPI())

        # Add Web Server Logging
        if not opts.disable_logging:
            self += Logger(file=(opts.accesslog or sys.stdout))

        # Daemon?
        if self.opts.daemon:
            Daemon(opts.pidfile).register(self)

        # Keep-Alive Timer
        Timer(60, Event.create("KeepAlive"), persist=True).register(self)

    def ready(self, component):
        """Ready Event

        This event is triggered by the underlying ``TCPClient`` Component
        when it is ready to start making a new connection.
        """

        self.fire(Connect(self.host, self.port))

    def keep_alive(self):
        self.fire(Write(b"\x00"))

    def connected(self, host, port):
        """Connected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when a successfully connection has been made.
        """

        nick = self.nick
        hostname = self.hostname
        name = "{0:s} on {1:s} using circuits/{2:s}".format(
            nick, hostname, circuits.__version__
        )

        self.fire(USER(nick, hostname, host, name))
        self.fire(NICK(nick))

    def disconnected(self):
        """Disconnected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when the active connection has been terminated.
        """

        self.fire(Connect(self.host, self.port))

    def numeric(self, source, target, numeric, args, message):
        """Numeric Event

        This event is triggered by the ``IRC`` Protocol Component when we have
        received an IRC Numberic Event from server we are connected to.
        """

        if numeric == 1:
            for ircchannel in self.ircchannels:
                self.fire(JOIN(ircchannel))
        elif numeric == 433:
            self.nick = newnick = "%s_" % self.nick
            self.fire(NICK(newnick))

    def message(self, source, target, message):
        """Message Event

        This event is triggered by the ``IRC`` Protocol Component for each
        message we receieve from the server.
        """

    def invite(self, source, target, channel):
        """Invite Event

        This event is triggered by the ``IRC`` Protocol Component when the
        bot has been invited to a channel.
        """

        self.fire(JOIN(channel))


def main():
    opts, args = parse_options()

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 6667

    if ":" in opts.bind:
        address, port = opts.bind.split(":")
        port = int(port)
    else:
        address, port = opts.bind, 8000

    opts.bind = (address, port)

    # Configure and run the system.
    Bot(host, port, opts=opts).run()


if __name__ == "__main__":
    main()
