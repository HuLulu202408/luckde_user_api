-- N-1 修复：账号唯一键与软删除语义冲突
--
-- 背景
--   原索引 UNIQUE KEY uk_registration_account (account) 只约束 account 单列。
--   应用层注册查重时带 is_delete = 0 条件，于是「已被软删除的同名账号」
--   能通过查重、却在 INSERT 时撞唯一键，表现为永远无法重新注册，且报错为
--   误导性的 409 Account already exists。
--
-- 变更
--   uk_registration_account (account)
--     -> uk_registration_account_type (account, regist_type)
--   account 列同时承载用户名（regist_type=0）与未来的手机号（regist_type=1），
--   按 regist_type 分列唯一可避免两者互相占用。软删除占用问题由应用层
--   墓碑改写（services/service.py:DELETED_ACCOUNT_PREFIX）解决。
--
-- 执行前检查（应为空结果）：
--   SELECT account, regist_type, COUNT(*) AS c
--     FROM table_registration
--    WHERE account IS NOT NULL
--    GROUP BY account, regist_type
--   HAVING c > 1;

ALTER TABLE `table_registration`
  DROP INDEX `uk_registration_account`,
  ADD UNIQUE KEY `uk_registration_account_type` (`account`, `regist_type`);

-- 回滚语句
-- ALTER TABLE `table_registration`
--   DROP INDEX `uk_registration_account_type`,
--   ADD UNIQUE KEY `uk_registration_account` (`account`);
