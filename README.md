# Ada

Ada 是一个可分发的 Hermes profile：一个偏软件工程、重正确性与可验证性的 agent。

当前仓库包含：

- `SOUL.md`：Ada 的人格与工程判断
- `distribution.yaml`：Hermes profile distribution manifest

## 安装

```bash
hermes profile install github.com/wubing7755/Ada --alias
```

安装后可直接使用：

```bash
ada chat
```

## 更新

```bash
hermes profile update ada
```

## 说明

- 这个 distribution 不携带安装者的记忆、会话、API 密钥或本地日志。
- 安装者使用自己的模型配置与凭据。
- 目前仓库主要定义 Ada 的 identity / SOUL；如后续增加 skills、cron、MCP 或 profile 级配置，可直接继续加入仓库。
