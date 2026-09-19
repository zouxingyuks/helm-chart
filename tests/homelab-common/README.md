# 公共库契约测试

需要 Helm 3.12+ 或 Helm 4、Python 3.9+ 和 PyYAML（`python3 -m pip install -r tests/homelab-common/requirements.txt`）。所有构建产物写入系统临时目录；不操作集群、不修改消费者源文件。

准备可信的 Bitnami common 2.10.1 与 2.41.0 tgz，然后执行：

```sh
python3 tests/homelab-common/test.py \
  --common /path/to/common-2.10.1.tgz \
  --common /path/to/common-2.41.0.tgz
```

`--common` 可重复，用于增加兼容性矩阵。程序打印实际 Helm 版本及参考制品 SHA-256，使用真实 common helper，逐版本验证共存，不联网下载依赖。2.41.0 校验值见公共库 README；2.10.1 的参考校验值：`c0c8a32b011e060c4158438f3395b514cc2342d1c86833a47d61c476f1fb0b8e`。

覆盖命名截断/override/release 包含名称、selector 稳定性与标签冲突、镜像回退/digest/global、拉取凭据去重与错误、StorageClass 省略/禁用/优先级、existingClaim、ServiceAccount、tpl 相对上下文、map 合并及空值、strict lint、library 和消费者包内容、删除消费者源码后离线渲染。

`fixture` 是最小消费示例，输出一个 ConfigMap 展示 helper 结果；不是生产工作负载。手工验证可运行：

```sh
helm dependency build tests/homelab-common/fixture --skip-refresh
helm template demo tests/homelab-common/fixture
```

手工命令会在 fixture 内生成依赖和锁文件；这些产物由 fixture 的 .gitignore 排除。自动测试无需清理。
