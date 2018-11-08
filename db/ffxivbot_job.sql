-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-11-08 16:24:09
-- 服务器版本： 5.5.59-log
-- PHP Version: 5.4.45

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `FFXIV`
--

-- --------------------------------------------------------

--
-- 表的结构 `ffxivbot_job`
--

CREATE TABLE IF NOT EXISTS `ffxivbot_job` (
  `id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `cn_name` varchar(64) NOT NULL,
  `nickname` longtext NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `ffxivbot_job`
--

INSERT INTO `ffxivbot_job` (`id`, `name`, `cn_name`, `nickname`) VALUES
(1, 'Astrologian', '占星术士', '{"nickname": ["占星"] }'),
(2, 'Bard', '吟游诗人', '{"nickname": ["诗人"] }'),
(3, 'BlackMage', '黑魔法师', '{"nickname": ["黑魔","黑膜","blm","BLM"] }'),
(4, 'DarkKnight', '暗黑骑士', '{"nickname": ["暗骑","黑骑","dk","DK"] }'),
(5, 'Dragoon', '龙骑士', '{"nickname": ["龙骑","躺尸龙"] }'),
(6, 'Machinist', '机工士', '{"nickname": ["机工"] }'),
(7, 'Monk', '武僧', '{}'),
(8, 'Ninja', '忍者', '{"nickname": ["兔子","兔忍"] }'),
(9, 'Paladin', '骑士', '{"nickname": ["彩骑","大翅膀","pld","PLD"] }'),
(10, 'Scholar', '学者', '{"nickname": ["小仙女","小仙女的召唤兽"] }'),
(11, 'Summoner', '召唤师', '{"nickname": ["召唤"] }'),
(12, 'Warrior', '战士', '{"nickname": ["战爹","锯爆"] }'),
(13, 'WhiteMage', '白魔法师', '{"nickname": ["白魔","白膜"] }'),
(14, 'RedMage', '赤魔法师', '{"nickname": ["赤魔","吃馍"] }'),
(15, 'Samurai', '武士', '{"nickname":["侍","Sam","sam"]}');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ffxivbot_job`
--
ALTER TABLE `ffxivbot_job`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ffxivbot_job`
--
ALTER TABLE `ffxivbot_job`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=16;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
