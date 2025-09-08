# 🧠 智谱AI多图分析工具

一个简单易用的桌面应用，支持拖拽上传多张图片，批量调用智谱AI（ZhipuAI）的视觉模型进行分析，并自动保存结果。

<img width="1036" height="916" alt="e9e237a7c5d6ba2b47be646423391ec6" src="https://github.com/user-attachments/assets/5995a7ec-d501-46d4-98ec-9c9be12ff660" />

## ✨ 功能特性

- ✅ 拖拽上传多张图片（支持 JPG/PNG/BMP/WebP）
- ✅ 批量调用 `glm-4v` 或 `glm-4.5v` 视觉模型
- ✅ 自定义系统提示词与用户问题
- ✅ 分析结果实时显示 + 自动保存为文本
- ✅ 支持配置记忆（API Key、提示词等）
- ✅ 暗色主题，美观易用

## 🚀 快速开始

### 方法1：下载可执行文件（推荐新手）

👉 [点击下载最新版 .exe](https://github.com/spacexyqc/zhipu-vision-tool/releases/tag/1.0)

> 无需安装Python，双击即可使用（仅限Windows）

### 方法2：从源码运行

```bash
git clone https://github.com/你的用户名/zhipu-vision-tool.git
cd zhipu-vision-tool
pip install -r requirements.txt

python main.py

