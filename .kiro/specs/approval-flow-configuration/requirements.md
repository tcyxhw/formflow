# Requirements Document

## Introduction

本文档定义了审批流程配置功能的需求。该功能允许表单创建者在表单发布前配置审批流程，确保流程的完整性和正确性。审批流程采用有向图模型，包含节点（开始、审批、条件、结束）和连线，并在发布前进行严格的拓扑和业务规则校验。

## Glossary

- **Form_Creator**: 创建表单的用户，拥有配置该表单审批流程的权限
- **Flow_Definition**: 审批流程定义，关联到特定表单，包含节点和连线的完整配置
- **Flow_Node**: 流程节点，包括开始节点、审批节点、条件节点、结束节点
- **Flow_Route**: 流程连线，连接两个节点，定义流程的流转路径
- **Flow_Draft**: 流程草稿，用于保存未发布的流程配置
- **Flow_Snapshot**: 流程快照，记录已发布流程的历史版本
- **Start_Node**: 开始节点，流程的唯一入口点
- **End_Node**: 结束节点，流程的出口点，可以有多个
- **Approval_Node**: 审批节点，需要配置审批人的节点
- **Condition_Node**: 条件节点，根据条件分支的节点
- **Flow_Configurator**: 流程配置器，前端可视化流程设计组件
- **Form_Service**: 表单服务，负责表单的创建、发布等操作
- **Flow_Service**: 流程服务，负责流程的保存、发布、校验等操作
- **Form_List**: 表单列表页面，展示用户的表单并提供操作入口
- **Form_Designer**: 表单设计器页面，用于设计表单结构

## Requirements

### Requirement 1: 自动创建流程定义

**User Story:** 作为表单创建者，我希望在创建表单时自动创建关联的流程定义，以便后续配置审批流程。

#### Acceptance Criteria

1. WHEN Form_Creator creates a new form, THE Form_Service SHALL create an associated Flow_Definition
2. THE Flow_Definition SHALL be initialized with the form_id and tenant_id from the form
3. THE Flow_Definition SHALL be created in draft status
4. THE Flow_Definition SHALL have an empty node and route configuration initially


### Requirement 2: 流程配置路由

**User Story:** 作为表单创建者，我希望能够通过路由访问流程配置器，以便设计审批流程。

#### Acceptance Criteria

1. THE Frontend_Router SHALL define a route path for the Flow_Configurator component
2. THE route SHALL accept form_id as a URL parameter
3. WHEN Form_Creator navigates to the flow configuration route, THE Frontend_Router SHALL render the Flow_Configurator component
4. THE route SHALL be protected and require authentication

### Requirement 3: 表单列表流程配置入口

**User Story:** 作为表单创建者，我希望在表单列表中看到"配置流程"按钮，以便快速进入流程配置。

#### Acceptance Criteria

1. WHEN Form_Creator views Form_List, THE Form_List SHALL display a "配置流程" action button for each form
2. WHERE the form is in draft status, THE action button SHALL be enabled
3. WHERE the form is published, THE action button SHALL be disabled or hidden
4. WHEN Form_Creator clicks the "配置流程" button, THE Form_List SHALL navigate to the Flow_Configurator with the form_id

### Requirement 4: 表单设计器流程配置引导

**User Story:** 作为表单创建者，我希望在表单设计器中看到流程配置提示，以便了解下一步需要配置审批流程。

#### Acceptance Criteria

1. WHEN Form_Creator saves a form in Form_Designer, THE Form_Designer SHALL display a prompt about configuring the approval flow
2. THE prompt SHALL include a link or button to navigate to the Flow_Configurator
3. THE prompt SHALL explain that flow configuration is required before publishing
4. WHEN Form_Creator clicks the flow configuration link, THE Form_Designer SHALL navigate to the Flow_Configurator


### Requirement 5: 流程配置权限控制

