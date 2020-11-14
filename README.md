# OtterBot

[![ActionsStatus](https://github.com/Bluefissure/OtterBot/workflows/Python%203.6/badge.svg)](https://github.com/Bluefissure/OtterBot/actions?query=workflow%3A%22Python+3.6%22) [![CodeFactor](https://www.codefactor.io/repository/github/bluefissure/otterbot/badge/master)](https://www.codefactor.io/repository/github/bluefissure/otterbot/overview/master) [![license](https://img.shields.io/badge/license-GPL-blue.svg)](https://github.com/Bluefissure/OtterBot/blob/master/LICENSE)

A QQ bot for Final Fantasy XIV (mostly served for CN server).

## Install

Please read [wiki](https://github.com/Bluefissure/OtterBot/wiki/%E5%BC%80%E5%8F%91%E6%96%87%E6%A1%A3) for more details.

- python 3.6+
- redis-server 4.0+
- django, channels and so on (see [requeirements.txt](https://github.com/Bluefissure/OtterBot/blob/master/requirements.txt) for details)
- [adminLTE](https://github.com/almasaeed2010/AdminLTE) for the front-end

## Use

Please read [wiki](https://github.com/Bluefissure/OtterBot/wiki/%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3) for more details.

- /cat : require an image of cat (crawled from [pexels](https://www.pexels.com/search/cat))
- /search $item : search $item in [FFXIVWIKI](https://ff14.huijiwiki.com/)
- /anime $image : search the animation of $image ([whatanime](https://whatanime.ga/) API token required)
- /random $num : require $num true random numbers  ([random.org](https://www.random.org/) API token required)
- /gif : generate an shadiao gif via [sorry.xuty.tk](https://sorry.xuty.tk/) (/gif help : get help)
- /dps : get the dps rank from fflogs

## Docker

Please read [wiki](https://github.com/Bluefissure/OtterBot/wiki/OtterBot-Docker) for more details.