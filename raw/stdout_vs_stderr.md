stderr vs stdout 的分离（见 agent.py:27-29）：_progress 写到 stderr，是因为这个脚本被设计成 CLI 管道友好——stdout 留给"最终答案"，这样如果有人 python agent.py | some_other_tool，管道里不会混入这些进度日志。这是 Unix 哲学里"数据流"和"人类可读的元信息"分离的经典做法。


