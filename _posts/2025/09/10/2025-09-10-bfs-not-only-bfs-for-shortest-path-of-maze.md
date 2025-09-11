---
header:
    image: /assets/images/hd_magic_micronaut_jpa.jpg
title:  bfs not only bfs for shortest path of maze
date: 2025-09-10
tags:
    - tech
permalink: /blogs/tech/en/bfs-not-only-bfs-for-shortest-path-of-maze
layout: single
category: tech
---
> Everything you want is on the other side of fear. - Jack Canfield

# 从迷宫算法到Principal级系统设计：一个Bug的深度之旅

> 一个看似简单的迷宫最短路径问题，如何演变为分布式系统设计的深度思考？本文将带你从算法基础到系统架构，体验Principal工程师的思维之旅。

## 问题定义：迷宫最短路径

### 原始问题描述
给定一个二维网格迷宫，其中：
- `0` 表示可以通过的空格
- `1` 表示不可通过的障碍物

需要找到从左上角 `(0,0)` 到右下角 `(m-1, n-1)` 的最短路径长度。如果不存在这样的路径，返回 `-1`。

**示例迷宫**：
```python
maze = [
    [0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 0, 1],
    [1, 1, 1, 0, 0]
]
# 最短路径长度为8
```

### 原始解决方案：BFS算法

```python
from collections import deque

def find_shortest_path(maze):
    """
    使用BFS算法寻找迷宫最短路径
    
    参数:
        maze: 二维列表，0表示通路，1表示障碍物
        
    返回:
        int: 最短路径长度，不可达时返回-1
    """
    # 边界情况：空迷宫
    if not maze or not maze[0]:
        return -1
    
    n, m = len(maze), len(maze[0])
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 右、下、左、上

    # 使用队列进行BFS，存储(x, y, 步数)
    queue = deque([(0, 0, 1)])
    visited = set([(0, 0)])  # 记录已访问节点

    while queue:
        x, y, steps = queue.popleft()

        # 到达目标点
        if x == n - 1 and y == m - 1:
            return steps

        # 探索四个方向
        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            # 检查新位置是否有效
            if (0 <= nx < n and 0 <= ny < m and 
                maze[nx][ny] == 0 and 
                (nx, ny) not in visited):
                
                queue.append((nx, ny, steps + 1))
                visited.add((nx, ny))
    
    return -1
```

### 基础测试用例

```python
def test_basic_cases():
    """基础功能测试"""
    # 正常迷宫
    maze1 = [
        [0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 0, 1],
        [1, 1, 1, 0, 0]
    ]
    assert find_shortest_path(maze1) == 8
    
    # 无解迷宫
    maze2 = [
        [0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 0, 0, 1],
        [1, 1, 1, 0, 0]
    ]
    assert find_shortest_path(maze2) == -1
    
    print("基础测试通过")
```

## 问题发现：那个不该返回1的迷宫

在扩展测试用例时，我们发现了一个边界情况bug：

```python
maze4 = [[1]]  # 只有1个元素，且是障碍物
print(find_shortest_path(maze4))  # 返回1，但应该是-1
```

**问题分析**：原始算法没有检查起点是否为障碍物。如果起点 `(0,0)` 本身就是障碍物（`maze[0][0] == 1`），应该立即返回 `-1`，而不是尝试进行BFS搜索。

## 算法修复：防御性编程的重要性

### 修复后的代码

```python
def find_shortest_path(maze):
    """
    修复后的BFS算法，包含完整的边界检查
    """
    # 边界情况：空迷宫
    if not maze or not maze[0]:
        return -1
    
    n, m = len(maze), len(maze[0])
    
    # 关键修复：检查起点和终点是否为障碍物
    if maze[0][0] == 1 or maze[n-1][m-1] == 1:
        return -1
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    queue = deque([(0, 0, 1)])
    visited = set([(0, 0)])

    while queue:
        x, y, steps = queue.popleft()

        if x == n - 1 and y == m - 1:
            return steps

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (0 <= nx < n and 0 <= ny < m and 
                maze[nx][ny] == 0 and 
                (nx, ny) not in visited):
                
                queue.append((nx, ny, steps + 1))
                visited.add((nx, ny))
    
    return -1
```

