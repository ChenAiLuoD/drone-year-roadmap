# 数据说明

## 来源

- 数据集：UAVDT-Benchmark-M
- 官方主页：https://sites.google.com/view/grli-uavdt
- DET/MOT toolkit：UAVDT 官方下载页提供的 DET/MOT toolkit
- Attributes：UAVDT 官方下载页提供的 Attributes
- 访问日期：2026-11-08
- 本地根目录：data/
- 当前图像清点：40,735 张 JPG（以下载后本地命令输出为准）

## 许可和用途

UAVDT 官方主页说明数据集仅限研究用途。toolkit 自带 README 说明其评估代码以 GNU GPL 发布；代码许可与数据集使用限制分别记录，不把 GPL 自动解释成数据集的开放再分发许可。

本项目只用于个人学习、研究和本地作品集实验。原始图像、原始标注、忽略区域、属性文件和可还原数据集的派生文件不提交 Git、不上传公开仓库、不重新分发。若未来需要商业或闭源使用，必须重新联系数据作者确认许可。

## 原始类别

*_gt_whole.txt 的 object_category 定义为：

~~~text
1 = car
2 = truck
3 = bus
~~~

第一版项目统一为：

~~~text
car / truck / bus -> vehicle -> class 0
~~~

## 文件角色

- UAVDT-Benchmark-M/：按序列保存原始图像帧。
- UAVDT-DET-MOT-toolkit/GT/*_gt_whole.txt：完整检测真值，包含原始类别、出画和遮挡字段。
- UAVDT-DET-MOT-toolkit/GT/*_gt.txt：MOT 轨迹真值，保留帧号和轨迹 ID。
- UAVDT-DET-MOT-toolkit/GT/*_gt_ignore.txt：忽略区域。
- UAVDT-Attributes/train/：官方训练序列属性。
- UAVDT-Attributes/test/：官方 DET/MOT 测试序列属性。

原始目录和标注正文不改写。转换数据若产生，放入新的版本目录并记录转换规则与统计量。
