# 教育考试院官网爬虫系统 - 设计文档

**版本**: 1.1  
**日期**: 2026-03-31  
**作者**: Claude Code  
**状态**: 已通过Spec Review

---

## 1. 项目概述

### 1.1 目标
开发一个自动化爬虫系统，用于抓取全国31个省份教育考试院/招生办公室的官网内容，提供API供前端网站调用，支持三级浏览（省份→板块→内容）和增量更新检测。

### 1.2 功能需求
1. **省份管理**：管理31个省份的基础信息和入口URL
2. **板块发现**：基于预定义URL自动发现并识别网站板块结构
3. **内容抓取**：抓取列表页和详情页全文内容
4. **更新检测**：识别新增、修改的内容
5. **API服务**：提供RESTful API供前端调用
6. **刷新机制**：支持手动和自动定时刷新

---

## 2. 技术架构

### 2.1 技术栈
| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 异步Python Web框架，自动生成OpenAPI文档 |
| 爬虫引擎 | Playwright | 支持JavaScript渲染，处理动态网页 |
| 解析库 | BeautifulSoup4 + lxml | HTML解析和内容提取 |
| 数据库 | MySQL 8.0 | 关系型数据存储 |
| ORM | SQLAlchemy 2.0 | 数据库模型和操作 |
| 任务调度 | APScheduler | 定时任务执行 |
| 部署 | Docker Compose | 容器化部署 |

### 2.2 系统架构图
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端网站       │────▶│   FastAPI       │────▶│     MySQL       │
│  (已存在)        │◀────│   后端服务       │◀────│   数据库        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   爬虫引擎       │
                        │  Playwright     │
                        └─────────────────┘
```

---

## 3. 数据库设计

### 3.1 实体关系图
```
provinces (1) ────< (N) sections (1) ────< (N) contents
      │                      │                      │
      │                      │                      │
      └──────────────────────┴──────────────────────┘
                              │
                              ▼
                        updates (记录内容变更)