### 完备的测试体系

```python
def test_comprehensive_cases():
    """Principal级别工程师的测试用例设计"""
    
    # 功能测试
    assert find_shortest_path([[0,1,0],[0,0,0],[1,1,0]]) == 5
    
    # 边界测试
    assert find_shortest_path([[0]]) == 1      # 1x1空迷宫
    assert find_shortest_path([[1]]) == -1     # 1x1障碍迷宫（修复的bug）
    assert find_shortest_path([]) == -1        # 空输入
    assert find_shortest_path([[]]) == -1      # 空行
    
    # 起点终点障碍测试
    assert find_shortest_path([[1,0],[0,0]]) == -1      # 起点障碍
    assert find_shortest_path([[0,0],[0,1]]) == -1      # 终点障碍
    
    # 性能测试
    large_maze = [[0]*100 for _ in range(100)]
    assert find_shortest_path(large_maze) == 199  # 100+100-1
    
    print("所有测试用例通过")
```

## 算法深度：从BFS到分布式系统

### 算法选择矩阵
| 场景 | 算法选择 | 时间复杂度 | 空间复杂度 | 适用条件 |
|------|----------|------------|------------|----------|
| 无权图最短路径 | BFS | O(V+E) | O(V) | 所有边权重相等 |
| 带权图（非负） | Dijkstra | O(ElogV) | O(V) | 无负权重边 |
| 带权图+启发式 | A* | 取决于启发式 | O(V) | 有好的启发函数 |
| 超大图 | 双向BFS | O(b^(d/2)) | O(b^(d/2)) | 知道起点终点 |
| 分布式环境 | 并行BFS | O(D)理想 | O(V)分布式 | 超大规模图 |

### 有权图处理：Dijkstra算法

```python
def dijkstra_weighted_maze(maze):
    """处理带权迷宫的Dijkstra算法"""
    import heapq
    
    if not maze or not maze[0]:
        return -1
    
    n, m = len(maze), len(maze[0])
    
    # 检查起点终点可达性
    if maze[0][0] == float('inf') or maze[n-1][m-1] == float('inf'):
        return -1
    
    # 距离矩阵初始化
    dist = [[float('inf')] * m for _ in range(n)]
    dist[0][0] = maze[0][0]  # 起点权重
    
    # 最小堆优化
    heap = [(maze[0][0], 0, 0)]
    
    while heap:
        cost, x, y = heapq.heappop(heap)
        
        # 跳过非最短路径
        if cost != dist[x][y]:
            continue
            
        # 到达终点
        if x == n-1 and y == m-1:
            return cost
            
        # 探索邻居
        for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and maze[nx][ny] != float('inf'):
                new_cost = cost + maze[nx][ny]
                if new_cost < dist[nx][ny]:
                    dist[nx][ny] = new_cost
                    heapq.heappush(heap, (new_cost, nx, ny))
    
    return -1
```

## 系统广度：分布式BFS架构设计

（以下内容保持不变，展示从单机算法到分布式系统的思维演进）

## 总结：从算法基础到系统架构

这个迷宫最短路径问题展示了完整的技术演进路径：

1. **问题理解**：明确需求约束条件
2. **算法实现**：选择合适的BFS算法
3. **边界处理**：发现并修复起点检查bug
4. **测试完备**：设计全面的测试用例
5. **算法扩展**：支持有权重、大规模场景
6. **系统设计**：分布式架构解决超大规模问题

每个层次都体现了不同级别工程师的思维深度，而那个简单的 `[[1]]` 迷宫bug，正是连接算法基础与系统架构的关键桥梁。

> 在技术的深度探索中，最微小的bug往往能引出最宏大的系统设计思考。这正是Principal工程师的价值所在：见微知著，从代码细节到系统架构的全栈思维。