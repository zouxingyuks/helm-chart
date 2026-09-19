# 验证指南

从仓库根目录执行。修改哪个 chart 就先验证哪个 chart；公共库变化还需验证受影响的消费者。测试入口以此处链接的脚本和专用 README 为准。

## 检查层次

| 检查 | 前置条件 | 覆盖与副作用 |
| --- | --- | --- |
| `helm lint charts/<name> --strict` | Helm、所需依赖已就绪 | Chart 静态检查；不安装 release |
| `helm template demo charts/<name>` | Helm、所需依赖已就绪 | 本地渲染；不能证明集群 API、调度或应用运行成功 |
| [公共库契约测试](../../tests/homelab-common/README.md) | Helm 3.12+ / 4、Python 3.9+、PyYAML、可信参考 tgz | 在临时目录验证 helper、共存和打包；不下载依赖、不操作集群 |
| [tracing 渲染检查](../../charts/tracing-stack/tests/check_render.py) | Helm、Python 3、PyYAML、已构建依赖 | 检查默认和覆盖配置、关联及非法输入；不操作集群 |
| [tracing smoke](../../charts/tracing-stack/tests/smoke.py) | 可访问的已部署组件 | 向 Gateway 写入测试遥测，再查询三类信号及关联 |
| [Grafana 检查](../../charts/tracing-stack/tests/check_grafana.py) | Grafana 地址和密码文件 | 在线查询 datasource 健康和配置；不替代 UI 跳转验证 |
| [离线镜像检查](../../charts/tracing-stack/tests/verify_images.py) | Docker、本地已加载镜像、离线 release manifest | 通过本地 inspect 核对镜像 ID 和平台；不证明 Kubernetes 节点已导入 |

本地 lint/template 也可能输出敏感配置；渲染文件留在临时目录，不作为普通文档提交。

## 常用入口

无第三方依赖的 Subconverter 可直接验证：

```sh
helm lint charts/subconverter --strict
helm template demo charts/subconverter > /tmp/subconverter-rendered.yaml
```

tracing-stack 在依赖构建完成后验证：

```sh
helm lint charts/tracing-stack --strict
python3 charts/tracing-stack/tests/check_render.py
```

公共库的 `--common` 参数、制品校验值、测试覆盖及手工 fixture 用法集中维护在[测试 README](../../tests/homelab-common/README.md)，不要省略参考制品后宣称完整契约测试通过。

## 选择验证范围

- 模板或 values 变化：覆盖默认值、受影响开关和错误输入；身份相关变化对比资源名称、selector、Pod 标签及 PVC 引用。
- 公共库变化：运行契约测试以及实际消费 chart 的回归；仅 lint library 不足以证明输出兼容。
- 依赖或交付变化：检查锁文件，并从携带依赖的 tgz 渲染；具体流程见[打包与发布](releasing.md)。
- 文档变化：核对命令、路径、配置键和引用；新增或修改的可执行示例做对应检查，不因文字改动自动操作集群。

部署后的端口转发、smoke 参数与 Grafana 密码文件用法见[tracing-stack README](../../charts/tracing-stack/README.md)。在线 smoke 会产生数据，只有本地检查的任务不包含这一动作。
