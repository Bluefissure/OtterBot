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

 Date: 22/07/2019 23:28:10
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ffxivbot_huntergroupid
-- ----------------------------
DROP TABLE IF EXISTS `ffxivbot_huntergroupid`;
CREATE TABLE `ffxivbot_huntergroupid`  (
  `groupid` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `servermark` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `remark` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`groupid`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ffxivbot_huntergroupid
-- ----------------------------
INSERT INTO `ffxivbot_huntergroupid` VALUES ('824575036', 'myc', '萌芽池 测试组');

SET FOREIGN_KEY_CHECKS = 1;
