-- ============================================================
-- 新手 Python 算法练习 Coding —— MySQL 8.0 建表脚本
-- 用法：mysql -u root -p < schema.sql
-- 说明：题库 / 专题 / 卡片数据由 manage.py init 导入，
--       本脚本只负责建库建表。
-- ============================================================

CREATE DATABASE IF NOT EXISTS `pyoj`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `pyoj`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `submit`;
DROP TABLE IF EXISTS `mistake_note`;
DROP TABLE IF EXISTS `problem_note`;
DROP TABLE IF EXISTS `topic_problem`;
DROP TABLE IF EXISTS `topic`;
DROP TABLE IF EXISTS `card`;
DROP TABLE IF EXISTS `problem`;
DROP TABLE IF EXISTS `user`;

-- ------------------------------------------------------------
-- 1. 用户表
-- ------------------------------------------------------------
CREATE TABLE `user` (
  `id`            INT          NOT NULL AUTO_INCREMENT COMMENT '用户 id',
  `username`      VARCHAR(64)  NOT NULL COMMENT '登录账号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希（werkzeug pbkdf2）',
  `nickname`      VARCHAR(64)  NOT NULL DEFAULT '' COMMENT '昵称',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_username` (`username`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户';

-- ------------------------------------------------------------
-- 2. 题目表
-- ------------------------------------------------------------
CREATE TABLE `problem` (
  `id`            INT          NOT NULL AUTO_INCREMENT COMMENT '题目 id',
  `title`         VARCHAR(128) NOT NULL COMMENT '标题',
  `difficulty`    VARCHAR(16)  NOT NULL DEFAULT '入门' COMMENT '难度：入门 / 基础',
  `tags`          VARCHAR(255) NOT NULL DEFAULT '' COMMENT '算法标签，逗号分隔',
  `description`   TEXT         NOT NULL COMMENT '题干（支持轻量 Markdown）',
  `hint`          TEXT         NOT NULL COMMENT '思路提示（只给方向，不给代码）',
  `sample_input`  TEXT         NOT NULL COMMENT '样例输入',
  `sample_output` TEXT         NOT NULL COMMENT '样例输出',
  `tests_json`    MEDIUMTEXT   NOT NULL COMMENT '全部测试点，JSON：[{input, output}]',
  `time_limit_ms` INT          NOT NULL DEFAULT 2000 COMMENT '单测试点时限（毫秒）',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_problem_difficulty` (`difficulty`),
  KEY `idx_problem_title` (`title`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '题目';

-- ------------------------------------------------------------
-- 3. 提交表
-- ------------------------------------------------------------
CREATE TABLE `submit` (
  `id`          INT        NOT NULL AUTO_INCREMENT COMMENT '提交 id',
  `user_id`     INT        NOT NULL COMMENT '用户 id',
  `problem_id`  INT        NOT NULL COMMENT '题目 id',
  `code`        MEDIUMTEXT NOT NULL COMMENT '提交的 Python3 代码',
  `status`      VARCHAR(8) NOT NULL DEFAULT 'WA' COMMENT 'AC / WA / TLE / RE / CE',
  `passed`      INT        NOT NULL DEFAULT 0 COMMENT '通过的测试点数',
  `total`       INT        NOT NULL DEFAULT 0 COMMENT '测试点总数',
  `time_ms`     INT        NOT NULL DEFAULT 0 COMMENT '最大运行用时（毫秒）',
  `message`     TEXT       NULL COMMENT '判题说明（新手可读）',
  `detail_json` MEDIUMTEXT NULL COMMENT '逐测试点详情，JSON',
  `created_at`  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  PRIMARY KEY (`id`),
  KEY `idx_submit_user` (`user_id`),
  KEY `idx_submit_problem` (`problem_id`),
  KEY `idx_submit_status` (`status`),
  KEY `idx_submit_created` (`created_at`),
  CONSTRAINT `fk_submit_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_submit_problem` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '提交记录';

-- ------------------------------------------------------------
-- 4. 错题笔记表
-- ------------------------------------------------------------
CREATE TABLE `mistake_note` (
  `id`         INT      NOT NULL AUTO_INCREMENT COMMENT '错题笔记 id',
  `user_id`    INT      NOT NULL COMMENT '用户 id',
  `problem_id` INT      NOT NULL COMMENT '题目 id',
  `content`    TEXT     NULL COMMENT '笔记内容（错因 / 思路）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '标记时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_mistake_user_problem` (`user_id`, `problem_id`),
  KEY `idx_mistake_problem` (`problem_id`),
  CONSTRAINT `fk_mistake_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_mistake_problem` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '错题本';

-- ------------------------------------------------------------
-- 5. 解题笔记表（二期：任意题目都可以写思路，不限于错题）
-- ------------------------------------------------------------
CREATE TABLE `problem_note` (
  `id`         INT      NOT NULL AUTO_INCREMENT COMMENT '解题笔记 id',
  `user_id`    INT      NOT NULL COMMENT '用户 id',
  `problem_id` INT      NOT NULL COMMENT '题目 id',
  `content`    TEXT     NULL COMMENT '笔记内容（思路 / 关键点）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_problem_note_user_problem` (`user_id`, `problem_id`),
  KEY `idx_problem_note_problem` (`problem_id`),
  CONSTRAINT `fk_problem_note_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_problem_note_problem` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '解题笔记';

-- ------------------------------------------------------------
-- 6. 专题套题（二期）：topic 是套题，topic_problem 维护顺序
-- ------------------------------------------------------------
CREATE TABLE `topic` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '专题 id',
  `name`        VARCHAR(64)  NOT NULL COMMENT '专题名称',
  `slug`        VARCHAR(64)  NOT NULL COMMENT '英文标识（唯一）',
  `description` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '一句话说明',
  `icon`        VARCHAR(8)   NOT NULL DEFAULT '📘' COMMENT '图标',
  `sort_order`  INT          NOT NULL DEFAULT 0 COMMENT '展示顺序',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_topic_slug` (`slug`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '专题套题';

CREATE TABLE `topic_problem` (
  `topic_id`   INT NOT NULL COMMENT '专题 id',
  `problem_id` INT NOT NULL COMMENT '题目 id',
  `position`   INT NOT NULL DEFAULT 0 COMMENT '题目在套题中的顺序',
  PRIMARY KEY (`topic_id`, `problem_id`),
  KEY `idx_topic_problem_problem` (`problem_id`),
  CONSTRAINT `fk_topic_problem_topic` FOREIGN KEY (`topic_id`) REFERENCES `topic` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_topic_problem_problem` FOREIGN KEY (`problem_id`) REFERENCES `problem` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '专题-题目关联';

-- ------------------------------------------------------------
-- 7. 语法知识点卡片表（二期）
-- ------------------------------------------------------------
CREATE TABLE `card` (
  `id`         INT          NOT NULL AUTO_INCREMENT COMMENT '卡片 id',
  `title`      VARCHAR(64)  NOT NULL COMMENT '卡片标题',
  `category`   VARCHAR(32)  NOT NULL DEFAULT '基础语法' COMMENT '分类',
  `summary`    VARCHAR(200) NOT NULL DEFAULT '' COMMENT '一句话摘要',
  `content`    TEXT         NULL COMMENT '卡片正文（轻量 Markdown）',
  `tags`       VARCHAR(128) NOT NULL DEFAULT '' COMMENT '标签，逗号分隔',
  `sort_order` INT          NOT NULL DEFAULT 0 COMMENT '展示顺序',
  PRIMARY KEY (`id`),
  KEY `idx_card_category` (`category`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Python 语法卡片';

SET FOREIGN_KEY_CHECKS = 1;
