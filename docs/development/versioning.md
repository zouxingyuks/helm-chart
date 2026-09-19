# Chart 版本规则

本页维护项目专属 chart 版本契约；Agent 执行流程见 [helm-chart-version](../../.agents/skills/helm-chart-version/SKILL.md)。规则不自动迁移现有 chart，`appVersion` 独立维护，Git tag 不是发布前提。

## 格式与校验

格式为 `ArchVer.Major.Minor-Tag.Patch[-Mark]`，不带 `v`，例如 `1.2.3-beta.4`、`1.2.3-beta.4-test.1`。

- `ArchVer` 为正整数，其余数字字段为非负整数，均禁止前导零。
- 默认 Tag 仅允许小写 `alpha`、`beta`、`lts`；其他 Tag 必须先明确用途和递增基准，再扩展校验规则。
- Mark 非空，仅允许小写字母、数字、连字符和点，整体首尾必须为字母或数字；点分段不能为空，独立的纯数字分段禁止前导零。
- Mark 仅标识临时测试产物，不参与正常发布基准；产物可能在测试后删除。删除必须有明确清理指令，不因临时性质自动执行。

以下 Python 正则使用 `re.fullmatch` 匹配整个版本号，之后还须检查 Mark 中的独立纯数字分段：

```python
VERSION_PATTERN = r"(?P<arch>[1-9][0-9]*)\.(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)-(?P<tag>alpha|beta|lts)\.(?P<patch>0|[1-9][0-9]*)(?:-(?P<mark>[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?))?"

def valid_version(value):
    import re

    match = re.fullmatch(VERSION_PATTERN, value)
    if match is None:
        return False
    mark = match.group("mark")
    return mark is None or all(
        part and (not part.isdigit() or part == "0" or not part.startswith("0"))
        for part in mark.split(".")
    )
```

| 示例 | 校验结果 |
| --- | --- |
| `1.0.0-beta.0`、`1.0.0-beta.0-test.1`、`1.0.0-beta.0-fix-123` | 有效 |
| `v1.0.0-beta.0`、`0.0.0-beta.0`、`1.00.0-beta.0` | 无效 |
| `1.0.0-BETA.0`、`1.0.0-stable.0` | 默认规则无效 |
| `1.0.0-beta.0-test..1`、`1.0.0-beta.0-test.01`、`1.0.0-beta.0-test-` | 无效 |

## 变更级别

以待发布内容相对所选已发布基准的实际变化判断，混合变更取最高级别，只递增一次。高位递增时所有低位数字归零；不按 commit 数量或中间测试发布次数累加。

| 字段 | 递增条件 |
| --- | --- |
| `ArchVer` | 普通迭代固定；只有明确批准的产品代际变化才递增 |
| `Major` | 不兼容更新：破坏受支持配置、资源名称、selector 或 PVC 身份，或升级需要手动迁移等 |
| `Minor` | 兼容地新增独立部署能力 |
| `Patch` | 兼容的配置补充、修复、维护和 chart 包内文档修正 |

判断兼容性以现有受支持部署能否按正常升级流程继续工作为准。依赖、默认镜像、配置变化按实际影响分级，不一律归为 Patch。只改变仓库外层文档、开发工具且不影响 chart 制品时，不提升 chart 版本；仅修改版本字段不是变更依据。无内容变更不发版。

例如基准为 `1.2.3-beta.4`，基础修复得到 `1.2.3-beta.5`，新增兼容的独立部署能力得到 `1.2.4-beta.0`，不兼容更新得到 `1.3.0-beta.0`；获准的新产品代际得到 `2.0.0-beta.0`。

## 通道与基准

“已发布”指目标发布渠道中已有可获取的 chart 制品。工作区的 `Chart.yaml`、本地 tgz 或 Git tag 单独存在都不能证明已发布。Git 记录可辅助关联源码，但不强制创建 tag。

所有正常基准都限定在同一 chart 和目标维护线，排除带 Mark 的版本；不跨维护线取全仓最大版本，不跨 Tag 用 SemVer 排序推断业务上的最新版本。

| 通道 | 用途与递增基准 |
| --- | --- |
| `alpha` | 发布前内测；首次从目标稳定基线起步，后续相对该维护线的上个已发布 alpha 递增 |
| `beta` | 常规公开发布，也是正常使用最多的通道；公测与正式使用不由版本号区分，生产验证状态记录在 release notes |
| `lts` | 长期支持；首次从获准长期支持的 beta 保留数字创建，后续相对该 LTS 维护线的上个已发布 lts 递增 |

beta 始终相对该维护线的上个已发布 beta 重新计算全部数字。从 alpha 转入 beta 不是替换 Tag，不继承 alpha 的发布次数或部分数字。例如上个 beta 为 `1.2.3-beta.4`，中间多个 alpha 累计引入不兼容变更，则目标为 `1.3.0-beta.0`。

首次创建获准的 LTS 通道允许沿用 beta 内容和数字；这是支持承诺变化，不是同一通道内的无变更重复发版。

全新 chart 首个 alpha 为 `1.0.0-alpha.0`，首个 beta 为 `1.0.0-beta.0`。已有 chart 遇到旧格式时，必须明确迁移基准和首个目标版本，不能自动重置成全新 chart 的起点。已有 chart 的维护线没有对应通道历史或起步基线不明确时，先确认基准，不套用全新 chart 的初始化规则。

测试改动最终进入正常发布时，仍与目标维护线上个不带 Mark 的对应通道版本比较；不依赖临时产物继续存在。

## Helm 工具语义

本项目业务字段不同于 SemVer 的字段语义：Helm 将 `ArchVer.Major.Minor` 当作 SemVer 的前三位，将 `Tag.Patch[-Mark]` 当作 prerelease。因此 `beta` 和 `lts` 在 Helm 中仍是 prerelease，普通版本范围不能代表本项目的兼容性承诺。

安装和依赖示例使用明确版本。例如安装时传入 `--version 1.0.0-beta.0`，依赖声明使用 `version: "1.0.0-beta.0"`；这些是格式示例，不表示该制品已发布。搜索 prerelease 需使用 `helm search repo <keyword> --devel`。Mark 不是 SemVer 的 `+build` 元数据，会参与工具排序，不能依赖排序自动排除测试版本。

官方依据：[Charts and Versioning](https://helm.sh/docs/topics/charts/#charts-and-versioning)、[helm search repo](https://helm.sh/docs/helm/helm_search_repo/)。制品发布与远程验证继续遵循[发布指南](releasing.md)。
