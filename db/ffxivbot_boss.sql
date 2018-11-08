-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-11-08 16:23:14
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
-- 表的结构 `ffxivbot_boss`
--

CREATE TABLE IF NOT EXISTS `ffxivbot_boss` (
  `boss_id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `cn_name` varchar(64) NOT NULL,
  `nickname` longtext NOT NULL,
  `add_time` bigint(20) NOT NULL,
  `cn_add_time` bigint(20) NOT NULL,
  `quest_id` int(11) NOT NULL,
  `parsed_days` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `ffxivbot_boss`
--

INSERT INTO `ffxivbot_boss` (`boss_id`, `name`, `cn_name`, `nickname`, `add_time`, `cn_add_time`, `quest_id`, `parsed_days`) VALUES
(51, 'Phantom Train', '魔列车', '{"nickname": ["5s","5S","O5S","o5s"] }', 1517529600, 1526313600, 21, 229),
(52, 'Demon Chadarnook', '恶魔查达奴克', '{"nickname": ["6s","6S","O6S","o6s","画魔","查达奴克","查达努克","恶魔查达努克"] }', 1517529600, 1526313600, 21, 229),
(53, 'Guardian', '守护者', '{"nickname": ["7s","7S","O7S","o7s"] }', 1517529600, 1526313600, 21, 0),
(54, 'Kefka', '凯夫卡（门神）', '{"nickname": ["门神"] }', 1517529600, 1526313600, 21, 229),
(55, 'God Kefka', '凯夫卡（本体）', '{"name": "God Kefka", "nickname": ["卡夫卡", "本体", "凯夫卡", "小丑", "8s", "o8s", "8S", "O8S"] }', 1517529600, 1526313600, 21, 0),
(60, 'Chaos', '卡奥斯', '{"nickname":["卡卡","o9s","9s","O9S","9S"]}', 1537660800, 1537833600, 25, 46),
(61, 'Midgardsormr', '尘世幻龙', '{"nickname":["o10s","10s","O10S","10S","尘世幻龙"]}', 1537660800, 1537833600, 25, 46),
(62, 'Omega', '欧米茄', '{"nickname":["o11s","11s","O11S","11S"]}', 1537660800, 1537833600, 25, 46),
(63, 'Omega-M and Omega-F', '欧米茄男女', '{"nickname":["o12s门神","12s门神","O12S门神","12S门神","男女","狗男女"]}', 1537660800, 1537833600, 25, 46),
(64, 'The Final Omega', '终级欧米茄', '{"nickname":["o12s","12s","O12S","12S","o12s本体","12s本体","O12S本体","12S本体"]}', 1537660800, 1537833600, 25, 46),
(1040, 'Byakko', '极白虎', '{"nickname": ["鸡掰虎","鸡掰猫","白虎","白猫","极白猫","大长腿"] }', 1517529600, 1526313600, 15, 261),
(1041, 'Tsukuyomi', '极月读', '{"nickname":["极月神","极夜神","极夜露","极月","极夜","夜露","月读"]}', 1527206400, 1536105600, 15, 146);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ffxivbot_boss`
--
ALTER TABLE `ffxivbot_boss`
  ADD PRIMARY KEY (`boss_id`),
  ADD KEY `ffxivbot_boss_quest_id_56a19897_fk_ffxivbot_quest_quest_id` (`quest_id`);

--
-- 限制导出的表
--

--
-- 限制表 `ffxivbot_boss`
--
ALTER TABLE `ffxivbot_boss`
  ADD CONSTRAINT `ffxivbot_boss_quest_id_56a19897_fk_ffxivbot_quest_quest_id` FOREIGN KEY (`quest_id`) REFERENCES `ffxivbot_quest` (`quest_id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
