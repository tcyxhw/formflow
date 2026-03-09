"""
定时任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.services.draft_service import DraftService
from app.services.attachment_service import AttachmentService
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


@scheduler.scheduled_job('cron', hour=2, minute=0)
def clean_expired_drafts():
    """清理过期草稿 - 每天凌晨2点"""
    db = SessionLocal()
    try:
        count = DraftService.clean_expired_drafts(db)
        logger.info(f"Cleaned {count} expired drafts")
    except Exception as e:
        logger.error(f"Clean expired drafts error: {e}")
    finally:
        db.close()


@scheduler.scheduled_job('cron', minute=0)
def clean_temp_attachments():
    """清理临时附件 - 每小时"""
    db = SessionLocal()
    try:
        count = AttachmentService.clean_temp_attachments(db)
        logger.info(f"Cleaned {count} temp attachments")
    except Exception as e:
        logger.error(f"Clean temp attachments error: {e}")
    finally:
        db.close()


@scheduler.scheduled_job('cron', hour=3, minute=0)
def clean_export_files():
    """清理导出文件 - 每天凌晨3点"""
    from pathlib import Path
    from datetime import datetime, timedelta
    from app.config import settings

    try:
        export_dir = Path(settings.EXPORT_TEMP_DIR)
        if not export_dir.exists():
            return

        cutoff_time = datetime.now() - timedelta(hours=24)
        count = 0

        for file_path in export_dir.glob("*.xlsx"):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                file_path.unlink()
                count += 1

        logger.info(f"Cleaned {count} export files")
    except Exception as e:
        logger.error(f"Clean export files error: {e}")


@scheduler.scheduled_job('interval', minutes=5)
def escalate_overdue_tasks():
    """SLA超时任务升级扫描 - 每5分钟执行一次

    扫描所有租户的超时任务，执行升级策略：
    1. 改派上级
    2. 回组池
    3. 转值班（预留）
    """
    from app.services.sla_service import SLAService
    from app.services.notification_service import NotificationService
    from app.models.user import Tenant

    db = SessionLocal()
    try:
        # 获取所有活跃租户
        tenants = db.query(Tenant).all()

        total_escalated = 0
        total_notified = 0

        for tenant in tenants:
            try:
                # 执行升级
                results = SLAService.escalate_overdue_tasks(
                    tenant_id=tenant.id,
                    db=db,
                    batch_size=100,
                )

                successful = [r for r in results if r.success]
                total_escalated += len(successful)

                # 发送升级通知
                for result in successful:
                    if result.new_assignee:
                        try:
                            NotificationService.notify_task_escalation(
                                task_id=result.task_id,
                                old_assignee_id=result.old_assignee,
                                new_assignee_id=result.new_assignee,
                                process_name=f"流程#{result.task_id}",  # 简化处理
                                escalation_reason=result.message,
                                tenant_id=tenant.id,
                                db=db,
                            )
                            total_notified += 1
                        except Exception as notify_error:
                            logger.error(
                                f"升级通知发送失败",
                                extra={
                                    "task_id": result.task_id,
                                    "tenant_id": tenant.id,
                                    "error": str(notify_error),
                                },
                            )

                db.commit()

                if successful:
                    logger.info(
                        f"租户 {tenant.id} SLA升级完成",
                        extra={
                            "tenant_id": tenant.id,
                            "escalated": len(successful),
                            "failed": len(results) - len(successful),
                        },
                    )

            except Exception as tenant_error:
                logger.error(
                    f"租户SLA升级失败",
                    extra={
                        "tenant_id": tenant.id,
                        "error": str(tenant_error),
                    },
                )
                db.rollback()
                continue

        logger.info(
            f"SLA升级扫描全部完成",
            extra={
                "total_escalated": total_escalated,
                "total_notified": total_notified,
                "tenant_count": len(tenants),
            },
        )

    except Exception as e:
        logger.error(f"SLA升级扫描异常: {e}")
        db.rollback()
    finally:
        db.close()