/*
 Navicat Premium Data Transfer

 Source Server         : FFXIVBOT
 Source Server Type    : MySQL
 Source Server Version : 80016
 Source Host           : 127.0.0.1:3306
 Source Schema         : ffxiv_dev

 Target Server Type    : MySQL
 Target Server Version : 80016
 File Encoding         : 65001

 Date: 22/07/2019 23:29:01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ffxivbot_monsterlist
-- ----------------------------
DROP TABLE IF EXISTS `ffxivbot_monsterlist`;
CREATE TABLE `ffxivbot_monsterlist`  (
  `monsterid` int(11) NOT NULL,
  `monstername` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `region` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `starttime` bigint(20) NOT NULL,
  `completetime` bigint(20) NOT NULL,
  `maintainedstarttime` bigint(20) NOT NULL,
  `maintainedcompletetime` bigint(20) NOT NULL,
  `triggermethod` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`monsterid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ffxivbot_monsterlist
-- ----------------------------
INSERT INTO `ffxivbot_monsterlist` VALUES (1, '护土精灵', '中拉诺西亚', 234000, 270000, 140400, 162000, 'ET19:00-22:00，采集“3级拉诺西亚土壤” (第8格)，坐标 (x23,y26)');
INSERT INTO `ffxivbot_monsterlist` VALUES (2, '咕尔呱洛斯', '拉诺西亚低地', 180000, 180000, 108000, 108000, '起始触发时间为满月(ET17:00)时溜达触发.持续时间16-20日每天晚上');
INSERT INTO `ffxivbot_monsterlist` VALUES (3, '伽洛克', '东拉诺西亚', 151200, 172800, 75600, 104400, '连续200分钟（现实时间）不下雨');
INSERT INTO `ffxivbot_monsterlist` VALUES (4, '火愤牛', '西拉诺西亚', 234000, 270000, 140400, 162000, 'ET 8:00-11:00，采集“拉诺西亚韭菜” (第6格)，坐标 (x33,y27)');
INSERT INTO `ffxivbot_monsterlist` VALUES (5, '南迪', '拉诺西亚高地', 169200, 190800, 100800, 115200, '带着宠物在刷新点附近遛达，可骑坐骑');
INSERT INTO `ffxivbot_monsterlist` VALUES (6, '牛头黑神', '拉诺西亚外地', 234000, 255600, 140400, 154800, '玩家死亡触发');
INSERT INTO `ffxivbot_monsterlist` VALUES (7, '雷德罗巨蛇', '黑衣森林中央林区', 151200, 172800, 90000, 104400, '连续两个雨天期间，在第2个雨天的第2个小时刷新 （艾欧泽亚小时）');
INSERT INTO `ffxivbot_monsterlist` VALUES (8, '乌尔伽鲁', '黑衣森林东部林区', 237600, 280800, 140400, 169200, '开启战斗理符触发 （军队理符亦可触发）');
INSERT INTO `ffxivbot_monsterlist` VALUES (9, '夺心魔', '黑衣森林南部林区', 180000, 180000, 108000, 108000, '起始触发时间为新月凌晨(ET0:00)时溜达触发.持续时间1-4日每天晚上');
INSERT INTO `ffxivbot_monsterlist` VALUES (10, '千竿口花希达', '黑衣森林北部林区', 205200, 226800, 122400, 136800, 'ET17:00-21:00 钓“审判瑶”，钓场：秋瓜湖畔 (x21,y26)，鱼饵：雉鸡拟饵，需345获得力');
INSERT INTO `ffxivbot_monsterlist` VALUES (11, '虚无探索者', '西萨纳兰', 205200, 226800, 122400, 136800, '碧空或晴朗钓“铜镜”，钓场：丰饶神井 (x24,y21) 鱼饵：黄油虫，需292获得力');
INSERT INTO `ffxivbot_monsterlist` VALUES (12, '布隆特斯', '中萨纳兰', 237600, 280800, 140400, 169200, '在刷新点附近吃食物触发');
INSERT INTO `ffxivbot_monsterlist` VALUES (13, '巴拉乌尔', '东萨纳兰', 237600, 280800, 140400, 169200, '开启战斗理符触发 （军队理符亦可触发）');
INSERT INTO `ffxivbot_monsterlist` VALUES (14, '努纽努维', '南萨纳兰', 158400, 194400, 93600, 118800, '一小时内地图中所有类型FATE都被触发并且成功完成,5个触发型fate坐标(25.12)(17.18)(21.19)(17.24)(19.35)');
INSERT INTO `ffxivbot_monsterlist` VALUES (15, '蚓螈巨虫', '北萨纳兰', 205200, 226800, 122400, 136800, '大量击杀土元精 （可利用Fate “核心危机” x22,y22 不交任务道具不断击杀土元精）');
INSERT INTO `ffxivbot_monsterlist` VALUES (16, '萨法特', '中央高地', 216000, 302400, 129600, 183600, '玩家处于频死状态触发 （可选择在高处跳下来触发）');
INSERT INTO `ffxivbot_monsterlist` VALUES (17, '阿格里帕', '摩杜纳', 216000, 302400, 129600, 183600, '开启G3，G4，G5，绿图，星光图的箱子触发');
INSERT INTO `ffxivbot_monsterlist` VALUES (18, '凯撒贝希摩斯', '西部高地', 298800, 482400, 183600, 288000, '在刷新点附近遛“皇家贝希摩斯宝宝” (兵团点换)。可骑坐骑飞行触发');
INSERT INTO `ffxivbot_monsterlist` VALUES (19, '极乐鸟', '阿巴拉提亚云海', 298800, 482400, 183600, 288000, '让B怪“斯奎克”放出“唧唧咋咋” 的技能');
INSERT INTO `ffxivbot_monsterlist` VALUES (20, '神穆尔鸟', '龙堡参天高地', 298800, 482400, 198000, 288000, '连续完成5次或以上 FATE——龙卵引起的战争（x19,y28）');
INSERT INTO `ffxivbot_monsterlist` VALUES (21, '刚德瑞瓦', '翻云雾海', 298800, 482400, 198000, 288000, '采集“皇金矿”；采集“星极花” （需要传承录——龙堡篇开启采集点），详细信息参考caiji.ffxiv.cn');
INSERT INTO `ffxivbot_monsterlist` VALUES (22, '苍白骑士', '龙堡内陆低地', 298800, 482400, 183600, 288000, '开启G7藏宝图的箱子');
INSERT INTO `ffxivbot_monsterlist` VALUES (23, '卢克洛塔', '魔大陆阿济兹拉', 298800, 482400, 198000, 288000, '累计击杀50只亚拉戈奇美拉，50只小海德拉，50只美拉西迪亚薇薇尔飞龙触发');
INSERT INTO `ffxivbot_monsterlist` VALUES (24, '优昙婆罗花', '基拉巴尼亚边区', 298800, 482400, 198000, 288000, '击杀植物系怪 （狄亚卡，莱西，寄生花） ');
INSERT INTO `ffxivbot_monsterlist` VALUES (25, '爬骨怪龙', '基拉巴尼亚山区', 298800, 482400, 198000, 288000, '陆行鸟运输服务，路径途中触发。');
INSERT INTO `ffxivbot_monsterlist` VALUES (26, '盐和光', '基拉巴尼亚湖区', 298800, 482400, 198000, 288000, '任意地点舍弃任意道具。');
INSERT INTO `ffxivbot_monsterlist` VALUES (27, '巨大鳐', '红玉海', 298800, 482400, 198000, 288000, '起始触发时间为满月(ET12:00)时击杀无壳和有壳观梦螺触发，现实时间持续4小时12分钟（游戏时间：3天12小时）');
INSERT INTO `ffxivbot_monsterlist` VALUES (28, '伽马', '延夏', 298800, 482400, 198000, 288000, '晚间时分 ET17:00-ET9:00 带着迷你亚历山大 宠物 溜达， 可骑坐骑飞行触发。 ');
INSERT INTO `ffxivbot_monsterlist` VALUES (29, '兀鲁忽乃朝鲁', '太阳神草原', 298800, 482400, 198000, 288000, '完成Fate石头人英雄：格尔该朝鲁，坐标 （X13.5,Y13.5） ，然后在刷新点附近溜达触发。');

SET FOREIGN_KEY_CHECKS = 1;
