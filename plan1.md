

# 优化后的组织树与规则

---

## 一、6条组织规则（优化版）

### 规则1：系统角色只保留3个

```
管理员
老师
学生
```

角色只管系统功能权限（比如谁能建表、谁能看后台），不参与审批选人。

---

### 规则2：审批选人按"部门 + 岗位"

```
部门 → 决定在哪个组织范围找人
岗位 → 决定找这个范围里的谁
```

不用角色来决定审批人。

---

### 规则3：部门关系只有父子

```
合法：学校 → 计算机学院 → 软件工程系 → 教研室（纵向父子链）
不存在：教务处 和 财务处 之间的上下级关系（横向并列）
```

每个部门只有一个 parent_id 指向上级，构成一棵树。

---

### 规则4：岗位只在本部门内部有意义

```
合法：财务处内部的 处长 > 副处长 > 会计
不存在：财务处会计 > 教务处专员（跨部门岗位关系）
```

---

### 规则5：每个部门必须标记一个主负责人岗位

```
计算机学院 → 主负责人岗位：院长
财务处     → 主负责人岗位：处长
学工办公室 → 主负责人岗位：主任
教研室     → 主负责人岗位：教研室主任
```

在数据层面用 is_head 标记，不靠人工约定。

---

### 规则6：校级领导不参与自动上溯

```
校长、党委书记、副校长这些岗位：
  ✓ 可以在流程里用 FIXED 模式显式指定
  ✗ 不会被 ORG_CHAIN_UP 自动匹配到
```

实现方式：ORG_CHAIN_UP 向上找到根部门（学校）时就停下来，不进入根部门查岗位。

---

### 规则7（新增）：需要被上溯匹配的岗位，必须挂在链路部门上

```
辅导员日常行政归学工办公室管，但岗位关系要挂到学院一级。
教学秘书日常行政归教学办公室管，但岗位关系也挂到学院一级。

原因：
  学生挂在学院或系 → ORG_CHAIN_UP 沿父子链往上找 → 只经过系、学院、学校
  学工办公室是学院的子部门，在链路的旁支上，ORG_CHAIN_UP 不会横向钻进去
  如果辅导员岗位挂在学工办公室 → 永远找不到

所以：谁需要被上溯找到，谁的岗位就往链路上挂
```

---

## 二、优化后的组织树

和你原来的树比，部门结构完全不变，变的是**哪些岗位挂在哪个层级**。

下面用 `[链路岗位]` 标记那些为了上溯匹配而挂到上级部门的岗位，用 `[主负责人]` 标记每个部门的主负责人。

```
学校【根部门，is_root = true】
│
├─ 校级岗位【挂在根部门下，仅限 FIXED 模式显式指定】
│   ├─ 党委书记
│   ├─ 校长
│   └─ 副校长
│
├─ 党政办公室
│   ├─ 主任 [主负责人]
│   ├─ 副主任
│   └─ 秘书
│
├─ 教务处
│   ├─ 处长 [主负责人]
│   ├─ 副处长
│   └─ 教务专员
│
├─ 学生工作处
│   ├─ 处长 [主负责人]
│   ├─ 副处长
│   └─ 学生管理专员
│
├─ 人事处
│   ├─ 处长 [主负责人]
│   ├─ 副处长
│   └─ 人事专员
│
├─ 财务处
│   ├─ 处长 [主负责人]
│   ├─ 副处长
│   ├─ 会计
│   └─ 出纳
│
├─ 资产后勤处
│   ├─ 处长 [主负责人]
│   ├─ 副处长
│   ├─ 采购专员
│   └─ 后勤专员
│
├─ 信息化中心
│   ├─ 主任 [主负责人]
│   ├─ 副主任
│   ├─ 系统管理员
│   └─ 运维工程师
│
├─ 计算机学院
│   ├─ 院长 [主负责人]
│   ├─ 书记
│   ├─ 副院长
│   ├─ 副书记
│   ├─ 辅导员 [链路岗位，人在学工办公室工作，但岗位挂在学院级别]
│   ├─ 教学秘书 [链路岗位，人在教学办公室工作，但岗位挂在学院级别]
│   │
│   ├─ 学院办公室
│   │   ├─ 主任 [主负责人]
│   │   └─ 行政秘书
│   │
│   ├─ 教学办公室
│   │   └─ 主任 [主负责人]
│   │       （教学秘书的岗位关系已挂到学院级别，此处不再挂）
│   │
│   ├─ 学工办公室
│   │   └─ 主任 [主负责人]
│   │       （辅导员的岗位关系已挂到学院级别，此处不再挂）
│   │
│   ├─ 软件工程系
│   │   ├─ 系主任 [主负责人]
│   │   └─ 软件工程教研室
│   │       ├─ 教研室主任 [主负责人]
│   │       └─ 专任教师
│   │
│   └─ 实验中心
│       ├─ 主任 [主负责人]
│       └─ 实验员
│
└─ 艺术学院
    ├─ 院长 [主负责人]
    ├─ 书记
    ├─ 副院长
    ├─ 副书记
    ├─ 辅导员 [链路岗位]
    ├─ 教学秘书 [链路岗位]
    │
    ├─ 学院办公室
    │   ├─ 主任 [主负责人]
    │   └─ 行政秘书
    │
    ├─ 教学办公室
    │   └─ 主任 [主负责人]
    │
    ├─ 学工办公室
    │   └─ 主任 [主负责人]
    │
    ├─ 视觉传达系
    │   ├─ 系主任 [主负责人]
    │   └─ 视觉传达教研室
    │       ├─ 教研室主任 [主负责人]
    │       └─ 专任教师
    │
    └─ 实训中心
        ├─ 主任 [主负责人]
        └─ 实训教师
```