**User Story:** 作为系统管理员，我希望只有表单创建者可以配置流程，以便保护流程配置的安全性。

#### Acceptance Criteria

1. WHEN a user attempts to access the Flow_Configurator, THE Flow_Service SHALL verify that the user is the Form_Creator
2. IF the user is not the Form_Creator, THEN THE Flow_Service SHALL return an authorization error
3. THE Flow_Configurator SHALL display an error message when authorization fails
4. THE tenant_id SHALL be validated to ensure cross-tenant access is prevented

### Requirement 6: 流程节点唯一性校验

**User Story:** 作为表单创建者，我希望系统确保流程有且只有一个开始节点，以便流程有明确的入口。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that exactly one Start_Node exists
2. IF zero Start_Nodes exist, THEN THE Flow_Service SHALL return a validation error with message "流程必须有一个开始节点"
3. IF more than one Start_Node exists, THEN THE Flow_Service SHALL return a validation error with message "流程只能有一个开始节点"
4. THE validation SHALL occur before any flow data is persisted

### Requirement 7: 流程结束节点校验

**User Story:** 作为表单创建者,我希望系统确保流程至少有一个结束节点，以便流程有明确的出口。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that at least one End_Node exists
2. IF zero End_Nodes exist, THEN THE Flow_Service SHALL return a validation error with message "流程必须至少有一个结束节点"
3. THE validation SHALL count all nodes with type "end"
4. THE validation SHALL occur before any flow data is persisted


### Requirement 8: 审批节点存在性校验

**User Story:** 作为表单创建者，我希望系统确保流程至少有一个审批节点，以便流程能够执行审批操作。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that at least one Approval_Node exists
2. IF zero Approval_Nodes exist, THEN THE Flow_Service SHALL return a validation error with message "流程必须至少有一个审批节点"
3. THE validation SHALL count all nodes with type "approval"
4. THE validation SHALL occur before any flow data is persisted

### Requirement 9: 节点出边校验

**User Story:** 作为表单创建者，我希望系统确保每个非结束节点都有出边，以便流程能够继续流转。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that each non-End_Node has at least one outgoing Flow_Route
2. IF a non-End_Node has zero outgoing routes, THEN THE Flow_Service SHALL return a validation error with the node_id and message "节点必须有出边"
3. THE validation SHALL iterate through all Flow_Nodes except End_Nodes
4. THE validation SHALL occur before any flow data is persisted

### Requirement 10: 节点入边校验

**User Story:** 作为表单创建者，我希望系统确保每个非开始节点都有入边，以便节点能够被到达。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that each non-Start_Node has at least one incoming Flow_Route
2. IF a non-Start_Node has zero incoming routes, THEN THE Flow_Service SHALL return a validation error with the node_id and message "节点必须有入边"
3. THE validation SHALL iterate through all Flow_Nodes except Start_Nodes
4. THE validation SHALL occur before any flow data is persisted


### Requirement 11: 条件节点分支校验

**User Story:** 作为表单创建者，我希望系统确保条件节点至少有两条出边，以便条件分支能够正常工作。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that each Condition_Node has at least two outgoing Flow_Routes
2. IF a Condition_Node has fewer than two outgoing routes, THEN THE Flow_Service SHALL return a validation error with the node_id and message "条件节点必须至少有两条分支"
3. THE validation SHALL count outgoing routes for nodes with type "condition"
4. THE validation SHALL occur before any flow data is persisted

### Requirement 12: 审批节点配置校验

**User Story:** 作为表单创建者，我希望系统确保每个审批节点都配置了审批人，以便审批任务能够分配。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL validate that each Approval_Node has approver configuration
2. IF an Approval_Node has no approver configuration, THEN THE Flow_Service SHALL return a validation error with the node_id and message "审批节点必须配置审批人"
3. THE validation SHALL check the node_config field for approver_type and approver_ids
4. THE validation SHALL occur before any flow data is persisted

