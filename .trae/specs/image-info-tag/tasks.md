# Tasks

- [x] Task 1: 修改 main.py，在 _do_generate 成功后添加信息标签
  - [ ] SubTask 1.1: 在 _do_generate 返回后，构造信息标签字符串（预设名 | 耗时X秒）
  - [ ] SubTask 1.2: 使用 event.image_result 发送图片后，再用 event.send 发送文字标签
  - [ ] SubTask 1.3: 读取当前使用的预设名称（如果有）
  - [ ] SubTask 1.4: 生图失败时也要发送信息标签，格式：`预设名 | 耗时X秒\n失败原因：XXX`

- [x] Task 2: 在 _conf_schema.json 添加 show_image_info 配置项
  - [x] SubTask 2.1: 添加布尔类型配置项 show_image_info，默认 true

- [x] Task 3: 在 main.py 读取 show_image_info 配置，控制是否发送标签

- [x] Task 4: 提交代码并推送，版本升到 v1.0.7

- [x] Task 5: 创建标签 v1.0.7-stable
