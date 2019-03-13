# FFXIVBOT

[![Build Status](https://travis-ci.org/Bluefissure/FFXIVBOT.svg?branch=master)](https://travis-ci.org/Bluefissure/FFXIVBOT)
[![CodeFactor](https://www.codefactor.io/repository/github/bluefissure/ffxivbot/badge/master)](https://www.codefactor.io/repository/github/bluefissure/ffxivbot/overview/master)
[![license](https://img.shields.io/badge/license-GPL-blue.svg)](https://github.com/Bluefissure/FFXIVBOT/blob/master/LICENSE)

A QQ bot of FFXIV

## Install

Please read [wiki](https://github.com/Bluefissure/FFXIVBOT/wiki/%E5%BC%80%E5%8F%91%E6%96%87%E6%A1%A3) for more details.
For Windows enviroment please check [Windows下的开发文档](https://github.com/a08381/FFXIVBOT/wiki/Windows%E4%B8%8B%E7%9A%84%E5%BC%80%E5%8F%91%E6%96%87%E6%A1%A3) for more information.

- python 3.5.3+
- redis-server 4.0+
- django, channels and so on (see [requeirements.txt](https://github.com/Bluefissure/FFXIVBOT/blob/master/requirements.txt) for details)
- [coolq-wine(docker)](https://hub.docker.com/r/coolq/wine-coolq/) for back-end bot
- [coolq-http-api](https://github.com/richardchien/coolq-http-api) for web communication
- [adminLTE](https://github.com/almasaeed2010/AdminLTE) for the front-end

## Use

Please read [wiki](https://github.com/Bluefissure/FFXIVBOT/wiki/%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3) for more details.

- /cat : require an image of cat (crawled from [pexels](https://www.pexels.com/search/cat))
- /search $item : search $item in [FFXIVWIKI](https://ff14.huijiwiki.com/)
- /anime $image : search the animation of $image ([whatanime](https://whatanime.ga/) API token required)
- /random $num : require $num true random numbers  ([random.org](https://www.random.org/) API token required)
- /gif : generate an shadiao gif via [sorry.xuty.tk](https://sorry.xuty.tk/) (/gif help : get help)
- /dps : get the dps rank from fflogs

## Demo

[Configure site](https://xn--v9x.net/tata)

![/cat](https://i.loli.net/2018/04/11/5acd9cd833831.png)
![/search](https://i.loli.net/2018/04/11/5acd9c2eef267.png)
![/anime](https://i.loli.net/2018/04/11/5acd9c2f2ceea.png)
![/random](https://i.loli.net/2018/04/11/5acd9c2f0da51.png)

## Tips

- This project is currently using [django-channels](https://github.com/django/channels) to support reverse websocket of http-api, if you prefer http, see [previous version](https://github.com/Bluefissure/FFXIVBOT/tree/be91c3fb3910479733db937f5f7f263dcef331a7)

# FFXIV Quest Visualization

A Visualization of FFXIV Quest

## Demo

[Demo site](https://xn--v9x.net/quest)

![](https://i.loli.net/2018/09/14/5b9b2dcabfc95.jpg)
