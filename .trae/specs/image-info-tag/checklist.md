# Checklist

- [ ] main.py 的 _do_generate 成功后发送了图片+信息标签
- [ ] main.py 的生图失败时也发送了信息标签（包含失败原因）
- [ ] 信息标签格式正确：`预设名 | 耗时X秒` 或 `默认 | 耗时X秒`
- [ ] 失败信息格式正确：`预设名 | 耗时X秒\n失败原因：XXX`
- [ ] _conf_schema.json 添加了 show_image_info 配置项（布尔值，默认 true）
- [ ] show_image_info 关闭时只发图片，不发标签
- [ ] 版本号升到 v1.0.7
- [ ] 提交并推送成功
- [ ] 打标签 v1.0.7-stable
