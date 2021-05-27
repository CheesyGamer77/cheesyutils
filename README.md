# cheesyutils

A number of miscelanious utilities, mostly for writing bots in discord.py

## Usage

You can install the package by running the following command:

```sh
pip install -U cheesyutils
```

You can import the installed package by running the following python code

```py
from cheesyutils.discord_bots import DiscordBot
```

Creating a simple Discord bot with only the builtin Meta commands:

```py
from cheesyutils.discord_bots import DiscordBot

bot = DiscordBot(
    prefix=".",
    color="#a0365c"
)

bot.run("YOUR TOKEN HERE")
```
