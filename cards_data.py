"""Python 语法 / 算法知识点卡片。

content 支持轻量 Markdown：空行分段、``` 代码块、行内 `code`。
"""

CARDS = [
    {
        "title": "input() 读到的永远是字符串",
        "category": "基础语法",
        "summary": "要参与计算，先转换成 int 或 float。",
        "tags": "输入,int",
        "content": """`input()` 返回的是字符串，所以 `input() + 1` 会报 TypeError。

```python
n = int(input())                 # 单个整数
a, b = map(int, input().split()) # 一行两个整数
nums = list(map(int, input().split()))  # 一行多个整数
```

一次读不完时，可以用 `sys.stdin.read().split()` 把所有数字一次拿到手。""",
    },
    {
        "title": "range 的三种常见写法",
        "category": "基础语法",
        "summary": "range(stop) 从 0 开始，range(start, stop) 左闭右开。",
        "tags": "循环,range",
        "content": """```python
for i in range(5):        # 0 1 2 3 4
for i in range(1, 6):     # 1 2 3 4 5
for i in range(5, 0, -1): # 5 4 3 2 1
```

注意 `range(n)` 不包含 n，这是「差一错误」最常见的来源。""",
    },
    {
        "title": "条件表达式与短路求值",
        "category": "基础语法",
        "summary": "a if cond else b 可以一行完成判断。",
        "tags": "if,表达式",
        "content": """```python
sign = "正数" if x > 0 else "非正数"
```

`and` / `or` 会短路：`if n and nums[0] > 0:` 在 n 为 0 时不会去访问 `nums[0]`，可以顺手防越界。

但不要依赖短路做复杂逻辑，可读性优先。""",
    },
    {
        "title": "列表推导式",
        "category": "基础语法",
        "summary": "一行生成列表，比 for + append 更快也更短。",
        "tags": "推导式,list",
        "content": """```python
squares = [x * x for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

字典和集合也有推导式：

```python
count = {c: 0 for c in "abc"}
unique = {x for x in nums}
```""",
    },
    {
        "title": "函数的返回值与默认参数",
        "category": "基础语法",
        "summary": "没有 return 的函数返回 None；默认参数不要用可变对象。",
        "tags": "函数,return",
        "content": """```python
def add(a, b=1):
    return a + b

print(add(2))    # 3
print(add(2, 5)) # 7
```

**坑**：`def f(a, b=[])` 里的列表会被所有调用共享，需要默认空列表时写 `b=None` 再在函数内判断。""",
    },
    {
        "title": "list 常用操作",
        "category": "容器与字符串",
        "summary": "append / pop / sort / sorted / index / count",
        "tags": "list,排序",
        "content": """```python
a = [3, 1, 2]
a.append(4)     # [3, 1, 2, 4]
a.sort()        # 原地排序，返回 None
b = sorted(a)   # 返回新列表，原列表不变
a.index(2)      # 返回第一个 2 的下标
a.count(1)      # 统计 1 的个数
```

`sort()` 和 `sorted()` 都能用 `key=` 指定排序依据。""",
    },
    {
        "title": "dict 的 get 与 in",
        "category": "容器与字符串",
        "summary": "直接 d[key] 找不到会 KeyError，get 可以给默认值。",
        "tags": "dict,哈希",
        "content": """```python
cnt = {}
cnt[x] = cnt.get(x, 0) + 1   # 计数标准写法

if x in cnt:                 # 判断键是否存在
    ...
```

遍历时用 `for k, v in cnt.items()`，只遍历键用 `for k in cnt`。""",
    },
    {
        "title": "字符串切片与常用方法",
        "category": "容器与字符串",
        "summary": "s[::-1] 反转，split/join 处理行，strip 去首尾空白。",
        "tags": "字符串,切片",
        "content": """```python
s = "  Hello World  "
s.strip()        # "Hello World"
s.lower()        # 统一小写
s.split()        # ['Hello', 'World']
"-".join(["a", "b"])  # "a-b"
s[::-1]          # 反转字符串
```

切片 `s[start:stop:step]` 同样是左闭右开，越界不会报错，会自动截断。""",
    },
    {
        "title": "set 去重与集合运算",
        "category": "容器与字符串",
        "summary": "去重、判断是否存在、交并差，平均 O(1)。",
        "tags": "set,去重",
        "content": """```python
a = {1, 2, 3}
b = {2, 3, 4}
a & b   # 交集 {2, 3}
a | b   # 并集 {1, 2, 3, 4}
a - b   # 差集 {1}
```

`in` 判断用 set 比 list 快很多，需要频繁「是否存在」时先转成 set。""",
    },
    {
        "title": "enumerate 与 zip",
        "category": "容器与字符串",
        "summary": "同时拿到下标和值；同时遍历两个列表。",
        "tags": "enumerate,zip",
        "content": """```python
for i, x in enumerate(nums):      # i 从 0 开始
    print(i, x)

for i, x in enumerate(nums, 1):   # i 从 1 开始
    print(i, x)

for a, b in zip(list1, list2):
    print(a, b)
```

题目要求输出「从 1 开始的下标」时，`enumerate(nums, 1)` 能少写一次 +1。""",
    },
    {
        "title": "输入读取的两种套路",
        "category": "常用技巧",
        "summary": "少量输入用 input()，多行大量数字用 sys.stdin.read()。",
        "tags": "输入,io",
        "content": """```python
# 方式一：按行读，逻辑最清晰
n = int(input())
a = list(map(int, input().split()))

# 方式二：一次性读完，适合行数不固定的题
import sys
data = sys.stdin.read().split()
n = int(data[0])
a = list(map(int, data[1:1 + n]))
```

方式二不要混用 `input()`，否则会读乱顺序。""",
    },
    {
        "title": "输出格式：小数与 f-string",
        "category": "常用技巧",
        "summary": "保留两位小数用 f\"{x:.2f}\"，别用 round 硬凑。",
        "tags": "输出,格式化",
        "content": """```python
avg = sum(nums) / len(nums)
print(f"{avg:.2f}")       # 保留两位小数
print(f"{x:>5}")          # 右对齐占 5 位
print(f"{x:05d}")         # 补零到 5 位
```

评测逐行比对，多一个空格都可能判 WA，写完先拿样例自测一遍。""",
    },
    {
        "title": "排序 key 与多关键字",
        "category": "常用技巧",
        "summary": "key 接收一个函数，返回排序依据。",
        "tags": "排序,key",
        "content": """```python
students = [("张三", 90), ("李四", 85)]
students.sort(key=lambda s: s[1])            # 按分数升序
students.sort(key=lambda s: (-s[1], s[0]))   # 分数降序，同分按名字升序
```

元组本身也可以直接排序：`sorted(segs)` 会先比第一项再比第二项。""",
    },
    {
        "title": "双指针一遍扫完",
        "category": "常用技巧",
        "summary": "左右指针相向、快慢指针同向，常用于回文、去重、区间。",
        "tags": "双指针",
        "content": """```python
def is_palindrome(s):
    i, j = 0, len(s) - 1
    while i < j:
        if s[i] != s[j]:
            return False
        i += 1
        j -= 1
    return True
```

双指针能把 O(n²) 的枚举优化到 O(n)，前提是数据有单调性。""",
    },
    {
        "title": "二分查找模板（找第一个 ≥ x 的位置）",
        "category": "算法套路",
        "summary": "while lo <= hi，收缩边界时不要丢答案。",
        "tags": "二分",
        "content": """```python
def lower_bound(a, x):
    lo, hi = 0, len(a) - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] >= x:
            if a[mid] == x:
                ans = mid
            hi = mid - 1   # 继续往左找第一次出现
        else:
            lo = mid + 1
    return ans
```

题目要求「第一个位置」时，找到后不要立刻 return，要继续收缩左边界。""",
    },
    {
        "title": "二分答案：把最优化变成判定",
        "category": "算法套路",
        "summary": "答案单调时，枚举答案换成二分答案。",
        "tags": "二分,答案",
        "content": """```python
lo, hi, ans = 0, max(h), 0
while lo <= hi:
    mid = (lo + hi) // 2
    if check(mid):     # mid 可行 → 尝试更大的
        ans = mid
        lo = mid + 1
    else:
        hi = mid - 1
print(ans)
```

关键是想清楚：`check(mid)` 为真时，答案在左半边还是右半边。""",
    },
    {
        "title": "递归三要素与记忆化",
        "category": "算法套路",
        "summary": "出口、递推式、等价子问题；重复计算就加缓存。",
        "tags": "递归,记忆化",
        "content": """```python
from functools import lru_cache

@lru_cache(maxsize=None)
def f(n):
    if n <= 2:      # 1. 出口
        return 1
    return f(n - 1) + f(n - 2)   # 2. 递推式
```

朴素递归算 F(40) 要上亿次调用，加一行缓存就能秒过；或者干脆改成从下往上递推。""",
    },
    {
        "title": "栈处理括号匹配",
        "category": "算法套路",
        "summary": "左括号入栈，右括号与栈顶比对。",
        "tags": "栈",
        "content": """```python
pairs = {")": "(", "]": "[", "}": "{"}
stack = []
for ch in s:
    if ch in "([{":
        stack.append(ch)
    elif ch in pairs:
        if not stack or stack[-1] != pairs[ch]:
            print("NO"); break
        stack.pop()
else:
    print("YES" if not stack else "NO")
```

别忘了两个边界：右括号来时栈为空、扫完后栈不空。""",
    },
    {
        "title": "差一错误：下标与长度",
        "category": "易错点",
        "summary": "长度为 n 的列表，合法下标是 0 到 n-1。",
        "tags": "越界,索引",
        "content": """```python
a = [10, 20, 30]     # len(a) == 3
a[0]  a[2]           # 合法
a[3]                 # IndexError
```

写循环时优先用 `for x in a` 或 `for i in range(len(a))`，
输出「第几个」时再决定要不要 +1，别一边写一边加。""",
    },
    {
        "title": "整除与负数取模",
        "category": "易错点",
        "summary": "// 是向下取整，% 的符号跟除数一致。",
        "tags": "整除,取模",
        "content": """```python
7 // 2    # 3
-7 // 2   # -4（不是 -3）
-7 % 2    # 1 （不是 -1）
```

除法想保留小数用 `/`，想整除用 `//`，求余用 `%`；
判断奇偶时 `x % 2 == 1` 对负数不成立，建议写 `x % 2 != 0`。""",
    },
    {
        "title": "死循环与 EOFError",
        "category": "易错点",
        "summary": "while 条件不变、input 读多了，是最常见的两种崩溃。",
        "tags": "死循环,输入",
        "content": """TLE 多半是下面两种情况：

```python
while n != 1:      # n 永远不变 → 死循环
    pass

n = int(input())
b = int(input())   # 只有一行输入 → EOFError
```

自查方法：把样例粘进本地运行，看程序是卡住还是报错；
读多行输入时用 `sys.stdin.read().split()` 更省心。""",
    },
]
