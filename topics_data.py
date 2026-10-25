"""专题训练套题配置：按标签把题目编成有顺序的训练组。

题目用标题关联（seed 时按 title 查 problem.id），改名题目前记得同步这里。
"""

TOPICS = [
    {
        "name": "哈希表入门",
        "slug": "hash",
        "icon": "🗂️",
        "description": "用字典把「查找」从 O(n) 降到 O(1)，这是新手最先该掌握的加速技巧。",
        "problems": ["两数之和", "字符出现次数统计"],
    },
    {
        "name": "字符串处理",
        "slug": "string",
        "icon": "🔤",
        "description": "遍历、切片、编码转换，蓝桥杯 Python 组的高频送分题。",
        "problems": ["回文字符串", "凯撒密码"],
    },
    {
        "name": "数组与模拟",
        "slug": "array",
        "icon": "📋",
        "description": "照着题意一步步算，重点是把边界和计数写对。",
        "problems": ["最大值与它的位置", "日期差"],
    },
    {
        "name": "递归与递推",
        "slug": "recursion",
        "icon": "🌀",
        "description": "从定义出发把大问题拆小，再学会用递推避免重复计算。",
        "problems": ["斐波那契数列", "求阶乘", "爬楼梯"],
    },
    {
        "name": "排序与区间",
        "slug": "sorting",
        "icon": "📊",
        "description": "先排序再处理，很多看似复杂的问题会瞬间变简单。",
        "problems": ["第 k 小的数", "区间合并"],
    },
    {
        "name": "二分专题",
        "slug": "binary-search",
        "icon": "🔍",
        "description": "从「有序数组里找数」到「二分答案」，这是基础题的性价比之王。",
        "problems": ["二分查找", "砍树（二分答案）"],
    },
    {
        "name": "数学与枚举",
        "slug": "math",
        "icon": "🧮",
        "description": "试除法、因数分解、找规律，考的是观察力而不是代码量。",
        "problems": ["判断素数", "阶乘末尾零的个数"],
    },
    {
        "name": "栈的应用",
        "slug": "stack",
        "icon": "🧱",
        "description": "后进先出，专门对付括号、嵌套和「最近匹配」类问题。",
        "problems": ["括号匹配"],
    },
]
