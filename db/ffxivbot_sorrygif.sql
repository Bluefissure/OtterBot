-- phpMyAdmin SQL Dump
-- version 4.4.15.10
-- https://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2018-11-08 16:26:19
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
-- 表的结构 `ffxivbot_sorrygif`
--

CREATE TABLE IF NOT EXISTS `ffxivbot_sorrygif` (
  `id` int(11) NOT NULL,
  `name` varchar(16) NOT NULL,
  `api_name` varchar(32) NOT NULL,
  `example` longtext NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;

--
-- 转存表中的数据 `ffxivbot_sorrygif`
--

INSERT INTO `ffxivbot_sorrygif` (`id`, `name`, `api_name`, `example`) VALUES
(1, '为所欲为', 'sorry', '好啊|就算你是一流工程师|就算你出报告再完美|我叫你改报告你就要改|毕竟我是客户|客户了不起啊|sorry 客户真的了不起|以后叫他天天改报告|天天改 天天改'),
(2, '王境泽', 'wangjingze', '我就是饿死|死外边 从这跳下去|也不会吃你们一点东西|真香'),
(3, '金坷垃', 'jinkela', '金坷垃好处都有啥|谁说对了就给他|肥料掺了金坷垃|不流失 不蒸发 零浪费|肥料掺了金坷垃|能吸收两米下的氮磷钾'),
(4, '土拨鼠', 'marmot', '啊~|啊~~~'),
(5, '窃格瓦拉', 'dagong', '没有钱啊 肯定要做的啊|不做的话没有钱用|那你不会去打工啊|有手有脚的|打工是不可能打工的|这辈子不可能打工的'),
(6, '偷电动车', 'diandongche', '戴帽子的首先进里边去|开始拿剪刀出来 拿那个手机|手机上有电筒 用手机照射|寻找那个比较新的电动车|六月六号 两名男子再次出现|民警立即将两人抓获'),
(7, '工作细胞', 'hataraku', '那个呢 那个呢|因为出了些状况|施工进度推迟了'),
(8, '元首', 'fuhrer', '我们装备再好 总会死在外挂手里|没关系 我们可以苦练枪法|这外挂..|这外挂有锁血的 根本打不死|。。。'),
(9, '防身术', 'fangshen', '我将教你如何应对歹徒|集中注意|希望你有所收获'),
(10, '星际还是魔兽', 'dati', '平时你打电子游戏吗|偶尔|星际还是魔兽|连连看'),
(11, '今天星期五', 'friday', '今天星期五了|我的天|明天不上班|熬夜到天亮|再睡上一整天|周五万岁'),
(12, '谁反对', 'mini-disagree', '我话说完了|谁赞成|谁反对|我反对');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ffxivbot_sorrygif`
--
ALTER TABLE `ffxivbot_sorrygif`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ffxivbot_sorrygif`
--
ALTER TABLE `ffxivbot_sorrygif`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=13;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
