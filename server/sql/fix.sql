-- ============================================================================
-- 数据库修复脚本 - 修复 real_name 字段长度问题
-- ============================================================================

USE dbenterprise;

-- 修复 users 表的 real_name 字段：扩大为 VARCHAR(100)，确保能存中文姓名
ALTER TABLE `users` MODIFY COLUMN `real_name` VARCHAR(100) DEFAULT NULL COMMENT '真实姓名';

-- 修复 documents 表的 content_text 字段：改为 LONGTEXT 确保大文档不溢出
ALTER TABLE `documents` MODIFY COLUMN `content_text` LONGTEXT COMMENT '提取的文本内容（用于向量化）';
