# Changelog

## [v3.0.4] - 2023-04-15

- ⤴️ Migrated to `22.04 LTS` base image
- ⏫ Upgraded to Playwright `v1.32.1`
- 🧹 Updated some other dependencies

## [v3.0.3] - 2023-02-26

- ⏫ Upgraded to Playwright `v1.31.0`
- 🧹 Updated some other dependencies

## [v3.0.2] - 2022-12-12 🎅🏻 🎄

- 👨‍🔧 Fixed Screenshot client logic
- 🥽 Safer verification of the execution flow w/out Configuration setup
- ⏫ Upgraded to Playwright `v1.28.0`
- 📖 Added instructions for setup w/out Docker
- 🐍 Introduced support for Python `3.11.1`

## [v3.0.1] - 2022-11-18

- 🐳 Improved Dockerfile
- 👨‍🔧 Fixed Docker-compose issue
- 🪵 Added logging support

## [v3.0.0] - 2022-10-13

- ☁️ CF workaround implemented
- 🛂 Integrated control flow
- 🕶 Added black support
- 📖 Updated reqs
- 🏷 Supported multiple tags
- 🏗 Built CI/CD pipeline
- 🪪 Implemented brand new credentials flow
- 🖥 Entirely rewritten Chromium class
- 📬 Entirely rewritten logic around Notifier instantiation
- 🐳 Improved Dockerfile
- 🔖 Migrated deps management to Poetry (still in hybrid mode, not entirely depending on it)
- 🧪 Extended and improved testing suite
- ⏫ Upgraded to Playwright `v1.26.1`

## 2.0.4 - 2022-05-29

- ⏫ Upgraded to Playwright `v1.22.0`

## 2.0.3 - 2022-04-20

- ⏫ Upgraded to Playwright `v1.21.0`

## 2.0.2 - 2022-03-19

- ⏫ Updated to Playwright `v1.20.0`
- 👨‍🔧 Fixed DNS not resolving issue
- ⏰ Crontab correctly running on `ubuntu` image

## 2.0.1 - 2022-03-11

- 👨‍🔧 Fixed cron failure

## 2.0.0 - 2022-03-10

- 🔥 Migrated _pressReadMePlease_ to [Playwright](https://playwright.dev)
- ⚡️ Faster automation flow
- 💤 Removed manual `time.sleep` patterns that were previously used, wasting CPU cycles
- 💪🏻 More robust items selections and querying
- 🐞 Added support for debugging trace
- 📥 Added telegram support for debugging trace
- 😿 Migrated from `alpine` to `ubuntu` as base image
- 🏋️‍ Docker image is heavier but with `99%` efficiency

## 1.0.0 - 2022-02-26

- Released last supported Selenium-based docker image

[v3.0.4]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.4
[v3.0.3]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.3
[v3.0.2]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.2
[v3.0.1]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.1
[v3.0.0]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.0
