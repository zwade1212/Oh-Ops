# Flush CDN Pipeline

通过在 Jenkins 触发 `flush_cdn` pipeline，然后调用 `flush_cdn.py` 刷新 Cloudflare 和 CloudFront CDN。

## 使用步骤

1. 打开 Jenkins。
2. 找到并触发 `flush_cdn` pipeline，选择需要刷新的域名。
3. Jenkins pipeline 传入选择的域名参数调用 `flush_cdn.py` 脚本。
4. `flush_cdn.py` 脚本将刷新 Cloudflare 和 CloudFront CDN。

## 注意事项

- 确保 `flush_cdn.py` 脚本具有正确的权限和配置。
- 确保 Jenkins 配置正确，并且能够访问 `flush_cdn.py` 脚本。

## 常见问题

### 如何确认 CDN 刷新成功？

检查 Jenkins pipeline 的输出日志，确认 `flush_cdn.py` 脚本执行成功，并且没有错误信息。

### 如果刷新失败怎么办？

检查 Jenkins 和 `flush_cdn.py` 脚本的配置，确保所有必要的权限和配置都已正确设置。