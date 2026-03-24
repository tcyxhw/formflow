"""
预置表单模板
"""

FORM_TEMPLATES = [
    {
        "id": "template_leave",
        "name": "学生请假申请表",
        "category": "leave",
        "description": "学生请假审批流程",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {
                    "id": "student_name",
                    "type": "text",
                    "label": "学生姓名",
                    "required": True,
                    "props": {
                        "placeholder": "请输入姓名",
                        "maxLength": 20
                    }
                },
                {
                    "id": "student_id",
                    "type": "text",
                    "label": "学号",
                    "required": True,
                    "props": {
                        "placeholder": "请输入学号",
                        "maxLength": 20
                    }
                },
                {
                    "id": "leave_type",
                    "type": "select",
                    "label": "请假类型",
                    "required": True,
                    "props": {
                        "options": [
                            {"label": "事假", "value": "personal"},
                            {"label": "病假", "value": "sick"},
                            {"label": "公假", "value": "official"}
                        ]
                    }
                },
                {
                    "id": "date_range",
                    "type": "date-range",
                    "label": "请假时间",
                    "required": True,
                    "props": {
                        "format": "yyyy-MM-dd",
                        "valueFormat": "yyyy-MM-dd"
                    }
                },
                {
                    "id": "leave_days",
                    "type": "calculated",
                    "label": "请假天数",
                    "props": {
                        "formula": "diffDays(${date_range}.end, ${date_range}.start) + 1",
                        "dependencies": ["date_range"],
                        "precision": 0,
                        "readonly": True
                    }
                },
                {
                    "id": "reason",
                    "type": "textarea",
                    "label": "请假事由",
                    "required": True,
                    "props": {
                        "placeholder": "请详细说明请假原因",
                        "rows": 4,
                        "maxLength": 500
                    }
                },
                {
                    "id": "medical_cert",
                    "type": "upload",
                    "label": "病假证明",
                    "required": False,
                    "props": {
                        "accept": ".pdf,.jpg,.png",
                        "maxSize": 5242880,
                        "maxCount": 3
                    }
                },
                {
                    "id": "contact_phone",
                    "type": "phone",
                    "label": "联系电话",
                    "required": True,
                    "props": {
                        "placeholder": "请输入手机号"
                    }
                }
            ]
        },
        "ui_schema_json": {
            "layout": {
                "type": "grid",
                "columns": 24,
                "gutter": 16,
                "labelWidth": "120px"
            },
            "rows": [
                {"fields": [{"id": "student_name", "span": 12}, {"id": "student_id", "span": 12}]},
                {"fields": [{"id": "leave_type", "span": 12}, {"id": "contact_phone", "span": 12}]},
                {"fields": [{"id": "date_range", "span": 12}, {"id": "leave_days", "span": 12}]},
                {"fields": [{"id": "reason", "span": 24}]},
                {"fields": [{"id": "medical_cert", "span": 24}]}
            ]
        },
        "logic_json": {
            "rules": [
                {
                    "id": "rule_medical_cert",
                    "name": "病假需上传证明",
                    "trigger": {"type": "change", "fields": ["leave_type"]},
                    "condition": "${leave_type} === 'sick'",
                    "actions": [
                        {"type": "visible", "target": "medical_cert", "value": True},
                        {"type": "required", "target": "medical_cert", "value": True}
                    ]
                }
            ]
        }
    },

    {
        "id": "template_reimbursement",
        "name": "费用报销申请表",
        "category": "finance",
        "description": "差旅费、办公费等报销",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {
                    "id": "applicant_name",
                    "type": "text",
                    "label": "申请人",
                    "required": True,
                    "props": {"placeholder": "请输入姓名"}
                },
                {
                    "id": "department",
                    "type": "select",
                    "label": "所属部门",
                    "required": True,
                    "props": {
                        "options": [
                            {"label": "技术部", "value": "tech"},
                            {"label": "财务部", "value": "finance"},
                            {"label": "行政部", "value": "admin"}
                        ]
                    }
                },
                {
                    "id": "expense_type",
                    "type": "select",
                    "label": "报销类型",
                    "required": True,
                    "props": {
                        "options": [
                            {"label": "差旅费", "value": "travel"},
                            {"label": "办公费", "value": "office"},
                            {"label": "会议费", "value": "meeting"},
                            {"label": "其他", "value": "other"}
                        ]
                    }
                },
                {
                    "id": "expense_date",
                    "type": "date",
                    "label": "费用发生日期",
                    "required": True,
                    "props": {"format": "yyyy-MM-dd"}
                },
                {
                    "id": "amount",
                    "type": "number",
                    "label": "报销金额（元）",
                    "required": True,
                    "props": {
                        "precision": 2,
                        "min": 0,
                        "max": 50000,
                        "prefix": "¥"
                    }
                },
                {
                    "id": "description",
                    "type": "textarea",
                    "label": "费用说明",
                    "required": True,
                    "props": {
                        "placeholder": "请详细说明费用用途",
                        "rows": 3,
                        "maxLength": 300
                    }
                },
                {
                    "id": "invoices",
                    "type": "upload",
                    "label": "发票附件",
                    "required": True,
                    "props": {
                        "accept": ".pdf,.jpg,.png",
                        "maxSize": 10485760,
                        "maxCount": 10
                    }
                }
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24, "gutter": 16},
            "rows": [
                {"fields": [{"id": "applicant_name", "span": 12}, {"id": "department", "span": 12}]},
                {"fields": [{"id": "expense_type", "span": 12}, {"id": "expense_date", "span": 12}]},
                {"fields": [{"id": "amount", "span": 24}]},
                {"fields": [{"id": "description", "span": 24}]},
                {"fields": [{"id": "invoices", "span": 24}]}
            ]
        },
        "logic_json": {
            "rules": [
                {
                    "id": "rule_large_amount",
                    "name": "大额报销提示",
                    "trigger": {"type": "change", "fields": ["amount"]},
                    "condition": "${amount} > 5000",
                    "actions": [
                        {
                            "type": "message",
                            "value": "金额超过5000元，需要额外审批"
                        }
                    ]
                }
            ]
        }
    },

    {
        "id": "template_room_booking",
        "name": "会议室预约申请",
        "category": "booking",
        "description": "会议室、教室等场地预约",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {
                    "id": "applicant_name",
                    "type": "text",
                    "label": "申请人",
                    "required": True,
                    "props": {"placeholder": "请输入姓名"}
                },
                {
                    "id": "contact_phone",
                    "type": "phone",
                    "label": "联系电话",
                    "required": True,
                    "props": {"placeholder": "请输入手机号"}
                },
                {
                    "id": "room",
                    "type": "select",
                    "label": "会议室",
                    "required": True,
                    "props": {
                        "options": [
                            {"label": "一号会议室（可容纳20人）", "value": "room_1"},
                            {"label": "二号会议室（可容纳50人）", "value": "room_2"},
                            {"label": "多功能厅（可容纳100人）", "value": "hall"}
                        ]
                    }
                },
                {
                    "id": "booking_date",
                    "type": "date",
                    "label": "使用日期",
                    "required": True,
                    "props": {"format": "yyyy-MM-dd"}
                },
                {
                    "id": "time_range",
                    "type": "time-range",
                    "label": "使用时段",
                    "required": True,
                    "props": {"format": "HH:mm"}
                },
                {
                    "id": "participant_count",
                    "type": "number",
                    "label": "参会人数",
                    "required": True,
                    "props": {
                        "precision": 0,
                        "min": 1,
                        "max": 200
                    }
                },
                {
                    "id": "purpose",
                    "type": "textarea",
                    "label": "使用用途",
                    "required": True,
                    "props": {
                        "placeholder": "请说明会议主题或活动内容",
                        "rows": 3
                    }
                },
                {
                    "id": "equipment_needed",
                    "type": "checkbox",
                    "label": "所需设备",
                    "required": False,
                    "props": {
                        "options": [
                            {"label": "投影仪", "value": "projector"},
                            {"label": "音响", "value": "audio"},
                            {"label": "白板", "value": "whiteboard"},
                            {"label": "话筒", "value": "microphone"}
                        ]
                    }
                }
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "applicant_name", "span": 12}, {"id": "contact_phone", "span": 12}]},
                {"fields": [{"id": "room", "span": 24}]},
                {"fields": [{"id": "booking_date", "span": 12}, {"id": "time_range", "span": 12}]},
                {"fields": [{"id": "participant_count", "span": 12}]},
                {"fields": [{"id": "purpose", "span": 24}]},
                {"fields": [{"id": "equipment_needed", "span": 24}]}
            ]
        }
    },

    {
        "id": "template_activity_registration",
        "name": "活动报名表",
        "category": "activity",
        "description": "讲座、竞赛、志愿活动报名",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "name", "type": "text", "label": "姓名", "required": True},
                {"id": "student_id", "type": "text", "label": "学号", "required": True},
                {"id": "college", "type": "text", "label": "学院", "required": True},
                {"id": "major", "type": "text", "label": "专业", "required": True},
                {"id": "grade", "type": "select", "label": "年级", "required": True,
                 "props": {
                     "options": [
                         {"label": "大一", "value": "1"},
                         {"label": "大二", "value": "2"},
                         {"label": "大三", "value": "3"},
                         {"label": "大四", "value": "4"}
                     ]
                 }},
                {"id": "phone", "type": "phone", "label": "联系电话", "required": True},
                {"id": "email", "type": "email", "label": "电子邮箱", "required": True},
                {"id": "has_experience", "type": "radio", "label": "是否有相关经验", "required": True,
                 "props": {
                     "options": [
                         {"label": "是", "value": "yes"},
                         {"label": "否", "value": "no"}
                     ]
                 }},
                {"id": "experience_desc", "type": "textarea", "label": "经验描述", "required": False,
                 "props": {"rows": 3, "placeholder": "请简述相关经验"}},
                {"id": "reason", "type": "textarea", "label": "报名理由", "required": True,
                 "props": {"rows": 4, "placeholder": "请说明参加本次活动的动机"}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "name", "span": 12}, {"id": "student_id", "span": 12}]},
                {"fields": [{"id": "college", "span": 12}, {"id": "major", "span": 12}]},
                {"fields": [{"id": "grade", "span": 12}, {"id": "phone", "span": 12}]},
                {"fields": [{"id": "email", "span": 24}]},
                {"fields": [{"id": "has_experience", "span": 24}]},
                {"fields": [{"id": "experience_desc", "span": 24}]},
                {"fields": [{"id": "reason", "span": 24}]}
            ]
        },
        "logic_json": {
            "rules": [
                {
                    "id": "rule_experience",
                    "trigger": {"type": "change", "fields": ["has_experience"]},
                    "condition": "${has_experience} === 'yes'",
                    "actions": [
                        {"type": "visible", "target": "experience_desc", "value": True},
                        {"type": "required", "target": "experience_desc", "value": True}
                    ]
                }
            ]
        }
    },

    {
        "id": "template_certificate_apply",
        "name": "在读证明申请",
        "category": "certificate",
        "description": "在读证明、成绩证明等",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "name", "type": "text", "label": "姓名", "required": True},
                {"id": "student_id", "type": "text", "label": "学号", "required": True},
                {"id": "college", "type": "text", "label": "学院", "required": True},
                {"id": "major", "type": "text", "label": "专业", "required": True},
                {"id": "enrollment_year", "type": "number", "label": "入学年份", "required": True,
                 "props": {"precision": 0, "min": 2000, "max": 2030}},
                {"id": "cert_type", "type": "select", "label": "证明类型", "required": True,
                 "props": {
                     "options": [
                         {"label": "在读证明", "value": "enrollment"},
                         {"label": "成绩证明", "value": "transcript"},
                         {"label": "预毕业证明", "value": "pre_graduate"}
                     ]
                 }},
                {"id": "quantity", "type": "number", "label": "份数", "required": True,
                 "props": {"precision": 0, "min": 1, "max": 10, "defaultValue": 1}},
                {"id": "language", "type": "radio", "label": "语言版本", "required": True,
                 "props": {
                     "options": [
                         {"label": "中文", "value": "zh"},
                         {"label": "英文", "value": "en"},
                         {"label": "中英文", "value": "both"}
                     ]
                 }},
                {"id": "purpose", "type": "textarea", "label": "用途说明", "required": True,
                 "props": {"rows": 3, "placeholder": "请说明证明的用途"}},
                {"id": "contact_phone", "type": "phone", "label": "联系电话", "required": True}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "name", "span": 12}, {"id": "student_id", "span": 12}]},
                {"fields": [{"id": "college", "span": 12}, {"id": "major", "span": 12}]},
                {"fields": [{"id": "enrollment_year", "span": 12}, {"id": "cert_type", "span": 12}]},
                {"fields": [{"id": "quantity", "span": 12}, {"id": "language", "span": 12}]},
                {"fields": [{"id": "purpose", "span": 24}]},
                {"fields": [{"id": "contact_phone", "span": 24}]}
            ]
        }
    },

    # 继续添加其他5个模板...
    {
        "id": "template_equipment_borrow",
        "name": "设备借用申请",
        "category": "equipment",
        "description": "实验设备、体育器材等借用",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "borrower_name", "type": "text", "label": "借用人", "required": True},
                {"id": "department", "type": "text", "label": "院系/部门", "required": True},
                {"id": "contact_phone", "type": "phone", "label": "联系电话", "required": True},
                {"id": "equipment_category", "type": "select", "label": "设备类别", "required": True,
                 "props": {
                     "options": [
                         {"label": "电子设备", "value": "electronics"},
                         {"label": "体育器材", "value": "sports"},
                         {"label": "实验仪器", "value": "lab"},
                         {"label": "音响设备", "value": "audio"}
                     ]
                 }},
                {"id": "equipment_name", "type": "text", "label": "设备名称", "required": True},
                {"id": "quantity", "type": "number", "label": "数量", "required": True,
                 "props": {"precision": 0, "min": 1}},
                {"id": "borrow_date", "type": "date", "label": "借用日期", "required": True},
                {"id": "return_date", "type": "date", "label": "预计归还日期", "required": True},
                {"id": "purpose", "type": "textarea", "label": "用途", "required": True,
                 "props": {"rows": 3}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "borrower_name", "span": 12}, {"id": "department", "span": 12}]},
                {"fields": [{"id": "contact_phone", "span": 12}, {"id": "equipment_category", "span": 12}]},
                {"fields": [{"id": "equipment_name", "span": 12}, {"id": "quantity", "span": 12}]},
                {"fields": [{"id": "borrow_date", "span": 12}, {"id": "return_date", "span": 12}]},
                {"fields": [{"id": "purpose", "span": 24}]}
            ]
        }
    },

    {
        "id": "template_internship_apply",
        "name": "实习申请表",
        "category": "internship",
        "description": "校外实习申请",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "student_name", "type": "text", "label": "学生姓名", "required": True},
                {"id": "student_id", "type": "text", "label": "学号", "required": True},
                {"id": "major", "type": "text", "label": "专业", "required": True},
                {"id": "grade", "type": "text", "label": "年级", "required": True},
                {"id": "company_name", "type": "text", "label": "实习单位", "required": True},
                {"id": "company_address", "type": "text", "label": "单位地址", "required": True},
                {"id": "position", "type": "text", "label": "实习岗位", "required": True},
                {"id": "internship_period", "type": "date-range", "label": "实习期限", "required": True},
                {"id": "supervisor_name", "type": "text", "label": "实习导师", "required": True},
                {"id": "supervisor_phone", "type": "phone", "label": "导师电话", "required": True},
                {"id": "parent_agree", "type": "radio", "label": "家长是否同意", "required": True,
                 "props": {
                     "options": [
                         {"label": "同意", "value": "yes"},
                         {"label": "不同意", "value": "no"}
                     ]
                 }},
                {"id": "agreement", "type": "upload", "label": "实习协议", "required": True,
                 "props": {"accept": ".pdf", "maxCount": 1}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "groups": [
                {
                    "title": "学生信息",
                    "fields": ["student_name", "student_id", "major", "grade"]
                },
                {
                    "title": "实习单位信息",
                    "fields": ["company_name", "company_address", "position", "internship_period"]
                },
                {
                    "title": "其他信息",
                    "fields": ["supervisor_name", "supervisor_phone", "parent_agree", "agreement"]
                }
            ]
        }
    },

    {
        "id": "template_graduation_defense",
        "name": "毕业答辩申请",
        "category": "graduation",
        "description": "本科/研究生毕业答辩",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "student_name", "type": "text", "label": "学生姓名", "required": True},
                {"id": "student_id", "type": "text", "label": "学号", "required": True},
                {"id": "major", "type": "text", "label": "专业", "required": True},
                {"id": "thesis_title", "type": "text", "label": "论文题目", "required": True,
                 "props": {"maxLength": 100}},
                {"id": "advisor", "type": "text", "label": "指导教师", "required": True},
                {"id": "thesis_type", "type": "select", "label": "论文类型", "required": True,
                 "props": {
                     "options": [
                         {"label": "学术论文", "value": "academic"},
                         {"label": "工程设计", "value": "engineering"},
                         {"label": "调研报告", "value": "research"}
                     ]
                 }},
                {"id": "word_count", "type": "number", "label": "字数", "required": True,
                 "props": {"precision": 0, "suffix": "字"}},
                {"id": "preferred_date", "type": "date", "label": "期望答辩日期", "required": True},
                {"id": "thesis_file", "type": "upload", "label": "论文文件", "required": True,
                 "props": {"accept": ".pdf,.docx", "maxSize": 52428800, "maxCount": 1}},
                {"id": "abstract", "type": "textarea", "label": "论文摘要", "required": True,
                 "props": {"rows": 5, "maxLength": 1000}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "student_name", "span": 12}, {"id": "student_id", "span": 12}]},
                {"fields": [{"id": "major", "span": 12}, {"id": "advisor", "span": 12}]},
                {"fields": [{"id": "thesis_title", "span": 24}]},
                {"fields": [{"id": "thesis_type", "span": 12}, {"id": "word_count", "span": 12}]},
                {"fields": [{"id": "preferred_date", "span": 12}]},
                {"fields": [{"id": "abstract", "span": 24}]},
                {"fields": [{"id": "thesis_file", "span": 24}]}
            ]
        }
    },

    {
        "id": "template_scholarship_apply",
        "name": "奖学金申请表",
        "category": "scholarship",
        "description": "国家奖学金、校级奖学金申请",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "student_name", "type": "text", "label": "姓名", "required": True},
                {"id": "student_id", "type": "text", "label": "学号", "required": True},
                {"id": "college", "type": "text", "label": "学院", "required": True},
                {"id": "major", "type": "text", "label": "专业班级", "required": True},
                {"id": "scholarship_type", "type": "select", "label": "奖学金类型", "required": True,
                 "props": {
                     "options": [
                         {"label": "国家奖学金", "value": "national"},
                         {"label": "国家励志奖学金", "value": "励志"},
                         {"label": "校级一等奖学金", "value": "school_1"},
                         {"label": "校级二等奖学金", "value": "school_2"},
                         {"label": "校级三等奖学金", "value": "school_3"}
                     ]
                 }},
                {"id": "gpa", "type": "number", "label": "学分绩点", "required": True,
                 "props": {"precision": 2, "min": 0, "max": 5}},
                {"id": "ranking", "type": "text", "label": "专业排名", "required": True,
                 "props": {"placeholder": "如：1/150"}},
                {"id": "awards", "type": "textarea", "label": "获奖情况", "required": False,
                 "props": {"rows": 4, "placeholder": "请列举主要获奖"}},
                {"id": "personal_statement", "type": "textarea", "label": "个人陈述", "required": True,
                 "props": {"rows": 6, "maxLength": 1500}},
                {"id": "certificates", "type": "upload", "label": "证明材料", "required": False,
                 "props": {"accept": ".pdf,.jpg,.png", "maxCount": 10}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "student_name", "span": 12}, {"id": "student_id", "span": 12}]},
                {"fields": [{"id": "college", "span": 12}, {"id": "major", "span": 12}]},
                {"fields": [{"id": "scholarship_type", "span": 24}]},
                {"fields": [{"id": "gpa", "span": 12}, {"id": "ranking", "span": 12}]},
                {"fields": [{"id": "awards", "span": 24}]},
                {"fields": [{"id": "personal_statement", "span": 24}]},
                {"fields": [{"id": "certificates", "span": 24}]}
            ]
        }
    },

    {
        "id": "template_club_apply",
        "name": "社团活动申请",
        "category": "club",
        "description": "社团活动场地、经费申请",
        "schema_json": {
            "version": "1.0.0",
            "fields": [
                {"id": "club_name", "type": "text", "label": "社团名称", "required": True},
                {"id": "activity_name", "type": "text", "label": "活动名称", "required": True},
                {"id": "organizer_name", "type": "text", "label": "负责人", "required": True},
                {"id": "contact_phone", "type": "phone", "label": "联系电话", "required": True},
                {"id": "activity_type", "type": "select", "label": "活动类型", "required": True,
                 "props": {
                     "options": [
                         {"label": "学术讲座", "value": "lecture"},
                         {"label": "文艺演出", "value": "performance"},
                         {"label": "体育竞赛", "value": "sports"},
                         {"label": "公益活动", "value": "volunteer"}
                     ]
                 }},
                {"id": "activity_date", "type": "date", "label": "活动日期", "required": True},
                {"id": "activity_time", "type": "time-range", "label": "活动时间", "required": True},
                {"id": "venue", "type": "text", "label": "活动场地", "required": True},
                {"id": "participant_count", "type": "number", "label": "预计参与人数", "required": True,
                 "props": {"precision": 0}},
                {"id": "budget", "type": "number", "label": "预算经费（元）", "required": True,
                 "props": {"precision": 2, "prefix": "¥"}},
                {"id": "activity_plan", "type": "textarea", "label": "活动方案", "required": True,
                 "props": {"rows": 6}},
                {"id": "proposal", "type": "upload", "label": "策划书", "required": False,
                 "props": {"accept": ".pdf,.docx", "maxCount": 1}}
            ]
        },
        "ui_schema_json": {
            "layout": {"type": "grid", "columns": 24},
            "rows": [
                {"fields": [{"id": "club_name", "span": 12}, {"id": "activity_name", "span": 12}]},
                {"fields": [{"id": "organizer_name", "span": 12}, {"id": "contact_phone", "span": 12}]},
                {"fields": [{"id": "activity_type", "span": 12}, {"id": "activity_date", "span": 12}]},
                {"fields": [{"id": "activity_time", "span": 12}, {"id": "venue", "span": 12}]},
                {"fields": [{"id": "participant_count", "span": 12}, {"id": "budget", "span": 12}]},
                {"fields": [{"id": "activity_plan", "span": 24}]},
                {"fields": [{"id": "proposal", "span": 24}]}
            ]
        }
    }
]


def get_template_by_id(template_id: str) -> dict:
    """根据ID获取模板"""
    for template in FORM_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None


def get_templates_by_category(category: str) -> list:
    """根据分类获取模板列表"""
    return [t for t in FORM_TEMPLATES if t["category"] == category]


def list_all_templates() -> list:
    """获取所有模板（只返回基本信息）"""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "category": t["category"],
            "description": t["description"]
        }
        for t in FORM_TEMPLATES
    ]