# Task 4: Literature Cross-Analysis

将论文与知识库中已有论文和笔记进行交叉对比分析。主 agent 会提供 KB context（相关论文的标题、摘要）。

## 与知识库论文的具体对比
逐篇对比知识库提供的相关论文，指出：
- 方法层面的异同（problem formulation、算法设计、假设条件）
- 实验层面的异同（benchmark 重叠、性能对比）
- 哲学层面的异同（倾向于解决什么问题？用什么思路？）
- 引用时注明论文标题

## 哲学对比
这篇论文的方法哲学与知识库中学派的差异：
- 属于哪个技术路线？（如 "Critic-Calibration" vs. "Actor-Constraint"？"Data Accumulation" vs. "Data Discarding"？）
- 与前人工作的根本分歧点在哪里？

## 技术关联
- 是否使用了与先前论文相似的 backbone 或 loss 组件？（如 IQL-style advantage、CQL 的保守项）
- 是否站在某个技术路线的基础上做了改进？

输出格式：Markdown，至少 250 字。必须注明每篇对比论文的标题。提及的论文/方法若 Obsidian vault 中有对应笔记，使用 `[[wikilink]]` 链接（参考 `note-mapping.md` 或自行 `search_notes` 查找）。不编造未出现在知识库或论文原文中的引用。
