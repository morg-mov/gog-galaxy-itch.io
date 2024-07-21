import sys
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, Game, LicenseInfo, LicenseType


class PluginExample(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(
            Platform.ItchIo,  # choose platform from available list
            "0.1.0",  # version
            reader,
            writer,
            token
        )

    # implement methods

    # required
    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            pass

    # required
    async def get_owned_games(self):
        return [
            Game('test', 'The Test', None, LicenseInfo(LicenseType.SinglePurchase))
        ]


def main():
    create_and_run_plugin(PluginExample, sys.argv)

# run plugin event loop
if __name__ == "__main__":
    main()