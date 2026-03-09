"""
模块用途: 并行节点运行态管理
依赖配置: 无
数据流向: ProcessService -> ParallelRuntimeService -> ParallelRuntime
函数清单:
    - ParallelRuntimeService.record_parallel_fork(): 记录并行分叉开启信息
    - ParallelRuntimeService.reset_runtime(): 重置指定分叉的运行态
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.workflow import ParallelRuntime


class ParallelRuntimeService:
    """并行分叉运行态管理工具。"""

    @staticmethod
    def record_parallel_fork(
        process_instance_id: int,
        fork_node_id: int,
        tenant_id: int,
        opened_nodes: Iterable[int],
        db: Session,
        join_policy: str = "all",
        n_required: int | None = None,
    ) -> ParallelRuntime:
        """记录或更新并行分叉信息。

        :param process_instance_id: 流程实例 ID
        :param fork_node_id: 发起并行的节点 ID
        :param tenant_id: 租户 ID
        :param opened_nodes: 本次开启的分支节点 ID 列表
        :param db: 数据库会话
        :param join_policy: 合流策略，默认为 all
        :param n_required: n_of_m 策略需要的计数
        :return: 并行运行态记录

        Time: O(1), Space: O(1)
        """

        branches: List[int] = list(dict.fromkeys(opened_nodes))
        runtime = (
            db.query(ParallelRuntime)
            .filter(
                ParallelRuntime.process_instance_id == process_instance_id,
                ParallelRuntime.fork_node_id == fork_node_id,
                ParallelRuntime.tenant_id == tenant_id,
            )
            .with_for_update(of=ParallelRuntime)
            .first()
        )

        opened_count = len(branches)
        required = n_required if n_required is not None else opened_count

        if runtime:
            runtime.opened_count = opened_count
            runtime.opened_branches = branches
            runtime.arrived_count = 0
            runtime.join_policy = join_policy
            runtime.n_required = required
            runtime.closed = False
        else:
            runtime = ParallelRuntime(
                tenant_id=tenant_id,
                process_instance_id=process_instance_id,
                fork_node_id=fork_node_id,
                opened_count=opened_count,
                opened_branches=branches,
                join_policy=join_policy,
                n_required=required,
            )
            db.add(runtime)

        return runtime

    @staticmethod
    def reset_runtime(process_instance_id: int, fork_node_id: int, tenant_id: int, db: Session) -> None:
        """将并行运行态标记为已关闭，便于下次重新进入。

        Time: O(1), Space: O(1)
        """

        runtime = (
            db.query(ParallelRuntime)
            .filter(
                ParallelRuntime.process_instance_id == process_instance_id,
                ParallelRuntime.fork_node_id == fork_node_id,
                ParallelRuntime.tenant_id == tenant_id,
            )
            .first()
        )
        if runtime:
            runtime.closed = True
            runtime.arrived_count = runtime.opened_count

    @staticmethod
    def handle_branch_arrival(
        process_instance_id: int,
        tenant_id: int,
        node_id: int,
        db: Session,
    ) -> bool:
        """处理并行分支节点完成事件。

        :return: 是否允许当前分支继续推进后续路由

        Time: O(K), Space: O(1) K=并行分叉数量
        """

        runtimes = (
            db.query(ParallelRuntime)
            .filter(
                ParallelRuntime.process_instance_id == process_instance_id,
                ParallelRuntime.tenant_id == tenant_id,
                ParallelRuntime.closed.is_(False),
            )
            .with_for_update(of=ParallelRuntime)
            .all()
        )

        target: Optional[ParallelRuntime] = None
        for runtime in runtimes:
            if runtime.opened_branches and node_id in runtime.opened_branches:
                target = runtime
                break

        if not target:
            return True

        if target.closed:
            return False

        target.arrived_count = min(target.arrived_count + 1, target.opened_count)
        required = target.n_required or target.opened_count
        join_policy = (target.join_policy or "all").lower()

        should_release = False
        if join_policy == "any":
            should_release = target.arrived_count >= 1
        elif join_policy in {"n_of_m", "n_of", "n"}:
            should_release = target.arrived_count >= required
        else:
            should_release = target.arrived_count >= target.opened_count

        if should_release:
            target.closed = True
            return True

        return False
