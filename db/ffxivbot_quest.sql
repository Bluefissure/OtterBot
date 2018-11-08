-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-11-08 16:23:58
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
-- 表的结构 `ffxivbot_quest`
--

CREATE TABLE IF NOT EXISTS `ffxivbot_quest` (
  `quest_id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `cn_name` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `ffxivbot_quest`
--

INSERT INTO `ffxivbot_quest` (`quest_id`, `name`, `cn_name`) VALUES
(15, 'Trials (Extreme)', '蛮神（极）'),
(21, 'Omega: Sigmascape (Savage)', '欧米茄零式时空狭缝（西格玛幻境）'),
(25, 'Omega: Alphascape (Savage)', '欧米茄零式时空狭缝（阿尔法幻境）');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ffxivbot_quest`
--
ALTER TABLE `ffxivbot_quest`
  ADD PRIMARY KEY (`quest_id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