### Requirement 13: 流程可达性校验

**User Story:** 作为表单创建者，我希望系统确保从开始节点能够到达结束节点，以便流程能够正常完成。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL perform a graph traversal from the Start_Node
2. THE Flow_Service SHALL verify that at least one End_Node is reachable from the Start_Node
3. IF no End_Node is reachable, THEN THE Flow_Service SHALL return a validation error with message "流程不可达：无法从开始节点到达结束节点"
4. THE validation SHALL use breadth-first search or depth-first search algorithm


### Requirement 14: 流程环检测

**User Story:** 作为表单创建者，我希望系统检测流程中的死循环，以便避免流程无法终止。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a flow, THE Flow_Service SHALL detect cycles in the flow graph
2. THE Flow_Service SHALL use cycle detection algorithm to identify strongly connected components
3. IF a cycle is detected that does not include an End_Node, THEN THE Flow_Service SHALL return a validation error with message "流程存在死循环"
4. THE validation SHALL allow cycles that include End_Nodes as valid exit paths

### Requirement 15: 表单发布前流程校验

**User Story:** 作为表单创建者，我希望在发布表单前系统校验流程配置，以便确保流程的完整性。

#### Acceptance Criteria

1. WHEN Form_Creator attempts to publish a form, THE Form_Service SHALL verify that the associated Flow_Definition is published
2. IF the Flow_Definition is not published, THEN THE Form_Service SHALL return a validation error with message "表单发布前必须先配置并发布审批流程"
3. THE Form_Service SHALL check the Flow_Definition status field
4. THE validation SHALL occur before the form status is changed to published

### Requirement 16: 流程草稿保存

**User Story:** 作为表单创建者，我希望能够保存流程草稿，以便在未完成配置时保留进度。

#### Acceptance Criteria

1. WHEN Form_Creator saves flow configuration in Flow_Configurator, THE Flow_Service SHALL create or update a Flow_Draft
2. THE Flow_Draft SHALL store the complete node and route configuration as JSON
3. THE Flow_Service SHALL not perform validation when saving drafts
4. WHEN Form_Creator reopens the Flow_Configurator, THE Flow_Service SHALL load the latest Flow_Draft


### Requirement 17: 流程发布与快照

**User Story:** 作为表单创建者，我希望发布流程时创建快照，以便保留流程的历史版本。

#### Acceptance Criteria

1. WHEN Form_Creator publishes a flow, THE Flow_Service SHALL perform all validation rules (Requirements 6-14)
2. IF all validations pass, THEN THE Flow_Service SHALL create a Flow_Snapshot with the current configuration
3. THE Flow_Service SHALL update the Flow_Definition status to published
4. THE Flow_Service SHALL increment the version number in the Flow_Snapshot

### Requirement 18: 流程配置器节点操作

**User Story:** 作为表单创建者，我希望在流程配置器中添加、删除、编辑节点，以便设计流程结构。

#### Acceptance Criteria

1. WHEN Form_Creator drags a node from the node panel, THE Flow_Configurator SHALL add the node to the canvas
2. WHEN Form_Creator clicks a node, THE Flow_Configurator SHALL display the node properties panel
3. WHEN Form_Creator deletes a node, THE Flow_Configurator SHALL remove the node and its connected routes
4. THE Flow_Configurator SHALL support node types: start, approval, condition, end

### Requirement 19: 流程配置器连线操作

**User Story:** 作为表单创建者，我希望在流程配置器中连接节点，以便定义流程路径。

#### Acceptance Criteria

1. WHEN Form_Creator drags from a node's output port to another node's input port, THE Flow_Configurator SHALL create a Flow_Route
2. THE Flow_Configurator SHALL visually render the route as an arrow or line
3. WHEN Form_Creator deletes a route, THE Flow_Configurator SHALL remove the connection
4. THE Flow_Configurator SHALL prevent creating routes from End_Nodes

