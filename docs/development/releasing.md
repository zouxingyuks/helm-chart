# 打包与发布

本页维护仓库共用的发布步骤；chart 专属交付要求留在其 README。构建安装包与将其发布到远端是两个动作，本地打包成功不代表版本已发布。

版本选择遵循 [Chart 版本规则](versioning.md)；已有 chart 接入新格式时先明确迁移基准与目标版本，不自动重置版本。Agent 分析和更新版本使用 [Chart 版本 skill](../../.agents/skills/helm-chart-version/SKILL.md)。

## 准备制品

1. 核对目标 `Chart.yaml` 的 chart 版本与应用版本，完成受影响的[验证](testing.md)。已发布版本不覆盖，内容变化使用新 chart 版本。
2. 有依赖的应用先按[开发流程](workflow.md)重建并审查锁定依赖；包内必须包含安装需要的子 chart。
3. 输出到独立目录，避免混入旧制品。无运行时依赖的公共库示例：

```sh
helm lint charts/homelab-common --strict
helm package charts/homelab-common --destination /tmp/helm-chart-dist
```

检查实际 tgz 的元数据、模板、README、依赖与必要许可证。涉及文档迁移时，确认包内说明不依赖源码仓库外部的相对路径。应用包应能脱离源码目录渲染；library 使用消费者验证。

公共库额外要求见[公共库 README](../../charts/homelab-common/README.md)；其契约测试涵盖删除消费者源码后从包渲染。

## tracing-stack 交付

[package_release.py](../../charts/tracing-stack/tests/package_release.py) 创建带依赖的交付目录，先联网重建依赖、lint 和渲染，再打包。输出目录必须尚不存在。

`--offline` 表示生成含镜像的离线交付物；构建阶段仍需要 registry 网络和 Docker，会拉取、检查并导出镜像。在线包不含 `images.tar`。该脚本不自动运行完整 `check_render.py` 或线上 smoke，不能用打包成功替代它们。

命令、交付清单、校验和与镜像导入说明维护在[tracing-stack README](../../charts/tracing-stack/README.md)，它也被脚本复制到交付目录，必须保持独立可读。

## HTTP Helm 仓库

现有仓库地址为 `https://helm-chart.snubisks.com`，根目录 [index.yaml](../../index.yaml) 记录制品条目。远程实际可用性需要发布后验证，不能从本地索引推断。

1. 在独立发布目录准备版本化 tgz、校验值与索引变更。
2. 合并原有索引，保留其他 chart 和历史版本；不可用只含新包的目录生成索引后直接覆盖全仓索引。
3. 审查制品 URL、版本和摘要，先上传制品，再发布引用它的索引。
4. 从远程重新拉取，核验摘要；应用从 tgz 渲染，library 通过独立消费者构建、打包和渲染。

站点上传和 CI 部署方式未在本仓库提供统一脚本，本页不假定上传命令。正式发布时按实际发布环境执行并记录验证结果。