```

### 3.2 表结构

#### 3.2.1 provinces（省份表）
```sql
CREATE TABLE provinces (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL COMMENT '省份代码，如 sichuan',
    name VARCHAR(50) NOT NULL COMMENT '省份名称，如 四川',
    url VARCHAR(500) NOT NULL COMMENT '官网入口URL',
    status ENUM('active', 'inactive', 'error') DEFAULT 'active',
    last_crawl_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 3.2.2 sections（板块表）
```sql
CREATE TABLE sections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    province_id INT NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT '板块名称，如 通知公告',
    url VARCHAR(500) NOT NULL,
    selector_pattern VARCHAR(500) NULL COMMENT '列表项CSS选择器',
    parent_id INT NULL COMMENT '父板块ID，支持多级',
    is_auto_discovered BOOLEAN DEFAULT FALSE COMMENT '是否自动发现',
    status ENUM('active', 'inactive', 'error') DEFAULT 'active',
    last_crawl_at DATETIME NULL,
    content_count INT DEFAULT 0 COMMENT '内容数量缓存',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (province_id) REFERENCES provinces(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES sections(id) ON DELETE SET NULL,
    KEY idx_province_id (province_id),
    KEY idx_parent_id (parent_id),
    KEY idx_status (status, last_crawl_at)
);
```

#### 3.2.3 contents（内容表）
```sql
CREATE TABLE contents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    section_id INT NOT NULL,
    title VARCHAR(500) NOT NULL COMMENT '文章标题',
    url VARCHAR(500) NOT NULL COMMENT '文章链接',
    publish_date DATE NULL COMMENT '发布日期',
    content_text LONGTEXT NULL COMMENT '正文纯文本',
    html_snapshot LONGTEXT NULL COMMENT 'HTML快照（保留30天）',
    content_hash VARCHAR(64) NOT NULL COMMENT '内容哈希，用于更新检测',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已被删除',
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    UNIQUE KEY uk_section_url (section_id, url(255)),
    KEY idx_section_id (section_id),
    KEY idx_publish_date (publish_date),
    KEY idx_crawled_at (crawled_at),
    KEY idx_content_hash (content_hash),
    FULLTEXT INDEX idx_fulltext (title, content_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3.2.4 update_logs（更新记录表）
```sql
CREATE TABLE update_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT NOT NULL,
    update_type ENUM('new', 'modified', 'deleted') NOT NULL,
    old_hash VARCHAR(64) NULL,
    new_hash VARCHAR(64) NULL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    KEY idx_detected_at (detected_at),
    KEY idx_is_read (is_read, detected_at)
);
```

#### 3.2.5 crawl_jobs（爬虫任务表）
```sql
CREATE TABLE crawl_jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_type ENUM('full', 'province', 'section') NOT NULL,
    target_id INT NULL COMMENT '目标ID（省份或板块）',
    status ENUM('pending', 'running', 'completed', 'failed', 'timeout') DEFAULT 'pending',
    total_tasks INT DEFAULT 0,
    completed_tasks INT DEFAULT 0,
    error_message TEXT NULL,
    heartbeat_at DATETIME NULL COMMENT '心跳时间，用于检测僵死任务',
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_status (status, created_at),
    KEY idx_heartbeat (heartbeat_at)
);
```

#### 3.2.6 crawl_configs（爬虫配置表）
```sql
CREATE TABLE crawl_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    province_id INT NULL COMMENT 'NULL表示全局默认配置',
    section_id INT NULL COMMENT 'NULL表示省份默认配置',
    list_selector VARCHAR(500) DEFAULT 'a' COMMENT '列表项选择器',
    title_selector VARCHAR(200) NULL COMMENT '标题选择器',
    date_selector VARCHAR(200) NULL COMMENT '日期选择器',
    date_format VARCHAR(100) NULL COMMENT '日期格式，如 %Y-%m-%d',
    content_selector VARCHAR(500) NULL COMMENT '正文区域选择器（优先于自动提取）',
    max_pages INT DEFAULT 10 COMMENT '最大抓取页数',
    crawl_depth INT DEFAULT 2 COMMENT '板块发现深度',
    request_delay_ms INT DEFAULT 1500 COMMENT '请求间隔毫秒',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (province_id) REFERENCES provinces(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    UNIQUE KEY uk_province_section (province_id, section_id)
);
```

#### 3.2.7 request_logs（请求日志表）
```sql
CREATE TABLE request_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NULL,
    province_id INT NULL,
    url VARCHAR(500) NOT NULL,
    method VARCHAR(10) DEFAULT 'GET',
    status_code INT NULL,
    response_time_ms INT NULL,
    error_message TEXT NULL,
    is_success BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_job_id (job_id),
    KEY idx_created_at (created_at),
    KEY idx_province_id (province_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPRESSED
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION p2027 VALUES LESS THAN (2028),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

---

## 4. API接口设计

### 4.1 省份接口
```yaml
GET /api/provinces
Response: [
  {
    "id": 1,
    "code": "sichuan",
    "name": "四川",
    "url": "https://www.sceea.cn/",
    "status": "active",
    "last_crawl_at": "2026-03-30T03:00:00Z",
    "section_count": 8
  }
]

GET /api/provinces/{id}/stats
Response: {
  "total_contents": 156,
  "last_update": "2026-03-30T05:30:00Z",
  "new_today": 3
}
```

### 4.2 板块接口
```yaml
GET /api/provinces/{province_id}/sections
Response: [
  {
    "id": 1,
    "name": "通知公告",
    "url": "https://www.sceea.cn/List/NewsList_62_1.html",
    "parent_id": null,
    "children": [...],
    "content_count": 45
  }
]

GET /api/sections/{id}
Response: {
  "id": 1,
  "name": "通知公告",
  "province": { "id": 1, "name": "四川" },
  "url": "...",
  "is_auto_discovered": false,
  "last_crawl_at": "2026-03-30T03:15:00Z"
}
```

### 4.3 内容接口
```yaml
GET /api/sections/{section_id}/contents?page=1&page_size=20
Response: {
  "total": 156,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "id": 1,
      "title": "2026年上半年自学考试报名通知",
      "url": "https://www.sceea.cn/...",
      "publish_date": "2026-03-25",
      "is_new": true
    }
  ]
}

GET /api/contents/{id}
Response: {
  "id": 1,
  "title": "2026年上半年自学考试报名通知",
  "url": "...",
  "publish_date": "2026-03-25",
  "content_text": "...正文纯文本...",
  "html_snapshot": "...原始HTML...",
  "section": { "id": 1, "name": "通知公告" },
  "province": { "id": 1, "name": "四川" },
  "crawled_at": "2026-03-30T03:20:00Z"
}

GET /api/contents/search?keyword=报名&province_id=1
Response: 搜索结果列表
```

### 4.4 爬虫控制接口
```yaml
POST /api/crawl/trigger
Body: { "type": "full" }  # full|province|section
      { "type": "province", "province_id": 1 }
Response: { "job_id": 123, "status": "started" }

GET /api/crawl/status/{job_id}
Response: {
  "id": 123,
  "type": "full",
  "status": "running",
  "progress": "15/31",
  "current_province": "江苏",
  "started_at": "2026-03-30T03:00:00Z"
}

GET /api/crawl/queue
Response: {
  "pending": 0,
  "running": 1,
  "completed_today": 2
}
```

### 4.5 更新通知接口
```yaml
GET /api/updates?unread_only=true&limit=20
Response: {
  "total_unread": 15,
  "data": [
    {
      "id": 1,
      "type": "new",
      "content": {
        "id": 100,
        "title": "...",
        "province": "四川",
        "section": "通知公告"
      },
      "detected_at": "2026-03-30T05:30:00Z"
    }
  ]
}

PUT /api/updates/{id}/read
Response: { "success": true }

PUT /api/updates/read-all
Response: { "marked_count": 15 }
```

---

## 4.6 认证与授权

```yaml
# 管理接口需要API Key认证
POST /api/crawl/trigger
Headers:
  X-API-Key: your-secret-api-key

# 公开接口无需认证
GET /api/provinces
GET /api/sections/{id}/contents
```

**API Key配置**: 通过环境变量 `ADMIN_API_KEY` 设置，默认为随机生成的UUID。

---

## 4.7 健康检查

```yaml
GET /health
Response:
  {
    "status": "healthy",
    "database": "connected",
    "crawler": "idle",  # idle|running|error
    "last_crawl": "2026-03-30T03:00:00Z",
    "queued_jobs": 0
  }
```

---

## 5. 爬虫核心逻辑

### 5.0 反检测与速率限制策略

```python
class CrawlerPolicy:
    """爬虫策略配置"""
    
    # 速率限制
    REQUEST_DELAY_MIN = 1000  # 最小间隔1秒
    REQUEST_DELAY_MAX = 3000  # 最大间隔3秒
    MAX_CONCURRENT_PROVINCES = 3  # 同时爬取省份数
    MAX_RETRIES = 3
    
    # User-Agent轮换列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
        # ... 更多真实浏览器UA
    ]
    
    @staticmethod
    def get_random_delay():
        return random.randint(
            CrawlerPolicy.REQUEST_DELAY_MIN, 
            CrawlerPolicy.REQUEST_DELAY_MAX
        ) / 1000
```

**反检测措施**:
1. 随机User-Agent
2. 随机请求间隔（1-3秒）
3. 限制并发（最多3个省份同时爬取）
4. 模拟真实浏览器行为（Playwright默认行为）
5. 失败重试3次，指数退避

### 5.0.1 错误处理与恢复

```python
class CrawlJobManager:
    """任务管理器 - 确保任务可靠性"""
    
    JOB_TIMEOUT_MINUTES = 30  # 任务超时时间
    
    async def start_job(self, job_id: int):
        # 启动时记录开始时间和心跳
        pass
    
    async def update_heartbeat(self, job_id: int):
        # 每2分钟更新一次心跳
        pass
    
    async def recover_stalled_jobs(self):
        # 启动时检查：心跳超过35分钟未更新的任务标记为timeout
        pass
    
    async def resume_interrupted_job(self, job_id: int):
        # 支持断点续传：从上次完成的省份继续
        pass
```

### 5.1 板块发现策略

```python
class SectionDiscovery:
    """板块自动发现器
    
    策略说明：
    1. 首先加载get.txt中预定义的省份入口URL作为种子板块
    2. 访问种子页面，提取导航菜单中的所有链接
    3. 基于关键词匹配识别有价值的板块
    4. 自动发现的板块标记为is_auto_discovered=True
    5. 支持手动配置覆盖自动发现结果
    
    错误处理：
    - JavaScript渲染失败时，降级到静态HTML解析
    - 链接提取失败时，使用crawl_configs中预设的selector
    - 最多递归3层，防止无限递归
    """
    
    # 高优先级板块关键词（匹配这些词优先保留）
    PRIORITY_KEYWORDS = [
        "通知公告", "最新消息", "新闻动态",
        "报名", "报考", "注册", "志愿填报",
        "成绩", "查分", "分数查询", "录取查询",
        "考试安排", "考试计划", "考试科目", "考试时间",
        "准考证", "打印", "下载",
        "政策", "规定", "办法", "简章", "大纲"
    ]
    
    # 过滤词（匹配这些词的链接排除）
    EXCLUDE_KEYWORDS = [
        "关于我们", "联系方式", "网站地图", "隐私政策",
        "登录", "注册账号", "忘记密码", "个人中心",
        "首页", "返回", "更多", "详细", "点击"
    ]
    
    async def discover(self, province: Province, max_depth: int = 2) -> List[Section]:
        """
        1. 访问省份首页（Playwright渲染）
        2. 提取导航链接（优先使用crawl_configs.selector_pattern）
        3. 根据关键词匹配识别板块
        4. 递归发现子板块（最多max_depth级）
        5. 保存到数据库，标记is_auto_discovered
        """
        pass
    
    def calculate_relevance_score(self, text: str, url: str) -> float:
        """
        计算链接的相关性分数
        - 标题/链接文本匹配PRIORITY_KEYWORDS加分
        - 匹配EXCLUDE_KEYWORDS减分或直接排除
        - URL包含edu/gov.cn等域名加分
        - 返回0-1之间的分数，低于0.3的丢弃
        """
        pass
```

### 5.2 内容抓取流程

```python
class ContentCrawler:
    """内容抓取器"""
    
    async def crawl_section(self, section: Section):
        """
        1. 访问板块列表页
        2. 提取列表项（标题、链接、日期）
        3. 对每个链接：
           a. 检查是否已存在且未变化（对比hash）
           b. 访问详情页
           c. 提取正文内容（智能正文提取算法）
           d. 计算hash并保存
           e. 如有变化，记录update_log
        4. 处理分页（最多抓10页或最近3个月）
        """
        pass
    
    def extract_content(self, html: str, url: str) -> str:
        """
        使用 trafilatura 库进行正文提取
        
        优势：
        - 专门训练用于提取新闻和文章正文
        - 准确率高于通用的readability
        - 支持中文内容
        - 可输出纯文本或Markdown
        
        备选方案：若trafilatura失败，降级到readability-lxml
        """
        import trafilatura
        
        # 优先使用trafilatura
        text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False  # 允许备用提取
        )
        
        if text and len(text) > 100:
            return text
        
        # 降级方案：使用readability
        from readability import Document
        doc = Document(html)
        return doc.summary()
        pass
```

### 5.3 更新检测机制

```python
def detect_update(content: Content, new_hash: str) -> UpdateType:
    """
    - new: URL不存在于数据库 → 新增
    - modified: URL存在但hash不同 → 修改
    - deleted: 列表页存在但详情页404 → 删除（标记is_deleted）
    """
    pass
```

---

## 6. 项目结构

```
testcrawl/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── models/              # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── province.py
│   │   ├── section.py
│   │   ├── content.py
│   │   └── update.py
│   ├── schemas/             # Pydantic模型
│   │   ├── __init__.py
│   │   ├── province.py
│   │   ├── section.py
│   │   └── content.py
│   ├── routers/             # API路由
│   │   ├── __init__.py
│   │   ├── provinces.py
│   │   ├── sections.py
│   │   ├── contents.py
│   │   └── crawl.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── crawler.py       # 爬虫核心
│   │   ├── section_discovery.py
│   │   └── content_extractor.py
│   └── utils/
│       ├── __init__.py
│       ├── hash.py          # 哈希计算
│       └── html_cleaner.py  # HTML清理
├── crawler/                 # 独立爬虫脚本
│   ├── __init__.py
│   └── runner.py
├── data/                    # 数据文件
│   ├── init_data.sql        # 省份初始化数据
│   └── get.txt              # 原始URL列表
├── tests/
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 7. 部署方案

### 7.1 Docker Compose配置

```yaml
version: '3.8'
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: exam_crawler
    volumes:
      - mysql_data:/var/lib/mysql
      - ./data/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql+pymysql://root:rootpass@db:3306/exam_crawler
      CRAWL_SCHEDULE: "0 3 * * *"  # 每天凌晨3点
    depends_on:
      - db
    volumes:
      - ./data:/app/data

volumes:
  mysql_data:
```

### 7.2 启动命令
```bash
docker-compose up -d
```

---

## 8. 数据保留与清理策略

### 8.1 HTML快照保留期
```sql
-- 每天凌晨4点清理30天前的HTML快照
UPDATE contents 
SET html_snapshot = NULL 
WHERE crawled_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 8.2 请求日志清理
- 保留最近90天的请求日志
- 使用MySQL分区表，按年分区，便于删除旧数据

### 8.3 已删除内容处理
- 标记删除的内容保留90天后物理删除
- 更新记录(update_logs)永久保留

---

## 9. 性能考虑

1. **并发控制**：Playwright使用连接池，限制同时打开的浏览器实例数（建议5-10个）
2. **增量抓取**：只抓取最近3个月的内容，避免全量抓取历史数据
3. **缓存策略**：已抓取的URL记录hash，避免重复下载未变化的页面
4. **失败重试**：网络错误时重试3次，指数退避
5. **全文搜索**：使用MySQL FULLTEXT索引，满足基本搜索需求

---

## 10. 后续扩展

1. **全文搜索**：集成Elasticsearch实现更强大的内容全文检索
2. **内容去重**：基于SimHash检测相似内容，避免同一通知在多个板块重复出现
3. **智能分类**：基于NLP自动给内容打标签（报名/成绩/政策等）
4. **推送通知**：WebSocket或SSE实时推送更新到前端
5. **可视化监控**：集成Prometheus + Grafana监控爬虫运行状态

---

## 11. 设计确认

本设计已通过以下决策：
- ✅ 技术栈：FastAPI + Playwright + MySQL
- ✅ 板块发现：预定义 + 自动补充（最多3层递归）
- ✅ 内容存储：列表 + 详情页全文（使用trafilatura提取）
- ✅ 部署方式：Docker Compose
- ✅ 速率限制：1-3秒随机延迟，最多3省份并发
- ✅ 数据保留：HTML快照30天，请求日志90天
- ✅ API认证：X-API-Key管理接口保护
