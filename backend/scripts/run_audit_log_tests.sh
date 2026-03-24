#!/bin/bash
# 运行审计日志修复相关的测试

echo "========================================="
echo "运行审计日志阻塞问题修复测试"
echo "========================================="
echo ""

echo "1️⃣  运行 Bug Condition 探索性测试..."
echo "----------------------------------------"
pytest backend/tests/test_audit_log_blocking_bug_exploration.py -v -s

echo ""
echo "2️⃣  运行保持性测试..."
echo "----------------------------------------"
pytest backend/tests/test_audit_log_preservation.py -v -s

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="