---

## 三、数据库怎么存

### 部门表 department

```
id            部门ID
name          部门名称
parent_id     上级部门ID（根部门的parent_id为null）
is_root       是否是根部门（只有"学校"这一条为true）
sort_order    排序
```

示例数据：

```
id=1   name=学校           parent_id=null  is_root=true
id=10  name=财务处          parent_id=1     is_root=false
id=20  name=计算机学院      parent_id=1     is_root=false
id=21  name=学院办公室      parent_id=20    is_root=false
id=22  name=教学办公室      parent_id=20    is_root=false
id=23  name=学工办公室      parent_id=20    is_root=false
id=24  name=软件工程系      parent_id=20    is_root=false
id=25  name=软件工程教研室  parent_id=24    is_root=false
id=26  name=实验中心        parent_id=20    is_root=false
id=30  name=艺术学院        parent_id=1     is_root=false
...
```

### 岗位表 post

```
id            岗位ID
name          岗位名称
```

示例数据：

```
id=1   name=校长
id=2   name=党委书记
id=3   name=副校长
id=10  name=院长
id=11  name=书记
id=12  name=副院长
id=13  name=副书记
id=14  name=辅导员
id=15  name=教学秘书
id=16  name=系主任
id=17  name=教研室主任
id=18  name=专任教师
id=20  name=处长
id=21  name=副处长
id=22  name=会计
id=23  name=出纳
id=24  name=主任
id=25  name=副主任
id=26  name=行政秘书
...
```

### 部门-岗位关系表 department_post

```
id              主键
department_id   部门ID
post_id         岗位ID
is_head         是否是该部门的主负责人岗位（boolean）
```

这张表定义的是**一个部门里有哪些岗位**以及**哪个岗位是主负责人**。

示例数据：

```
department_id=20(计算机学院)  post_id=10(院长)     is_head=true
department_id=20(计算机学院)  post_id=11(书记)     is_head=false
department_id=20(计算机学院)  post_id=12(副院长)   is_head=false
department_id=20(计算机学院)  post_id=13(副书记)   is_head=false
department_id=20(计算机学院)  post_id=14(辅导员)   is_head=false   ← 关键：辅导员挂在学院
department_id=20(计算机学院)  post_id=15(教学秘书) is_head=false   ← 关键：教学秘书挂在学院

department_id=23(学工办公室)  post_id=24(主任)     is_head=true
  （学工办公室下不再挂辅导员岗位）

department_id=24(软件工程系)  post_id=16(系主任)   is_head=true

department_id=10(财务处)      post_id=20(处长)     is_head=true
department_id=10(财务处)      post_id=21(副处长)   is_head=false
department_id=10(财务处)      post_id=22(会计)     is_head=false
department_id=10(财务处)      post_id=23(出纳)     is_head=false
```

### 用户-部门-岗位关系表 user_department_post

```
id              主键
user_id         用户ID
department_id   部门ID
post_id         岗位ID
```

这张表定义的是**一个人在哪个部门担任什么岗位**。

示例数据：

```
user_id=501(张老师)   department_id=20(计算机学院)  post_id=14(辅导员)
  ↑ 张老师日常在学工办公室工作，但审批匹配时按学院级别来找

user_id=601(王教授)   department_id=25(教研室)      post_id=18(专任教师)
user_id=701(李院长)   department_id=20(计算机学院)  post_id=10(院长)
user_id=801(赵会计)   department_id=10(财务处)      post_id=22(会计)
```

**一个人可以有多条记录**（比如某人既是系主任又兼任教研室主任）。

---

## 四、学生和老师怎么挂

### 学生

学生挂到他所属的学院：

```
user_id=301(小明)  department_id=20(计算机学院)  post_id=null
```

学生没有岗位，post_id 为 null。这条记录只是标记他属于哪个部门，用于审批时确定起点。

如果你的系细分到了专业/系一级，也可以挂在系上：

```
user_id=301(小明)  department_id=24(软件工程系)  post_id=null
```

这样 ORG_CHAIN_UP 找系主任时先命中软件工程系，找辅导员/院长时继续往上到计算机学院。

