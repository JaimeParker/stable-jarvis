# Task 3: Formula Derivation & Theorems

深入追溯论文中关键公式的数学推导链和损失函数的计算过程。

## 关键公式推导链
不要只列出最终公式。追溯数学叙事：
- 链条：识别关键公式的演进路径（通常 3-5 个核心公式的递进关系）
- 逻辑：对每次过渡，用 LaTeX 渲染公式，并解释作者**为什么**做此修改（不是为了改而改，要解释动机）
- 符号定义：定义每个使用的符号（首次出现时）

## 最终损失函数
- Actor Loss：完整公式 + 每个项的物理含义
- Critic Loss：完整公式 + 每个项的物理含义
- 其他辅助损失（如 entropy regularization、BC regularization 等）

## Loss 计算追踪
针对最终 Loss（actor 和 critic 各自的），逐步描述单次更新的计算过程：
- 数据从哪里来？（replay buffer? online interaction? both?）
- 每一步是网络预测还是固定目标？
- 梯度在哪里停止？（target network? detached?）
- 如果使用了 ensemble，min/mean 截断在哪里发生？

输出格式：Markdown，至少 300 字。所有公式用 LaTeX 渲染。
