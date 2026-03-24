"""
生成可填写表单测试数据
用于测试表单填写工作区功能
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.user import User, Tenant
from app.models.form import Form, FormVersion, FormPermission
from app.schemas.form_permission_schemas import PermissionType


def generate_fillable_forms():
    """生成可填写的测试表单"""
    
    db = next(get_db())
    
    try:
        print("=== 生成可填写表单测试数据 ===\n")
        
        # 1. 获取租户和用户
        tenant = db.query(Tenant).first()
        if not tenant:
            print("❌ 错误: 未找到租户，请先运行数据库迁移")
            return
        
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            print("❌ 错误: 未找到活跃用户")
            return
        
        print(f"✅ 使用租户: {tenant.name} (ID: {tenant.id})")
        print(f"✅ 使用用户: {user.name} (ID: {user.id})\n")
        
        # 2. 创建测试表单
        forms_data = [
            {
                "name": "学生信息登记表",
                "category": "教务",
                "schema": {
                    "version": "1.0.0",
                    "fields": [
                        {
                            "id": "name",
                            "type": "text",
                            "label": "姓名",
                            "required": True,
                            "props": {"placeholder": "请输入姓名"}
                        },
                        {
                            "id": "student_id",
                            "type": "text",
                            "label": "学号",
                            "required": True,
                            "props": {"placeholder": "请输入学号"}
                        },
                        {
                            "id": "major",
                            "type": "text",
                            "label": "专业",
                            "required": True,
                            "props": {"placeholder": "请输入专业"}
                        }
                    ],
                    "fieldOrder": ["name", "student_id", "major"]
                },
                "ui_schema": {
                    "layout": {
                        "type": "vertical",
                        "labelWidth": 120,
                        "labelPosition": "right",
                        "size": "medium"
                    },
                    "rows": [],
                    "groups": []
                }
            },
            {
                "name": "课程评价问卷",
                "category": "教学",
                "schema": {
                    "version": "1.0.0",
                    "fields": [
                        {
                            "id": "course_name",
                            "type": "text",
                            "label": "课程名称",
                            "required": True,
                            "props": {"placeholder": "请输入课程名称"}
                        },
                        {
                            "id": "rating",
                            "type": "rate",
                            "label": "课程评分",
                            "required": True,
                            "props": {"count": 5}
                        },
                        {
                            "id": "feedback",
                            "type": "textarea",
                            "label": "意见反馈",
                            "required": False,
                            "props": {"placeholder": "请输入您的意见和建议"}
                        }
                    ],
                    "fieldOrder": ["course_name", "rating", "feedback"]
                },
                "ui_schema": {
                    "layout": {
                        "type": "vertical",
                        "labelWidth": 120,
                        "labelPosition": "right",
                        "size": "medium"
                    },
                    "rows": [],
                    "groups": []
                }
            },
            {
                "name": "活动报名表",
                "category": "学工",
                "schema": {
                    "version": "1.0.0",
                    "fields": [
                        {
                            "id": "activity_name",
                            "type": "text",
                            "label": "活动名称",
                            "required": True,
                            "props": {"placeholder": "请输入活动名称"}
                        },
                        {
                            "id": "participant_name",
                            "type": "text",
                            "label": "参与者姓名",
                            "required": True,
                            "props": {"placeholder": "请输入姓名"}
                        },
                        {
                            "id": "phone",
                            "type": "phone",
                            "label": "联系电话",
                            "required": True,
                            "props": {"placeholder": "请输入手机号"}
                        }
                    ],
                    "fieldOrder": ["activity_name", "participant_name", "phone"]
                },
                "ui_schema": {
                    "layout": {
                        "type": "vertical",
                        "labelWidth": 120,
                        "labelPosition": "right",
                        "size": "medium"
                    },
                    "rows": [],
                    "groups": []
                },
                "deadline": datetime.now() + timedelta(days=7)
            }
        ]
        
        created_forms = []
        
        for form_data in forms_data:
            # 检查表单是否已存在
            existing_form = db.query(Form).filter(
                Form.name == form_data["name"],
                Form.tenant_id == tenant.id
            ).first()
            
            if existing_form:
                print(f"⚠️  表单已存在: {form_data['name']} (ID: {existing_form.id})")
                created_forms.append(existing_form)
                continue
            
            # 创建表单
            form = Form(
                name=form_data["name"],
                category=form_data["category"],
                access_mode="authenticated",
                owner_user_id=user.id,
                status="published",  # 直接发布
                allow_edit=False,
                tenant_id=tenant.id,
                submit_deadline=form_data.get("deadline")
            )
            db.add(form)
            db.flush()
            
            # 创建表单版本
            form_version = FormVersion(
                form_id=form.id,
                version=1,
                schema_json=form_data["schema"],
                ui_schema_json=form_data["ui_schema"],
                logic_json={"rules": []},
                published_at=datetime.now(),
                tenant_id=tenant.id
            )
            db.add(form_version)
            db.flush()
            
            # 创建 FILL 权限（让当前用户可以填写）
            permission = FormPermission(
                form_id=form.id,
                grant_type="user",
                grantee_id=user.id,
                permission=PermissionType.FILL.value,
                tenant_id=tenant.id
            )
            db.add(permission)
            
            created_forms.append(form)
            print(f"✅ 创建表单: {form.name} (ID: {form.id})")
            print(f"   - 版本: v{form_version.version}")
            print(f"   - 权限: FILL (用户 {user.id})")
        
        # 提交所有更改
        db.commit()
        
        print(f"\n=== 完成 ===")
        print(f"共创建 {len(created_forms)} 个可填写表单")
        print(f"用户 {user.name} (ID: {user.id}) 现在可以在填写工作区看到这些表单")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 生成测试数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    generate_fillable_forms()
