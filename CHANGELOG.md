# Changelog

## [v3.0.13] - 2025-07-11

- 🔄 Migrated to `freeAccessTime` data-bind selector
- ⏫ Upgraded to Playwright `v1.53.0`
- 🧹 Updated other dependencies

## [v3.0.12] - 2025-05-20

- 👨‍🔧 Fixed circular dependency issue via dependency injection
- ⏫ Upgraded to Playwright `v1.52.0`
- 🧹 Updated some other dependencies

## [v3.0.11] - 2025-05-13

- 🔄 Migrated from `Poetry` to `uv` for dependency management
- 🔁 Updated dependency installation flow to use `pyproject.toml` directly
- 🏗 Migrated CI/CD test pipeline

## [v3.0.10] - 2025-03-17

- 🐍 Introduced support for Python `3.12`
- 👨‍🔧 Fixed broken reference

## [v3.0.9] - 2025-03-06

- 🚧 Introduced `handle_errors` decorator to manage common error reporting and cleanup tasks
- 👨‍🔧 Fixed broken `.btn-hotspot` reference which was leading to useless screenshot + trace reporting
- ⏫ Upgraded to Playwright `v1.50.0`
- 🧹 Updated some other dependencies

## [v3.0.8] - 2024-04-14

- ⏫ Upgraded to Playwright `v1.43.0`
- 🧹 Updated some other dependencies

## [v3.0.7] - 2024-01-20

- ⏫ Upgraded to Playwright `v1.41.0`
- 🧹 Updated some other dependencies

## [v3.0.6] - 2023-09-04

- ⏫ Upgraded to Playwright `v1.37.0`
- 🧹 Updated some other dependencies
- 📖 Updated `Configuration` validators and fixed `telegram_chat_id`

## [v3.0.5] - 2023-05-28

- ⏫ Upgraded to Playwright `v1.34.0`
- 🧹 Updated some other dependencies

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

[v3.0.13]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.13
[v3.0.12]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.12
[v3.0.11]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.11
[v3.0.10]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.10
[v3.0.9]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.9
[v3.0.8]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.8
[v3.0.7]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.7
[v3.0.6]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.6
[v3.0.5]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.5
[v3.0.4]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.4
[v3.0.3]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.3
[v3.0.2]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.2
[v3.0.1]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.1
[v3.0.0]: https://github.com/tatoalo/pressReadMePlease/releases/tag/v3.0.0
