"""内置题库（一期 16 题：入门 8 题 + 基础 8 题）。

reference 字段只在开发期用来校验测试数据，不会写入数据库、也不会展示给用户。
运行 tools/verify_seed.py 可以自动检查每题参考解的输出与预期答案是否一致。
"""

PROBLEMS = [
    {
        "title": "两数之和",
        "difficulty": "入门",
        "tags": "哈希,枚举",
        "description": """给定 n 个整数和一个目标值 t，请在数组中找出两个数，使它们的和等于 t。

题目保证恰好存在一组解，且同一个位置不能使用两次。

输入格式：
第一行两个整数 n 和 t。
第二行 n 个整数，用空格分隔。

输出格式：
输出两个下标（从 1 开始计数，较小的下标在前），中间用一个空格分隔。""",
        "hint": """① 最直接的做法是两重循环把每对数都试一遍，复杂度 O(n²)，n 稍大就会超时。
② 换个角度想：遍历到 x 时，其实只需要知道"前面是否出现过 t-x"。
③ 用一个字典把"数值 → 下标"存起来，遍历一次即可，复杂度 O(n)。""",
        "tests": [
            {"input": "5 9\n2 7 11 15 1\n", "output": "1 2\n"},
            {"input": "4 6\n3 3 4 5\n", "output": "1 2\n"},
            {"input": "6 10\n1 2 8 2 9 3\n", "output": "2 3\n"},
            {"input": "3 -1\n5 -6 4\n", "output": "1 2\n"},
        ],
        "reference": """n, t = map(int, input().split())
nums = list(map(int, input().split()))
seen = {}
for i, x in enumerate(nums):
    if t - x in seen:
        print(seen[t - x] + 1, i + 1)
        break
    seen[x] = i
""",
    },
    {
        "title": "判断素数",
        "difficulty": "入门",
        "tags": "枚举,数学",
        "description": """输入 T 个整数，请逐个判断它们是否为素数（质数）。

素数的定义：大于 1 且只能被 1 和自身整除的整数。注意 1 不是素数。

输入格式：
第一行一个整数 T（1 ≤ T ≤ 100）。
接下来 T 行，每行一个整数 n（1 ≤ n ≤ 10^9）。

输出格式：
对每个 n 输出一行：是素数输出 YES，否则输出 NO。""",
        "hint": """① 从 2 开始试除到 n-1 是最朴素的写法，但 n 最大到 10^9，会超时。
② 只需要试除到 √n：如果 n 有因数，那么一定有一个不超过 √n。
③ 再加一条优化：先排除偶数，然后只试奇数，循环次数还能少一半。""",
        "tests": [
            {"input": "3\n2\n9\n97\n", "output": "YES\nNO\nYES\n"},
            {"input": "2\n1\n1000000007\n", "output": "NO\nYES\n"},
            {"input": "4\n4\n5\n999983\n1000000\n", "output": "NO\nYES\nYES\nNO\n"},
        ],
        "reference": """import sys


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


data = sys.stdin.read().split()
t = int(data[0])
ans = []
for k in range(1, t + 1):
    ans.append("YES" if is_prime(int(data[k])) else "NO")
print("\\n".join(ans))
""",
    },
    {
        "title": "回文字符串",
        "difficulty": "入门",
        "tags": "字符串,模拟",
        "description": """给定一个由字母和数字组成的字符串 s，请判断它是否为回文串。

判断时忽略字母的大小写，例如 "Level" 是回文串。

输入格式：
一行，一个字符串 s（1 ≤ 长度 ≤ 1000）。

输出格式：
是回文串输出 YES，否则输出 NO。""",
        "hint": """① 回文串正着读和反着读是一样的，可以先把字符串统一转成小写。
② Python 的切片 s[::-1] 能直接得到反转后的字符串，比较一下即可。
③ 也可以练习双指针：一个从头部走、一个从尾部走，相遇即说明是回文。""",
        "tests": [
            {"input": "Level\n", "output": "YES\n"},
            {"input": "hello\n", "output": "NO\n"},
            {"input": "abc1cba\n", "output": "YES\n"},
            {"input": "AbBa\n", "output": "YES\n"},
            {"input": "a\n", "output": "YES\n"},
        ],
        "reference": """s = input().strip().lower()
print("YES" if s == s[::-1] else "NO")
""",
    },
    {
        "title": "斐波那契数列",
        "difficulty": "入门",
        "tags": "递归,数学",
        "description": """斐波那契数列的定义为：

- F(1) = 1
- F(2) = 1
- 当 n > 2 时，F(n) = F(n-1) + F(n-2)

给定 n，请输出 F(n)。

输入格式：
一行，一个整数 n（1 ≤ n ≤ 40）。

输出格式：
一行，一个整数，表示 F(n)。""",
        "hint": """① 用递归写最贴近定义，但 F(40) 会重复计算上亿次，程序会超时。
② 换一种思路：从小到大依次算出每一项，只保留前两项，复杂度 O(n)。
③ 这也是"记忆化搜索 / 动态规划"的入门例子：把算过的结果存下来，别重复算。""",
        "tests": [
            {"input": "1\n", "output": "1\n"},
            {"input": "2\n", "output": "1\n"},
            {"input": "10\n", "output": "55\n"},
            {"input": "40\n", "output": "102334155\n"},
        ],
        "reference": """n = int(input())
a, b = 1, 1
for _ in range(3, n + 1):
    a, b = b, a + b
print(a if n <= 2 else b)
""",
    },
    {
        "title": "字符出现次数统计",
        "difficulty": "入门",
        "tags": "哈希,字符串",
        "description": """给定一个只包含小写字母的字符串 s，请统计出现次数最多的字符。

如果出现次数最多的字符不止一个，请输出其中字典序最小的那个。

输入格式：
一行，一个字符串 s（1 ≤ 长度 ≤ 10000）。

输出格式：
一行，输出"字符 次数"，中间用一个空格分隔。""",
        "hint": """① 依次遍历字符串，用一个字典记录每个字符出现了多少次。
② 统计完成后需要找最大值，同时处理"次数相同取字典序更小"的情况。
③ 可以遍历 a 到 z 这 26 个字母，这样天然按字典序比较。""",
        "tests": [
            {"input": "aabbbcc\n", "output": "b 3\n"},
            {"input": "abcabc\n", "output": "a 2\n"},
            {"input": "zzzz\n", "output": "z 4\n"},
            {"input": "leetcode\n", "output": "e 3\n"},
        ],
        "reference": """s = input().strip()
cnt = {}
for ch in s:
    cnt[ch] = cnt.get(ch, 0) + 1
best_ch, best_cnt = "", -1
for ch in sorted(cnt):
    if cnt[ch] > best_cnt:
        best_ch, best_cnt = ch, cnt[ch]
print(best_ch, best_cnt)
""",
    },
    {
        "title": "最大值与它的位置",
        "difficulty": "入门",
        "tags": "模拟,枚举",
        "description": """给定 n 个整数，请找出其中的最大值，以及这个最大值第一次出现的位置。

位置从 1 开始计数。

输入格式：
第一行一个整数 n（1 ≤ n ≤ 1000）。
第二行 n 个整数，用空格分隔（-10^9 ≤ 每个整数 ≤ 10^9）。

输出格式：
一行，输出最大值和它第一次出现的位置，中间用一个空格分隔。""",
        "hint": """① 先假设第一个数就是最大值，然后从第二个数开始逐个比较。
② 注意题目要求"第一次出现"的位置，所以遇到相等时不要更新下标。
③ 初始最大值不要写成 0，否则全是负数时会出错。""",
        "tests": [
            {"input": "5\n3 9 2 9 1\n", "output": "9 2\n"},
            {"input": "3\n-5 -1 -3\n", "output": "-1 2\n"},
            {"input": "1\n7\n", "output": "7 1\n"},
            {"input": "4\n5 5 5 5\n", "output": "5 1\n"},
        ],
        "reference": """n = int(input())
nums = list(map(int, input().split()))
best = nums[0]
pos = 1
for i in range(1, n):
    if nums[i] > best:
        best = nums[i]
        pos = i + 1
print(best, pos)
""",
    },
    {
        "title": "凯撒密码",
        "difficulty": "入门",
        "tags": "字符串,模拟",
        "description": """凯撒密码的加密方式：把每个小写字母向后移动 3 位。

例如 a → d、x → a、z → c。字符串中的其它字符（大写字母、数字、空格、标点）保持原样。

输入格式：
一行，一个字符串 s（1 ≤ 长度 ≤ 1000，可能包含空格）。

输出格式：
一行，输出加密后的字符串。""",
        "hint": """① 字母在计算机里是用编码（ord）表示的，a 的编码是 97。
② 把字母换算成 0～25 的数字：ord(ch) - ord('a')，加 3 再对 26 取余即可循环。
③ 再转换回字符：chr(数字 + ord('a'))；非小写字母直接原样拼接。""",
        "tests": [
            {"input": "abc\n", "output": "def\n"},
            {"input": "xyz\n", "output": "abc\n"},
            {"input": "hello, world\n", "output": "khoor, zruog\n"},
            {"input": "abz\n", "output": "dec\n"},
        ],
        "reference": """s = input()
out = []
for ch in s:
    if "a" <= ch <= "z":
        out.append(chr((ord(ch) - ord("a") + 3) % 26 + ord("a")))
    else:
        out.append(ch)
print("".join(out))
""",
    },
    {
        "title": "求阶乘",
        "difficulty": "入门",
        "tags": "递归,数学",
        "description": """给定正整数 n，请计算 n! = 1 × 2 × 3 × … × n。

输入格式：
一行，一个整数 n（1 ≤ n ≤ 20）。

输出格式：
一行，一个整数，表示 n! 的结果。

提示：Python 的整数没有上限，不需要考虑溢出问题，但要保证算法本身正确。""",
        "hint": """① 既可以用循环从 1 累乘到 n，也可以用递归实现 fact(n) = n × fact(n-1)。
② 递归一定要写出口：n == 1 时返回 1，否则会无限递归。
③ 想一想：为什么这道题 n 只有 20？因为 20! 已经是 19 位数字了。""",
        "tests": [
            {"input": "5\n", "output": "120\n"},
            {"input": "1\n", "output": "1\n"},
            {"input": "10\n", "output": "3628800\n"},
            {"input": "20\n", "output": "2432902008176640000\n"},
        ],
        "reference": """n = int(input())
ans = 1
for i in range(1, n + 1):
    ans *= i
print(ans)
""",
    },
    {
        "title": "二分查找",
        "difficulty": "基础",
        "tags": "二分",
        "description": """给定一个长度为 n 的升序整数序列，以及 q 次询问，每次询问一个整数 x。

请回答 x 在序列中第一次出现的位置（从 1 开始）；如果 x 不存在，输出 -1。

输入格式：
第一行两个整数 n 和 q（1 ≤ n, q ≤ 10^5）。
第二行 n 个升序排列的整数，用空格分隔。
接下来 q 行，每行一个整数 x。

输出格式：
共 q 行，每行一个整数，表示答案。""",
        "hint": """① 从头到尾扫描每次询问最快也要 O(n)，q 次就是 O(nq)，会超时。
② 序列是升序的，可以用二分法在 O(log n) 时间内定位 x。
③ 题目要求"第一次出现"，所以找到 x 之后还要继续往左收缩边界，而不是直接返回。""",
        "tests": [
            {"input": "5 3\n1 3 5 7 9\n3\n8\n9\n", "output": "2\n-1\n5\n"},
            {"input": "1 2\n42\n42\n0\n", "output": "1\n-1\n"},
            {"input": "6 2\n1 1 2 2 3 3\n2\n4\n", "output": "3\n-1\n"},
            {"input": "8 4\n-5 -1 0 3 3 7 9 9\n-5\n3\n9\n2\n", "output": "1\n4\n7\n-1\n"},
        ],
        "reference": """import sys

data = sys.stdin.read().split()
it = iter(data)
n = int(next(it))
q = int(next(it))
a = [int(next(it)) for _ in range(n)]
out = []
for _ in range(q):
    x = int(next(it))
    lo, hi = 0, n - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] >= x:
            if a[mid] == x:
                ans = mid + 1
            hi = mid - 1
        else:
            lo = mid + 1
    out.append(str(ans))
print("\\n".join(out))
""",
    },
    {
        "title": "第 k 小的数",
        "difficulty": "基础",
        "tags": "排序",
        "description": """给定 n 个整数（可能有重复），请输出其中第 k 小的数。

例如数组 [3, 1, 4, 1, 5] 中，第 3 小的数是 3（排序后为 1, 1, 3, 4, 5）。

输入格式：
第一行两个整数 n 和 k（1 ≤ k ≤ n ≤ 10^5）。
第二行 n 个整数，用空格分隔。

输出格式：
一行，一个整数，表示第 k 小的数。""",
        "hint": """① 最简单的做法是直接排序，然后取下标 k-1 的元素，复杂度 O(n log n)。
② 注意"第 k 小"是从 1 开始数的，数组下标却从 0 开始，别差一位。
③ 进阶：可以用快速选择（quickselect）把复杂度降到平均 O(n)，感兴趣可以试试。""",
        "tests": [
            {"input": "5 3\n3 1 4 1 5\n", "output": "3\n"},
            {"input": "4 1\n9 -2 7 7\n", "output": "-2\n"},
            {"input": "3 3\n2 2 2\n", "output": "2\n"},
            {"input": "6 5\n10 9 8 7 6 5\n", "output": "9\n"},
        ],
        "reference": """import sys

data = sys.stdin.read().split()
n = int(data[0])
k = int(data[1])
a = [int(x) for x in data[2:2 + n]]
a.sort()
print(a[k - 1])
""",
    },
    {
        "title": "括号匹配",
        "difficulty": "基础",
        "tags": "栈,字符串",
        "description": """给定一个只由圆括号、方括号、花括号组成的字符串，判断其中的括号是否配对。

配对规则：每个左括号必须有相同类型的右括号与之匹配，且不能交叉嵌套。

输入格式：
一行，一个括号字符串 s（1 ≤ 长度 ≤ 10^5）。

输出格式：
配对输出 YES，否则输出 NO。""",
        "hint": """① 从左往右读，遇到左括号就先"记下来"，遇到右括号时要和最近一个左括号比较。
② "最近一个"正好是后进先出，所以用栈（Python 里用 list 的 append / pop 即可）。
③ 别忘了两种情况：右括号来时栈是空的；以及读完后栈里还有剩余的左括号。""",
        "tests": [
            {"input": "()[]{}\n", "output": "YES\n"},
            {"input": "(]\n", "output": "NO\n"},
            {"input": "([{}])\n", "output": "YES\n"},
            {"input": "(((\n", "output": "NO\n"},
            {"input": "]\n", "output": "NO\n"},
            {"input": ")(", "output": "NO\n"},
            {"input": "([)]\n", "output": "NO\n"},
            {"input": "({[]})\n", "output": "YES\n"},
        ],
        "reference": """s = input().strip()
pairs = {")": "(", "]": "[", "}": "{"}
stack = []
ok = True
for ch in s:
    if ch in "([{":
        stack.append(ch)
    elif ch in pairs:
        if not stack or stack[-1] != pairs[ch]:
            ok = False
            break
        stack.pop()
if stack:
    ok = False
print("YES" if ok else "NO")
""",
    },
    {
        "title": "区间合并",
        "difficulty": "基础",
        "tags": "排序,模拟",
        "description": """给定 n 个闭区间 [l, r]，请把有重叠或首尾相接的区间合并成一个。

例如 [1, 2] 和 [3, 4] 首尾相接（2 与 3 相邻），需要合并为 [1, 4]。

输入格式：
第一行一个整数 n（1 ≤ n ≤ 10^5）。
接下来 n 行，每行两个整数 l 和 r（0 ≤ l ≤ r ≤ 10^9）。

输出格式：
按起点从小到大输出合并后的区间，每行一个"l r"。""",
        "hint": """① 如果区间是乱序的，合并时会来回判断，非常麻烦。先把区间按左端点排序。
② 排序后依次处理：当前区间与已合并的最后一个区间比较，能接上就扩展右端点。
③ "能接上"的条件是 l ≤ 最后一个区间的右端点 + 1（题目把首尾相接也算合并）。""",
        "tests": [
            {"input": "3\n1 3\n2 6\n8 10\n", "output": "1 6\n8 10\n"},
            {"input": "2\n5 5\n5 5\n", "output": "5 5\n"},
            {"input": "1\n0 0\n", "output": "0 0\n"},
            {"input": "4\n1 2\n3 4\n2 3\n10 20\n", "output": "1 4\n10 20\n"},
            {"input": "3\n10 12\n1 4\n3 8\n", "output": "1 8\n10 12\n"},
        ],
        "reference": """n = int(input())
segs = []
for _ in range(n):
    l, r = map(int, input().split())
    segs.append([l, r])
segs.sort()
merged = []
for l, r in segs:
    if merged and l <= merged[-1][1] + 1:
        if r > merged[-1][1]:
            merged[-1][1] = r
    else:
        merged.append([l, r])
print("\\n".join(f"{a} {b}" for a, b in merged))
""",
    },
    {
        "title": "阶乘末尾零的个数",
        "difficulty": "基础",
        "tags": "数学,模拟",
        "description": """给定 n，请计算 n! 末尾有多少个连续的 0。

输入格式：
一行，一个整数 n（1 ≤ n ≤ 10^9）。

输出格式：
一行，一个整数，表示末尾连续 0 的个数。

说明：n 很大，直接计算 n! 再数 0 会非常慢，需要想数学方法。""",
        "hint": """① 末尾的 0 来自因子 10，而 10 = 2 × 5；阶乘中因子 2 远多于因子 5，所以关键看 5 的个数。
② 1～n 中 5 的倍数贡献 1 个 5，25 的倍数再多贡献 1 个，125 的倍数再再多 1 个……
③ 所以答案等于 n//5 + n//25 + n//125 + …，一直加到商为 0 为止。""",
        "tests": [
            {"input": "5\n", "output": "1\n"},
            {"input": "10\n", "output": "2\n"},
            {"input": "25\n", "output": "6\n"},
            {"input": "1000000000\n", "output": "249999998\n"},
        ],
        "reference": """n = int(input())
ans = 0
power = 5
while power <= n:
    ans += n // power
    power *= 5
print(ans)
""",
    },
    {
        "title": "爬楼梯",
        "difficulty": "基础",
        "tags": "递归,数学",
        "description": """有一个 n 级台阶的楼梯，每次可以走 1 级或 2 级。

问：走完 n 级台阶一共有多少种不同的走法？

输入格式：
一行，一个整数 n（1 ≤ n ≤ 45）。

输出格式：
一行，一个整数，表示走法总数。""",
        "hint": """① 最后一步只有两种可能：从 n-1 级走 1 级上来，或者从 n-2 级走 2 级上来。
② 于是 f(n) = f(n-1) + f(n-2)，这就是斐波那契式的递推关系。
③ 直接递归会重复计算大量子问题（n=45 时几乎跑不完），改成一维递推即可。""",
        "tests": [
            {"input": "1\n", "output": "1\n"},
            {"input": "2\n", "output": "2\n"},
            {"input": "3\n", "output": "3\n"},
            {"input": "45\n", "output": "1836311903\n"},
        ],
        "reference": """n = int(input())
a, b = 1, 2
if n == 1:
    print(1)
elif n == 2:
    print(2)
else:
    for _ in range(3, n + 1):
        a, b = b, a + b
    print(b)
""",
    },
    {
        "title": "日期差",
        "difficulty": "基础",
        "tags": "模拟,数学",
        "description": """给定两个日期（格式 YYYY-MM-DD），请计算它们之间相差多少天（取绝对值）。

日期范围为 1900-01-01 到 2100-12-31，保证输入合法。

输入格式：
第一行一个日期，第二行一个日期。

输出格式：
一行，一个整数，表示相差的天数。

说明：需要注意闰年的规则——能被 4 整除但不能被 100 整除，或者能被 400 整除的年份是闰年。""",
        "hint": """① 直接数天数容易漏掉闰年，可以换个思路：把日期换算成"从某个基准日起的第几天"。
② 想清楚每个月有多少天：2 月平年 28 天、闰年 29 天，可以写成一张表。
③ Python 标准库 datetime 也能直接算，但自测时建议先手写一遍，理解闰年逻辑。""",
        "tests": [
            {"input": "2024-01-01\n2024-01-31\n", "output": "30\n"},
            {"input": "2023-12-31\n2024-01-01\n", "output": "1\n"},
            {"input": "2023-02-28\n2023-03-01\n", "output": "1\n"},
            {"input": "2020-02-28\n2020-03-01\n", "output": "2\n"},
            {"input": "2024-03-01\n2024-02-28\n", "output": "2\n"},
        ],
        "reference": """from datetime import date

a = input().strip()
b = input().strip()
y1, m1, d1 = map(int, a.split("-"))
y2, m2, d2 = map(int, b.split("-"))
print(abs((date(y2, m2, d2) - date(y1, m1, d1)).days))
""",
    },
    {
        "title": "砍树（二分答案）",
        "difficulty": "基础",
        "tags": "二分,贪心",
        "description": """有 n 棵树排成一排，第 i 棵树的高度是 h[i]。

伐木工把锯片设置在高度 H（整数），所有高于 H 的树都会被锯掉顶端，得到长度为 h[i] - H 的木材；
高度不超过 H 的树不产生木材。

现在需要至少 m 单位长度的木材，请找出最大的可行高度 H。

输入格式：
第一行两个整数 n 和 m（1 ≤ n ≤ 10^6，1 ≤ m ≤ 2×10^9）。
第二行 n 个整数，表示每棵树的高度 h[i]（0 ≤ h[i] ≤ 10^9）。

输出格式：
一行，一个整数，表示最大的可行高度 H。

说明：题目保证至少存在 H = 0 能满足需求。""",
        "hint": """① 暴力从高到低尝试 H 太慢，但可以观察到：H 越小，得到的木材越多，答案具有单调性。
② 单调性提示我们用二分：若 H 可行，则所有小于 H 的高度都可行，答案在右半边。
③ 注意本题数值很大（m 可达 2×10^9），累加时用 Python 整数即可，不用担心溢出。""",
        "tests": [
            {"input": "4 7\n20 15 10 17\n", "output": "15\n"},
            {"input": "5 20\n4 42 40 26 46\n", "output": "36\n"},
            {"input": "1 1\n10\n", "output": "9\n"},
            {"input": "3 3\n1 2 3\n", "output": "1\n"},
        ],
        "reference": """n, m = map(int, input().split())
h = list(map(int, input().split()))
lo, hi = 0, max(h)
ans = 0
while lo <= hi:
    mid = (lo + hi) // 2
    total = 0
    for x in h:
        if x > mid:
            total += x - mid
    if total >= m:
        ans = mid
        lo = mid + 1
    else:
        hi = mid - 1
print(ans)
""",
    },
]
