# Task 2: Algorithm & Architecture

分析论文的核心算法设计和网络架构，聚焦于工程实现层面的细节。

## 方法概述
用一段话总结最终提出的机制/算法。

## 算法循环
以清晰的逐步列表呈现训练循环。区分不同阶段（如 Pre-training vs. Fine-tuning、Pre-sample vs. Online）。

## 数据流图
生成一个 Mermaid 图代码块（flowchart TD），可视化：
- 数据从何处来（offline dataset? online interaction?）
- 训练阶段和数据流方向
- 关键网络组件及其交互关系

## 网络架构
- Actor 的输入/输出具体是什么？（如 state → single action? action chunk?）
- Critic 的输入/输出具体是什么？（如 (state, action) → scalar Q? ensemble?）
- Backbone 是什么？（MLP? U-Net? Transformer? CNN?）
- 是否有特殊的网络设计选择？（如 LayerNorm、Q-ensemble、权重共享等）

输出格式：Markdown，至少 300 字。Mermaid 图放在独立代码块中。
