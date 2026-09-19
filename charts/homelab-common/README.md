# homelab-common

供应用 Chart 使用的 Helm library，版本 **0.1.0**。不生成 Kubernetes 资源，不读取集群，不提供应用、数据库或 tracing 拓扑。支持 Helm 3.12+ / 4；需要通过应用 Chart 消费，不能独立安装。

## 来源与维护方式

本库维护 Bitnami common **2.41.0** 的必要源码子集，所有定义和内部调用均改为 `homelab.common.*`。`Chart.yaml` 明确声明 `dependencies: []`，没有运行时 Bitnami 依赖，无需下载嵌套 chart，发布包包含全部实现、LICENSE 和 NOTICE。

不采用简单 wrapper 或 dependency alias：Helm named templates 是全局的，alias 不会重命名 `common.*`。DeepLX 已依赖 common 2.10.1；wrapper 可能受另一版本覆盖影响。源码隔离使本库行为不受第三方 common 版本影响，但不能消除第三方 chart 之间自身的 common 冲突。

参考制品 `common-2.41.0.tgz` 的 SHA-256：
`f29eae562b8945add10869416586f0190cba79b0bcd231d036571862a52f7b1b`。
上游：[Bitnami charts](https://github.com/bitnami/charts/tree/main/bitnami/common)。保留 Broadcom 版权和 Apache-2.0 许可证；改编范围见 NOTICE。升级上游时逐项审查选用 helper、内部 include、许可与行为差异，运行本库测试；不批量覆盖源码。

设计依据是 AxonHub、LobeHub、Subconverter 的命名、标签和 ServiceAccount 重复实现，以及其镜像、拉取凭据、PVC 模板；模板渲染与合并来自 DeepLX 的 common 使用方式。保留现有命名算法，未采用新版 Bitnami 的 release 名称规范化或标签清洗。标签保护、合并的空值语义、StorageClass 优先级是本库自己的明确契约，不宣称与全部 Bitnami API 等价。

## 消费

应用的 `Chart.yaml`（路径相对于应用目录）：

```yaml
dependencies:
  - name: homelab-common
    version: 0.1.0
    repository: file://../homelab-common
```

运行 `helm dependency build charts/<app>`，提交应用依赖锁文件并按仓库发布流程打包。消费者包须携带 `charts/homelab-common`；本地 file 路径不需要存在于安装机器。使用远程仓库时将 repository 换成实际发布地址并继续固定版本。仓库根目录提供版本化制品 `homelab-common-0.1.0.tgz` 和对应的 `index.yaml` 条目；远程消费需等待制品和索引发布到仓库站点。

```gotemplate
metadata:
  name: {{ include "homelab.common.names.fullname" . }}
  labels:
    {{- include "homelab.common.labels.standard" (dict "context" $ "customLabels" .Values.commonLabels) | nindent 4 }}
# Deployment spec.selector.matchLabels 和 Pod metadata.labels 都使用同一 selector 参数：
{{ include "homelab.common.labels.selector" (dict "context" $) }}
# 容器镜像：
image: {{ include "homelab.common.images.image" (dict "imageRoot" .Values.image "chart" .Chart) | quote }}
```

可直接构建、渲染的最小消费者是仓库的 `tests/homelab-common/fixture`，用 ConfigMap 展示全部 API 的输出；它是通用示例，不是可部署业务服务。

## 公开 API 与边界

以下名称均加前缀 `homelab.common.`。`context` 必须是**消费应用的根上下文 `$`**，不是 library 子值或 range 中的当前元素；`Chart` / `Release` 来自应用。未说明的可选 map/list 参数可省略或为 null，分别视为空 map/list。返回值均为字符串；YAML 片段使用 `nindent`，标量资源字段使用 `quote`。输入必须符合注明类型，库不负责把任意字符串变成合法 Kubernetes 名称。

| Helper / 参数 | 返回与优先级 |
| --- | --- |
| `names.name $` | `Values.nameOverride` 非空时优先，否则 `Chart.Name`；截断 63 字符后去掉末尾一个 `-`。 |
| `names.fullname $` | 非空 `fullnameOverride` 优先；否则取 nameOverride 或 Chart.Name，若 release 名含该名称则用 release，否则 `release-name`；同样截断与去尾。检查 contains 使用未截断名称。 |
| `names.chart $` | `Chart.Name-Chart.Version`，`+` 替换为 `_`，截断 63 后去尾 `-`。 |
| `labels.selector {context, component?}` | YAML map，只有 `app.kubernetes.io/name`、`app.kubernetes.io/instance`；非空字符串 component 显式增加 `app.kubernetes.io/component`。不读取自定义标签。 |
| `labels.standard {context, component?, customLabels?}` | YAML map：自定义标签在先，库的 chart、managed-by、非空 appVersion、selector 值覆盖冲突。无 appVersion 时不生成版本标签。不会 tpl 自定义标签。与 selector 使用相同 component，确保 Pod 可被选中。 |
| `images.image {imageRoot, global?, chart?}` | repository 必填且非空；registry 为非空 `global.imageRegistry` > `imageRoot.registry` > 无前缀。digest > 非空 tag > chart.AppVersion；均无则失败，不隐式 latest。tag 数字转字符串（0 按 Helm 空值规则视为缺省），推荐引号字符串。digest 包含算法如 `sha256:...`。repository 直接拼接，不解析已有 registry/tag；使用 registry 时 repository 应为不含 registry 的路径。 |
| `images.pullSecrets {global?, pullSecrets?, images?}` | 完整 `imagePullSecrets:` YAML 字段；全局 imagePullSecrets、显式 pullSecrets、images 各项的 pullSecrets 依次合并，首次出现顺序去重。接受字符串和 `{name: string}`；空名、非字符串失败。无项返回空字符串，不创建 Secret，不 tpl。 |
| `tplvalues.render {value, context, scope?}` | 字符串原样处理，其他值先 toYaml；含 `{{` 时执行 tpl。非空 scope 作为相对 `.`，`$` 仍为根上下文；空 scope 不启用相对作用域。只对可信配置使用，具有 Helm tpl 完整能力。 |
| `tplvalues.merge {values, context, scope?}` | values 为 map 或可渲染为 YAML map 的字符串列表；先 render 再深度合并，**靠前项优先**，包括 false、0、空字符串、空列表和 null；列表整体替换。空 map 不清除低优先级 map 的子键。空列表返回 `{}`，非法 YAML/非 map 失败，顶层 `Error` 保留用于检测解析错误。输入对象不被修改。 |
| `storage.class {persistence?, global?}` | 完整 `storageClassName:` YAML 字段；非空 persistence.storageClass > 非空 global.defaultStorageClass > 省略字段。`-` 输出显式空字符串，禁止默认 StorageClass；空值表示未配置而非禁用。忽略旧式 global.storageClass。只有显式传 global 才启用全局默认。 |
| `storage.claimName {persistence?, defaultName?}` | 非空 existingClaim > 非空 defaultName，否则失败；名称不做 tpl、截断或添加后缀。应用负责 PVC 创建条件和原始名称。 |
| `serviceAccount.name {context, serviceAccount?}` | 非空 name 优先；否则 create=true 时用应用 fullname，create=false/缺省时为 `default`。create 须为 boolean；应用负责创建条件、annotations、automount。 |

本库没有会自动注入应用的 values 默认值。nameOverride/fullnameOverride、component、storageClass、existingClaim 和各种自定义名字都应是字符串，标签 map 的值应为合法标签字符串。`tplvalues.merge` 的 values 参数必传且必须为列表（允许 `[]`）；缺失、null 或非列表会返回明确错误。应用应通过自己的 values schema 验证业务配置。

## 兼容性与接入约定

同一 minor 系列的 patch 不改变公开签名、缺省值、优先级或输出语义。0.x 的破坏性变更提升 minor 并提供迁移说明；1.x 后遵循 SemVer。上游 Bitnami 版本变化不会自动进入本库。固定版本并审查升级 diff，不能把 library 更新视为自动迁移应用。

名称、selector、PVC 是持久身份：升级中不要更改 nameOverride、fullnameOverride、component，也不要把 commonLabels/podLabels 加入 selector。原有应用如果已使用自定义 selector，应继续保留原 helper；需要变更时单独制定资源重建方案。标准标签不替代 selector helper。

### tracing-stack 接入交接

1. 增加上述固定版本 file 依赖，构建并检查 Chart.lock。无需移除其第三方子 Chart 的 Bitnami common。
2. 保留 tracing-stack 自己的 helper 名称作为适配层，仅委托等价的库方法；组件 suffix、组件 selector、数据库连接、端口、拓扑等仍由应用维护。fullname helper 截断后再添加 suffix 与添加 suffix 后截断并不等价，必须保留原顺序。
3. 对每个工作负载同时迁移 selector 和 Pod labels，传入完全相同的显式 component。库缺省不会添加 component；已有 selector 的每个键和值都要保持。
4. 镜像逐组件传 imageRoot；只有原行为允许时传 global/chart（appVersion 回退不一定适用于数据库或 sidecar）。顶层 imagePullSecrets 显式传入，库不会自动读取应用 Values。
5. PVC 使用 `storage.claimName` 时 defaultName 传**原来的完整 claim 名称**，不直接改为库 fullname。应用继续使用 `enabled && !existingClaim` 创建条件；StatefulSet volumeClaimTemplates 名称、访问模式、容量、保留策略留在应用。首次迁移不要顺便启用 global.defaultStorageClass，也不要把历史 `-` 字面值不经审核改成空 StorageClass。
6. serviceAccount 配置显式传入；应用仍负责资源创建和 automount。若原应用默认 create=true，应在应用 values 中保留这个默认。
7. 离线对比接入前后 `helm template`：资源 kind/name/namespace、selector、Pod 标签、PVC/claimTemplate 名称、claimName 和 storageClassName 必须不变。测试默认、覆盖名、现有 PVC、各组件启停和外部存储配置。最后打包消费者并从 tgz 渲染；本库测试不代替应用回归测试。

## 验证

见仓库 `tests/homelab-common/README.md`。测试在临时目录构建依赖、lint、渲染、检查边界、与真实 Bitnami common 共存、打包并删除消费者源码后从包渲染。不会访问 Kubernetes。示例和测试位于 chart 外，不进入公共库安装包。

## 打包与正式发布

本库没有运行时依赖，直接打包即可，无需生成 Chart.lock：

```sh
helm lint charts/homelab-common --strict
helm package charts/homelab-common --destination /tmp/helm-chart-dist
sha256sum /tmp/helm-chart-dist/homelab-common-0.1.0.tgz
```

发布前运行完整契约测试，并检查 tgz 包含 Chart.yaml、templates、LICENSE、NOTICE、README.md。测试 fixture 不随库发布。版本发布后不可覆盖同版本制品；变更必须提升 Chart.yaml 的 version。

本仓库现有 HTTP Helm 仓库为 `https://helm-chart.snubisks.com`。正式发布时，将版本化 tgz 放到该站点可下载的位置，再把新 chart 条目合并到原 index.yaml，保留其他版本和应用条目。应在独立发布目录准备索引，审核差异后再发布，不能用仅含本库的目录直接覆盖现有索引。制品应先于引用它的索引上线。

发布完成后，远程消费者可使用：

```yaml
dependencies:
  - name: homelab-common
    version: 0.1.0
    repository: https://helm-chart.snubisks.com
```

消费者运行 `helm dependency update` 生成锁文件并打包；CI 使用 `helm dependency build` 根据锁文件重建依赖。发布验收应从远程仓库重新拉取本库，在独立消费者中构建、打包并离线渲染。上述远程依赖地址只有在该版本正式发布后才可用。
