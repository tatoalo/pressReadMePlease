<div align="center">
  <img src="./assets/logo.png" width="450" />

  # pressReadMePlease
  🦄 Automagically🪄 refresh PressReader weekly token.
  (currently tested against 🐍 `3.8.4`, `3.9` & `3.10.4`)
  <br/>
  [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/F1F7ABOVF)

  [![MIT](https://img.shields.io/github/license/tatoalo/pressReadMePlease)](https://github.com/tatoalo/pressReadMePlease) [![Pulls from DockerHub](https://img.shields.io/docker/pulls/tatoalo/pressreader-automation.svg)](https://hub.docker.com/r/tatoalo/pressreader-automation) [![Docker Image Version](https://img.shields.io/docker/v/tatoalo/pressreader-automation?sort=semver)][hub]

[hub]: https://hub.docker.com/r/tatoalo/pressreader-automation/
</div>

Using MLOL and PressReader to read newspapers from all over the world is pretty handy, if you use the mobile apps only, though, it may become pretty painful to remember once every week to manually login into MLOL and then PressReader from the desktop version so that PressReader doesn't throw you out of their system.

With pressReadMePlease you can automate this, **set it and forget it!**.

By default the authentication token updating procedure will launch every Friday at 3.20am, of course you can edit this scheduling in the related crontab file.

## Quick Start w/ Docker

You can [pull](https://hub.docker.com/r/tatoalo/pressreader-automation) the Docker image with

```
docker pull tatoalo/pressreader-automation:latest
```

and subsequently launch the container with:

```
docker run --name pressreader -itd --restart unless-stopped -v config.toml:/src/config.toml tatoalo/pressreader-automation
```

#### Docker Compose

```yaml
version: '3.8'
services:
  pressreadmeplease:
    image: tatoalo/pressreader-automation
    restart: unless-stopped
    volumes:
      - /path/to/my/configuration/file:/config/file
```

### Authentication Data

The application, in order to properly function, requires a file `config.toml` located in the `/src/` directory, where the source code lives, mount it appropriately.

Configuration example:

```toml
[mlol]
website = "https://example.medialibrary.it"
username = "username"
password = "password"

[pressreader]
username = "username"
password = "password"
```

### Telegram Notifications & Screenshot Support (optional)

In order to receive telegram notifications about runtime errors, add this section to the previously introduced `config.toml` file:

```toml
# Optional
[notification_service]
telegram_base_url = "https://api.telegram.org/bot"
telegram_token = "token/"
telegram_chat_id = 6942
```

Additionally, support for **attaching screenshots** has also been implemented.
This action makes sense just in certain flows (missing button that was expected to be found) and will be sent in addition to the error message.

### Watchtower support
If you want, you can run this beside [Watchtower](https://github.com/containrrr/watchtower) which allows you to automatically keep all your images up-to-date.
