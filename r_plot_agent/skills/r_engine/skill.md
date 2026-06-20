# r_engine Skill

## 触发条件
当用户提供绘图需求或需要创建 R Project 时触发。

## 输入
- 需求描述（图表类型、数据源）
- conductor 生成的 handler
- R Project 路径

## 处理流程

### 创建 R Project（如不存在）
1. 创建 RStudio Project 目录结构
2. 初始化 .Rproj 文件
3. 创建子目录（figures/, scripts/, data/）

### 执行绘图
1. 在指定 R Project 目录中工作
2. 根据需求选择 handler
3. 绑定实际数据字段到 handler
4. 应用美学映射
5. 生成 .r 脚本并执行

## 输出
- RStudio Project → `*.Rproj`
- 所有 R 对象 → `Rproject/.RData`
- 图形 PDF → `Rproject/figures/*.pdf`
- R 脚本 → `Rproject/scripts/*.r`
