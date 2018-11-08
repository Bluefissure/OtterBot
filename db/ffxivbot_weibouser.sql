-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-11-08 16:26:34
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
-- 表的结构 `ffxivbot_weibouser`
--

CREATE TABLE IF NOT EXISTS `ffxivbot_weibouser` (
  `id` int(11) NOT NULL,
  `name` varchar(16) NOT NULL,
  `uid` varchar(16) NOT NULL,
  `containerid` varchar(32) NOT NULL,
  `last_update_time` bigint(20) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `ffxivbot_weibouser`
--

INSERT INTO `ffxivbot_weibouser` (`id`, `name`, `uid`, `containerid`, `last_update_time`) VALUES
(3, '最终幻想14', '1797798792', '1076031797798792', 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ffxivbot_weibouser`
--
ALTER TABLE `ffxivbot_weibouser`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ffxivbot_weibouser_name_b980c0f0_uniq` (`name`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ffxivbot_weibouser`
--
ALTER TABLE `ffxivbot_weibouser`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=4;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
