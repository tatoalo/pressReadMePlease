# Change Log

## 2.0.2 - 2022-03-19

* Updated to Playwright `v1.20.0`
* Fixed DNS not resolving issue
* Crontab correctly running on `ubuntu` image

## 2.0.1 - 2022-03-11

* 👨‍🔧 Fixed cron failure

## 2.0.0 - 2022-03-10

* 🔥 Migrated *pressReadMePlease* to [Playwright](https://playwright.dev) 
* ⚡️ Faster automation flow
* 💤 Removed manual `time.sleep` patterns that were previously used, wasting CPU cycles
* 💪🏻 More robust items selections and querying
* 🐞 Added support for debugging trace
* 📥 Added telegram support for debugging trace
* 😿 Migrated from `alpine` to `ubuntu` as base image
* 🏋️‍ Docker image is heavier but with `99%` efficiency

## 1.0.0 - 2022-02-26

 * Released last supported Selenium-based docker image