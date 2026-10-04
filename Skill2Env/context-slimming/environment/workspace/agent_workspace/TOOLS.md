# TOOLS.md — 工具与凭证

本文件每轮注入。凭证永不写入本文件本身，只记录它们的位置与用途。

## 凭证位置

| 用途 | 路径 | 备注 |
|------|------|------|
| pearl 平台 API token | `~/.config/pearl/api_token.enc` | openssl enc 加密，口令问周工 |
| 部署机 SSH key | `~/.config/pearl/deploy_ed25519` | 只读权限，禁止转发 agent |
| 工单系统只读 token | `~/.config/pearl/ticket_ro.token` | 7 天轮换一次 |

## xray-cli 完整命令参考

巡检主入口。全局参数：`--profile prod|staging`，`--json`（机器可读输出），
`--since <duration>`（时间窗，如 15m、2h、1d）。

```
xray-cli nodes list                 # 节点清单与健康度
xray-cli nodes top --sort mem       # 按内存排序的节点
xray-cli alerts active --json       # 活动告警（聚类前）
xray-cli alerts cluster --json      # 三层聚类后的告警事件
xray-cli deps trace <service>       # 服务依赖链
xray-cli probe run <suite>          # 执行探针套件
xray-cli report daily --since 24h   # 生成当日巡检报告
xray-cli maintenance window         # 显示维护窗口（应为 02:00-04:00）
```

使用要点：任何 `--profile prod` 的写操作子命令（`xray-cli nodes drain` 等）
都等同于线上变更，先禀报。`alerts cluster` 的聚类规则版本固定在
`~/pearl/cluster-rules.v3.yaml`，升级规则文件前先在 staging 跑回放。

## MCP 配置样例

```json
{
  "mcpServers": {
    "pearl-readonly": {
      "command": "/usr/local/bin/pearl-mcp",
      "args": ["--profile", "prod", "--read-only"],
      "env": { "PEARL_TOKEN_FILE": "~/.config/pearl/api_token.enc" }
    }
  }
}
```

## 其他工具约定

- 邮件：只读 baymax 邮箱，发信一律先存草稿。
- 下载目录：~/Downloads，清理策略见 MEMORY.md 2024-12-05 的教训条目。
- BI 导出：CSV 用 semicolon 分隔，UTF-8 无 BOM。
