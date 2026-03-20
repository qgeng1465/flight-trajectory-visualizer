# 🌍 Geo-Intelligence Pro: Local-First Spatial & Flight Trajectory Visualization
**Language:** [English](#english) | [中文](#chinese)

<a id="english"></a>
## 📖 Overview
**Geo-Intelligence Pro** is a high-performance, fully offline 3D WebGL visualization system designed for rendering massive spatial data and flight trajectories. Initially developed for researchers handling high-throughput clinical cohort distributions and macro-economic flow analyses, it translates complex spatial relationships into intuitive 3D arcs and heatmaps.

## 🚀 Vision & Goals
Our ultimate goal is to build a **Privacy-First (100% local processing) and Hardware-Friendly** spatial visualization platform. 
We aim to break the hardware barrier: through advanced offline data dimensionality reduction (Python-based spatial clustering), we ensure that even standard laptops **without dedicated GPUs** can smoothly render tens of thousands of complex topological networks at 60 FPS.

## ✨ Core Features
* **🌍 Fully Offline Architecture:** Relies on local 10m-resolution TopoJSON boundaries and Earth textures. No internet connection required after cloning.
* **⚡ Extreme Performance & Compression:** Includes a Python preprocessing pipeline to aggregate raw trajectory CSVs, calculating traffic weights to drastically reduce browser memory overhead.
* **🔍 Semantic Zoom (LOD Engine):** Dynamic Level-of-Detail rendering. Large hubs and medium-sized city labels progressively appear/fade based on the camera altitude, mimicking professional GIS software.
* **📊 Multi-Dimensional Layers:** Seamlessly toggle between 3D flight arcs (with dynamic traffic thickness/color) and core hub heatmaps (3D altitude cylinders).
* **📸 Academic Snapshot Export:** One-click high-resolution WebGL canvas export (PNG) for direct inclusion in academic papers or analytical reports.
* **⚙️ Physical Auto-Rotation:** Customizable Earth rotation speed, ranging from a 15-second high-speed demo mode to real-time Earth sync velocity.

## 🛠️ Getting Started (Local Deployment)
1. **Pre-process Data:** Run the included Python script (`optimize_airports.py` or `compress_flights.py`) to compress your raw CSV data and calculate edge weights.
2. **Start Local Server:** Run the `Start_Server.bat` to bypass browser CORS restrictions.
3. **Visualize:** Open the provided `localhost` URL in your browser, import your compressed `.csv`, and explore.

## 🚧 Current Status
This project is currently under **Active Development**. I am continuously refactoring the codebase, optimizing individual modules, and exploring new algorithms to handle even larger spatial datasets locally. Contributions and feedback are welcome!

---

<a id="chinese"></a>
# 🌍 地理空间智能分析系统 (纯本地极限性能版)

## 📖 项目简介
**Geo-Intelligence Pro** 是一个高性能、纯本地运行的 3D WebGL 可视化系统，专为渲染海量空间流向数据和飞行轨迹而设计。本项目最初为处理高通量临床队列分布和宏观经济跨区域资金流向的科研人员打造，能够将复杂的空间关系转化为直观的 3D 连线与热力枢纽。

## 🚀 愿景与目标
我们的终极愿景是打造一个**极致注重隐私（100% 数据本地处理）且对硬件极度友好**的可视化平台。
致力于打破算力壁垒：通过引入先进的离线数据降维技术（Python 空间聚类聚合），彻底释放浏览器内存，让**没有独立显卡的普通轻薄笔记本**也能满帧（60 FPS）流畅运行数以万计的复杂空间拓扑网络。

## ✨ 核心功能
* **🌍 纯离线架构:** 核心渲染依赖本地 10m 级别的高精度 TopoJSON 省界与地球贴图，告别网络延迟与数据泄露风险。
* **⚡ 极限降维与聚合:** 配备 Python 离线数据清洗与聚类脚本，提前计算航线流量权重，将几十兆的原始数据压缩至几百 KB。
* **🔍 智能视锥体缩放 (LOD):** 引入类似百度地图的按需加载逻辑，随着视角放大（高度降低），大型枢纽与中型城市的名称标签会动态浮现。
* **📊 多维度图层解析:** 自由切换 3D 飞行轨迹线（粗细与颜色由流量权重动态决定）与核心枢纽热力图（3D 柱状体）。
* **📸 科研级快照导出:** 一键保存当前 WebGL 渲染帧为高清 PNG，方便直接插入学术论文或科研简报。
* **⚙️ 物理级自转控制:** 支持从 15秒/圈 的高速演示模式到真实地球同步角速度的自由切换。

## 🛠️ 如何运行 (本地部署)
1. **数据预处理:** 运行项目中的 Python 脚本（如 `compress_flights.py`），对庞大的原始 CSV 进行离线聚合与权重计算。
2. **启动本地服务:** 双击运行 `Start_Server.bat` 启动本地轻量级服务器，跨越浏览器本地跨域限制。
3. **渲染与交互:** 在浏览器中打开本地端口，导入刚刚生成的极致精简版 `.csv` 文件，即可体验丝滑的 3D 交互。

## 🚧 开发状态
本项目目前处于 **活跃开发阶段 (Active Development)**。我正在持续重构前端代码底座，优化各个独立数据模块的加载性能，并探索能让本地浏览器承载更大规模空间数据的新算法。欢迎交流与探讨！
