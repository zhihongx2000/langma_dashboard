# 前端界面启动命令
> 前置条件：需要先安装好 Node.js 和 npm。
> Node.js版本：v22.22.1
> npm版本：10.9.4

```bash
cd frontend
npm install
npm run dev
```

# 后端接口启动命令
> 前置条件：安装好 uv 管理工具。
> python版本：3.12
> uv版本： 0.10.12

首先，同步虚拟环境：
```
uv python install 3.12

uv venv .venv --python 3.12

uv sync
```

# 填写环境变量
将 env.example 文件复制一份并命名为 .env，然后根据实际情况修改其中的环境变量值。

# git分支管理
- main：主分支，存放稳定的代码版本。
- develop-hong：开发分支，存放hong正在开发中的代码。
- develop-yinan：开发分支，存放yinan正在开发中的代码。
- develop-lei：开发分支，存放sulei正在开发中的代码。
