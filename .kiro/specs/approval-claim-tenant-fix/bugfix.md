# Bugfix Requirements Document

## Introduction

This document describes the bugs to be fixed in the approval workflow:
1. **Backend bug**: `tenant_id` field is NULL when creating `TaskActionLog` during claim operation, causing database constraint violation
2. **Frontend UI bugs**: Remove "轨迹" section from approval workbench, remove "无截止" status display, and fix SLA label-font mismatch issue

## Bug Analysis

### Current Behavior (Defect)

**Backend - TaskActionLog tenant_id Issue:**
1.1 WHEN `claim_task` is called THEN the system calls `_create_action_log` without passing `tenant_id` parameter
1.2 WHEN `_create_action_log` creates a `TaskActionLog` record THEN the `tenant_id` field is NULL
1.3 WHEN `tenant_id` is NULL THEN the database raises `psycopg2.errors.NotNullViolation` error

**Frontend - Approval Workbench UI Issues:**
1.4 WHEN viewing the approval workbench THEN the "轨迹" (trace/timeline) section is displayed but should be removed
1.5 WHEN SLA overview shows tasks without due date THEN the display shows "无截止" text which should be removed
1.6 WHEN SLA overview displays status labels THEN the normal label is positioned next to warning-styled font, and warning label is positioned next to critical-styled font (label-font mismatch)

### Expected Behavior (Correct)

**Backend - TaskActionLog tenant_id Fix:**
2.1 WHEN `claim_task` is called THEN the system SHALL pass `tenant_id` to `_create_action_log`
2.2 WHEN `_create_action_log` creates a `TaskActionLog` record THEN the `tenant_id` field SHALL be set from the task's `tenant_id`
2.3 WHEN `tenant_id` is properly set THEN the database insert SHALL succeed without constraint violation

**Frontend - Approval Workbench UI Fix:**
2.4 WHEN viewing the approval workbench THEN the "轨迹" section SHALL NOT be displayed
2.5 WHEN SLA overview shows tasks without due date THEN the display SHALL NOT show "无截止" text
2.6 WHEN SLA overview displays status labels THEN each label SHALL be correctly paired with its corresponding font style (normal→success, warning→warning, critical→error, expired→error)

### Unchanged Behavior (Regression Prevention)

**Backend:**
3.1 WHEN other operations (release, perform_action, transfer, delegate) create action logs THEN the system SHALL CONTINUE TO work correctly with proper tenant_id handling
3.2 WHEN tasks are queried or listed THEN the system SHALL CONTINUE TO return correct task data

**Frontend:**
3.3 WHEN viewing the approval workbench THEN other sections (task list, SLA summary cards) SHALL CONTINUE TO display correctly
3.4 WHEN SLA badge shows valid status levels THEN the display SHALL CONTINUE TO work correctly