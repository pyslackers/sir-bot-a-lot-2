Sir-bot-a-lot
=============

The good Sir Bot-a-lot. An asynchronous python bot framework.

.. image:: https://travis-ci.org/pyslackers/sir-bot-a-lot-2.svg?branch=master
    :target: https://travis-ci.org/pyslackers/sir-bot-a-lot-2
    :alt: Travis-ci status
.. image:: https://badge.fury.io/py/sirbot.svg
    :target: https://pypi.org/project/sirbot
    :alt: PyPI status
.. image:: https://coveralls.io/repos/github/pyslackers/sir-bot-a-lot-2/badge.svg?branch=master
    :target: https://coveralls.io/github/pyslackers/sir-bot-a-lot-2?branch=master
    :alt: Coverage status

Installation
------------

Sir Bot-a-lot is `available on PyPI <https://pypi.org/project/sirbot/>`_.

.. code::

    $ pip install sirbot

Quickstart
----------

.. code-block:: python

    from sirbot import SirBot

    bot = SirBot()

    plugin = MyPlugin()
    bot.load(plugin)

    bot.start(host='0.0.0.0', port=8000)

Plugins
-------

Sir Bot-a-lot provide some plugins to connect to various services:

* ``sirbot.plugins.github.GithubPlugin`` For `Github <https://www.github.com>`_.
* ``sirbot.plugins.slack.SlackPlugin`` For `Slack <https://www.slack.com>`_.
* ``sirbot.plugins.postgres.PgPlugin`` For `PostgreSQL <https://www.postgresql.org/>`_.
* ``sirbot.plugins.apscheduler.APSchedulerPlugin`` For `APscheduler <https://apscheduler.readthedocs.io/en/latest/>`_.

Changelog
---------

dev
```

0.0.4
`````

* Initial release of ``sirbot.plugins.apscheduler.APSchedulerPlugin``.
* Routing on message subtype for ``sirbot.plugins.slack.SlackPlugin``.
* ``wait`` option for slack endpoint to wait the end of the handlers before responding.

0.0.3
`````

* Initial release of ``sirbot.plugins.postgres.PgPlugin``.

0.0.2
`````

* Various bugfix in ``sirbot.plugins.slack.SlackPlugin``.

0.0.1
`````

* Initial development release.
