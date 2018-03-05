pytest_plugins = "slack.tests.plugin",


def pytest_addoption(parser):
    parser.addoption("--postgres", action="store_true", default=False, help="Test PostgreSQL plugin")
