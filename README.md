# Discord TA Bot

## Setting up

First, create an application in the [Discord developer portal](https://discord.com/developers/applications/) and add a bot to it. Invite the bot to your server with the `Administrator` permission.

Then, copy the file `environment-example.env` to `environment.env` and edit its content:

- `COMMAND_PREFIX` is the bot's command prefix. All commands are invoked with this prefix.
- `DISCORD_BOT_TOKEN` is the secret token of you bot (can be found in the developer portal, on your app's bot settings page).

Finally, run `docker-compose up --build` in the project directory to start the bot.

## Notes

- This bot was developed for personal use, and for a very specific purpose on a single server only. While it should work fine with multiple servers, some functions like configuration or general stability are yet to be improved.
- No documentation is currently available.