### 老师

老师挂到他实际工作的部门和岗位：

```
user_id=601(王教授)  department_id=25(软件工程教研室)  post_id=18(专任教师)
```

---

## 五、用完整例子验证所有匹配场景

### 场景1：学生请假找辅导员（ORG_CHAIN_UP）

```
发起人：小明，department_id = 24（软件工程系）
节点配置：approverType=DEPARTMENT_POST, matchMode=ORG_CHAIN_UP, postId=14（辅导员）

查找过程：
  第1轮：软件工程系(id=24)下有没有辅导员？
    SELECT user_id FROM user_department_post WHERE department_id=24 AND post_id=14
    → 没有

  第2轮：软件工程系的parent_id=20（计算机学院）
    计算机学院是不是根部门？is_root=false，不是，继续
    计算机学院(id=20)下有没有辅导员？
    SELECT user_id FROM user_department_post WHERE department_id=20 AND post_id=14
    → 有！张老师(501)
    → 返回 [501]

结果：创建审批任务给张老师 ✓
```

### 场景2：学生请假找院长（ORG_CHAIN_UP）

```
发起人：小明，department_id = 24（软件工程系）
节点配置：matchMode=ORG_CHAIN_UP, postId=10（院长）

查找过程：
  第1轮：软件工程系 → 没有院长
  第2轮：计算机学院 → 有！李院长(701)
  → 返回 [701] ✓
```

### 场景3：教师报销找系主任（ORG_CHAIN_UP）

```
发起人：王教授，department_id = 25（教研室）
节点配置：matchMode=ORG_CHAIN_UP, postId=16（系主任）

查找过程：
  第1轮：教研室(id=25) → 没有系主任
  第2轮：教研室parent_id=24（软件工程系）→ 有！系主任
  → 返回 ✓
```

### 场景4：报销最后一步找财务会计（FIXED）

```
节点配置：matchMode=FIXED, departmentId=10（财务处）, postId=22（会计）

查找过程：
  直接查：SELECT user_id FROM user_department_post WHERE department_id=10 AND post_id=22
  → 赵会计(801)
  → 返回 [801] ✓

不看发起人是谁，固定找财务处的会计。
```

### 场景5：找当前部门负责人（CURRENT）

```
发起人：教研室的王教授，department_id = 25
节点配置：matchMode=CURRENT, postId=17（教研室主任）

查找过程：
  查教研室(id=25)下有没有教研室主任？
  → 有 → 返回 ✓

如果找不到 → 直接报错，不往上找（CURRENT模式的特点）
```

### 场景6：ORG_CHAIN_UP 到根部门停下来

```
发起人：财务处会计，department_id = 10
节点配置：matchMode=ORG_CHAIN_UP, postId=10（院长）

查找过程：
  第1轮：财务处 → 没有院长
  第2轮：财务处parent_id=1（学校），is_root=true
    → 到根部门了，停下来
    → 报错："在组织链上未找到院长"

不会去匹配校长、党委书记这些根部门下的岗位 ✓
```

### 场景7：显式指定校长审批（FIXED）

```
节点配置：matchMode=FIXED, departmentId=1（学校）, postId=1（校长）

查找过程：
  直接查学校(id=1)下的校长
  → 返回 ✓

只有 FIXED 模式能匹配到根部门下的岗位 ✓
```

---

## 六、ORG_CHAIN_UP 查找逻辑（最终版伪代码）

```
findByOrgChainUp(initiatorDeptId, postId):

  currentDeptId = initiatorDeptId

  循环开始：
    // 查当前部门下有没有这个岗位的人
    userIds = SELECT user_id 
              FROM user_department_post 
              WHERE department_id = currentDeptId AND post_id = postId

    如果 userIds 不为空：
      返回 userIds，结束

    // 没找到，查上级部门
    parentDept = SELECT id, parent_id, is_root 
                 FROM department 
                 WHERE id = (SELECT parent_id FROM department WHERE id = currentDeptId)

    如果 parentDept 为空：
      // 没有上级了
      报错："未找到该岗位人员"，结束

    如果 parentDept.is_root == true：
      // 到根部门了，不再往上（校级领导不参与自动上溯）
      报错："未找到该岗位人员"，结束

    // 继续往上找
    currentDeptId = parentDept.id
  循环结束
```

---

## 七、哪些岗位需要做"链路上挂"

你在录入数据时需要注意的岗位清单：

```
岗位          日常归属部门      岗位关系应该挂到
─────────────────────────────────────────
辅导员        学工办公室        所属学院
教学秘书      教学办公室        所属学院
行政秘书      学院办公室        看需求，如果需要上溯匹配就挂学院

其他岗位（院长、系主任、处长、会计等）本身就在链路上的部门，不需要特殊处理。
```

判断标准就一句话：**这个岗位所在的部门，是不是发起人往上走会经过的部门？如果不是（在旁支子部门里），就把岗位关系往上挂到链路上的部门。**