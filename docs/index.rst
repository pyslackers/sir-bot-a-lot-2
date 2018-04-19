==========================================
Sir Bot-a-lot | Asynchronous bot framework
==========================================

This project aims to provide a simple library to generate bots for various services. The initial goal was to implement
a bot for the slack team of the `pyslackers <https://www.pyslackers.com>`_ community.

Installation
------------

`Sir Bot-a-lot is on PyPI <https://pypi.org/project/sirbot/>`_.

.. code:: console

    $ pip3 install sirbot

We recommend installing it in a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_.

To run the bot initialize it and call the ``bot.start`` method:

.. code:: python3

    from sirbot import SirBot

    bot = SirBot()
    bot.start(host='0.0.0.0', port=80)

For examples take a look at the :ref:`howto` and the `pyslackers bot <https://github.com/pyslackers/sirbot-pyslackers>`_.

Plugins
-------

Sir Bot-a-lot connect to services with plugins, some are bundled by default:

    * :class:`sirbot.plugins.github.GithubPlugin` For `Github <https://www.github.com>`_.
    * :class:`sirbot.plugins.slack.SlackPlugin` For `Slack <https://www.slack.com>`_.
    * :class:`sirbot.plugins.postgres.PgPlugin` For `PostgreSQL <https://www.postgresql.org/>`_.
    * :class:`sirbot.plugins.apscheduler.APSchedulerPlugin` For `APscheduler <https://apscheduler.readthedocs.io/en/latest/>`_.

To load a plugin initialize it and call the ``bot.load`` method:

.. code:: python3

    from sirbot import SirBot
    from sirbot.plugins.slack import SlackPlugin

    bot = SirBot()

    slack = SlackPlugin(token='supersecureslacktoken')
    bot.load(slack)

    bot.start(host='0.0.0.0', port=80)

Navigation
----------

.. toctree::
   :maxdepth: 2

   how_to/index
   api/index
