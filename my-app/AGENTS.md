# 项目概览

- **目标**：配合后端实现校园表单与审批前端，支持拖拽与 AI 生成
- **核心**：拖拽设计器；AI 表单生成；多场景互动看板；提交与审批管理
- **技术栈**：Vue 3、Vite、Vue Router、Pinia、Naive UI、Axios、ECharts
- **当前状态**：Alpha，审批与 Element 旧模块待替换补齐

## 目录树

```
├─ package.json【依赖与脚本】
├─ vite.config.ts⭐【构建与代理】
├─ tsconfig.json【TS基础配置】
├─ tsconfig.app.json【应用TS配置】
├─ tsconfig.node.json【Node声明配置】
├─ index.html【Vite入口页】
├─ .env.development【开发变量】
├─ .env.production【生产变量】
└─ src
   ├─ main.ts⭐🔥【应用入口】
   ├─ App.vue⭐🔥【全局壳层】
   ├─ style.css【全局样式】
   ├─ api
   │  ├─ ai.ts【AI接口】
   │  ├─ attachment.ts【附件接口】
   │  ├─ auth.ts【认证接口】
   │  ├─ form.ts【表单接口】
   │  ├─ submission.ts【提交接口】
   │  └─ tenant.ts【租户接口】
   ├─ components
   │  ├─ FormDesigner
   │  │  ├─ index.vue⭐🔥【设计器汇总】
   │  │  ├─ AIAssistant.vue🎯【AI助手面板】
   │  │  ├─ ComponentLibrary.vue【字段库】
   │  │  ├─ DesignCanvas.vue🎯【画布与拖拽】
   │  │  ├─ FieldPreview.vue【字段预览】
   │  │  ├─ FormPreview.vue【表单预览】
   │  │  ├─ FormSettings.vue【基础设置】
   │  │  ├─ LogicRuleEditor.vue【逻辑编辑】
   │  │  └─ PropertyPanel
   │  │     ├─ index.vue【属性面板】
   │  │     ├─ BasicConfig.vue🎯【基础配置】
   │  │     ├─ DefaultValueInput.vue【默认值控件】
   │  │     ├─ FormulaEditor.vue【公式配置】
   │  │     ├─ OptionsEditor.vue【选项编辑】
   │  │     ├─ PropsConfig.vue【属性配置】
   │  │     └─ ValidationConfig.vue【校验配置】
   │  ├─ FormRenderer
   │  │  └─ index.vue【渲染容器】
   │  └─ home
   │     ├─ DataDashboard.vue【数据看板】
   │     ├─ FlowCanvas.vue【流程画布】
   │     ├─ FlowPlayground.vue【流程互动】
   │     ├─ HeroNLGenerator.vue🎯【AI生成组件】
   │     ├─ QuickActions.vue【快捷入口】
   │     └─ ScenarioSelector.vue【场景选择】
   ├─ composables
   │  └─ useTokenMonitor.ts【令牌监控】
   ├─ constants
   │  ├─ errorCodes.ts【错误码表】
   │  ├─ fieldTemplates.ts【字段模板】
   │  ├─ fieldTypes.ts【字段枚举】
   │  └─ formulaFunctions.ts【公式函数】
   ├─ layout
   │  ├─ index.vue🎯【旧布局壳】
   │  └─ components
   │     ├─ SidebarItem.vue🎯【侧栏项】
   │     └─ TagsView.vue【标签栏】
   ├─ router
   │  ├─ guards.ts⭐【路由守卫】
   │  └─ index.ts⭐【路由表】
   ├─ stores
   │  ├─ auth.ts⭐【认证状态】
   │  ├─ formDesigner.ts⭐【设计器状态】
   │  ├─ homeInteractive.ts【首页互动】
   │  └─ tenant.ts⭐【租户状态】
   ├─ utils
   │  ├─ configTransfer.ts【配置缓存】
   │  ├─ formValidation.ts【表单校验】
   │  ├─ idGenerator.ts【ID生成】
   │  ├─ request.ts⭐【HTTP封装】
   │  └─ submission.ts【提交转换】
   ├─ views
   │  ├─ HomeView.vue【首页展示】
   │  ├─ approvals
   │  │  └─ ApprovalListView.vue【审批占位】
   │  ├─ auth
   │  │  ├─ LoginView.vue🎯【登录注册】
   │  │  └─ TenantSelect.vue🎯【租户选择】
   │  ├─ dashboard
   │  │  └─ index.vue【仪表板旧版】
   │  ├─ error
   │  │  ├─ 403.vue【403页面】
   │  │  └─ 404.vue【404页面】
   │  ├─ form
   │  │  ├─ Designer.vue【设计器页】
   │  │  ├─ Fill.vue🎯【表单填写】
   │  │  ├─ List.vue🎯【表单列表】
   │  │  └─ Preview.vue🎯【表单预览】
   │  ├─ forms
   │  │  └─ FormNewView.vue【创建占位】
   │  └─ submissions
   │     ├─ SubmissionDetailView.vue🎯【提交详情】
   │     └─ SubmissionListView.vue🎯【提交列表】
   ├─ types
   │  ├─ ai.ts【AI类型】
   │  ├─ api.ts【通用类型】
   │  ├─ attachment.ts【附件类型】
   │  ├─ auth.ts【认证类型】
   │  ├─ field.ts【字段类型】
   │  ├─ form.ts【表单类型】
   │  ├─ global.d.ts【全局声明】
   │  ├─ iconify.d.ts【Iconify声明】
   │  ├─ logic.ts【逻辑类型】
   │  ├─ schema.ts【Schema类型】
   │  ├─ submission.ts【提交类型】
   │  ├─ tenant.ts【租户类型】
   │  ├─ user.ts【用户类型】
   │  └─ vuedraggable.d.ts【拖拽声明】
   └─ env.d.ts【环境声明】
```

**文件索引(JSON Lines)**

```
BEGIN FILE INDEX JSON
{"path":".env.development","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"dev env vars"}
{"path":".env.production","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"prod env vars"}
{"path":"index.html","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"vite html"}
{"path":"package.json","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"deps scripts"}
{"path":"tsconfig.app.json","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"ts app conf"}
{"path":"tsconfig.json","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"root ts conf"}
{"path":"tsconfig.node.json","size":"S","core":false,"pkg":false,"role":"配置","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"node ts conf"}
{"path":"vite.config.ts","size":"S","core":true,"pkg":false,"role":"配置","exports":["default"],"deps":["vite","@vitejs/plugin-vue"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"vite config"}
{"path":"src/App.vue","size":"S","core":true,"pkg":true,"role":"入口","exports":["App"],"deps":["vue","naive-ui","vue-router"],"routes":[],"apis":[],"store":null,"naive":["NConfigProvider","NMessageProvider","NDialogProvider","NNotificationProvider","NGlobalStyle"],"desc":"app shell"}
{"path":"src/env.d.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["ImportMetaEnv","ImportMeta"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"env types"}
{"path":"src/main.ts","size":"S","core":true,"pkg":true,"role":"入口","exports":["pinia"],"deps":["vue","pinia","naive-ui"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"mount entry"}
{"path":"src/style.css","size":"S","core":false,"pkg":false,"role":"样式","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"global css"}
{"path":"src/vite-env.d.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"vite types"}
{"path":"src/api/ai.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["generateFormByAI","quickGenerateForm","advancedGenerateForm","getTaskStatus"],"deps":[],"routes":[],"apis":[{"method":"POST","url":"/api/v1/ai/generate-form"},{"method":"GET","url":"/api/v1/ai/task/:taskId"}],"store":null,"naive":[],"desc":"ai service"}
{"path":"src/api/attachment.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["uploadAttachment","getAttachment","deleteAttachment","downloadAttachment","default"],"deps":[],"routes":[],"apis":[{"method":"POST","url":"/api/v1/attachments/upload"},{"method":"GET","url":"/api/v1/attachments/:attachmentId"},{"method":"DELETE","url":"/api/v1/attachments/:attachmentId"},{"method":"GET","url":"/api/v1/attachments/:attachmentId/download"}],"store":null,"naive":[],"desc":"file service"}
{"path":"src/api/auth.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["login","refreshToken","refreshTokenByString","register","logout","getCurrentUser","getTenants","validateTenant","validateTenantById","default"],"deps":[],"routes":[],"apis":[{"method":"POST","url":"/api/v1/auth/login"},{"method":"POST","url":"/api/v1/auth/refresh"},{"method":"POST","url":"/api/v1/auth/register"},{"method":"POST","url":"/api/v1/auth/logout"},{"method":"GET","url":"/api/v1/auth/me"},{"method":"GET","url":"/api/v1/auth/tenants"},{"method":"POST","url":"/api/v1/auth/validate-tenant"}],"store":null,"naive":[],"desc":"auth service"}
{"path":"src/api/form.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["createForm","updateForm","publishForm","getFormDetail","listForms","deleteForm","cloneForm","listTemplates","createFromTemplate","default"],"deps":[],"routes":[],"apis":[{"method":"POST","url":"/api/v1/forms"},{"method":"PUT","url":"/api/v1/forms/:formId"},{"method":"POST","url":"/api/v1/forms/:formId/publish"},{"method":"GET","url":"/api/v1/forms/:formId"},{"method":"GET","url":"/api/v1/forms"},{"method":"DELETE","url":"/api/v1/forms/:formId"},{"method":"POST","url":"/api/v1/forms/:formId/clone"},{"method":"GET","url":"/api/v1/forms/templates"},{"method":"POST","url":"/api/v1/forms/from-template/:templateId"}],"store":null,"naive":[],"desc":"form service"}
{"path":"src/api/submission.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["createSubmission","updateSubmission","deleteSubmission","getSubmissionDetail","getSubmissionList","getSubmissionStatistics","saveDraft","getDraft","deleteDraft","exportSubmissions","getExportTask","default"],"deps":[],"routes":[],"apis":[{"method":"POST","url":"/api/v1/submissions"},{"method":"PUT","url":"/api/v1/submissions/:submissionId"},{"method":"DELETE","url":"/api/v1/submissions/:submissionId"},{"method":"GET","url":"/api/v1/submissions/:submissionId"},{"method":"GET","url":"/api/v1/submissions"},{"method":"GET","url":"/api/v1/submissions/statistics/:formId"},{"method":"POST","url":"/api/v1/submissions/drafts"},{"method":"GET","url":"/api/v1/submissions/drafts/:formId"},{"method":"DELETE","url":"/api/v1/submissions/drafts/:draftId"},{"method":"POST","url":"/api/v1/submissions/export"},{"method":"GET","url":"/api/v1/submissions/export/:taskId"}],"store":null,"naive":[],"desc":"sub service"}
{"path":"src/api/tenant.ts","size":"S","core":false,"pkg":false,"role":"服务","exports":["getTenantList","validateTenant"],"deps":[],"routes":[],"apis":[{"method":"GET","url":"/api/v1/auth/tenants"},{"method":"POST","url":"/api/v1/auth/validate-tenant"}],"store":null,"naive":[],"desc":"tenant svc"}
{"path":"src/components/FormDesigner/AIAssistant.vue","size":"S","core":false,"pkg":true,"role":"组件","exports":["AIAssistant"],"deps":["vue","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NAlert","NButton","NCollapse","NCollapseItem","NDivider","NDrawer","NDrawerContent","NForm","NFormItem","NIcon","NInput","NRadio","NRadioGroup","NSpace","NStatistic","NTag","NTooltip"],"desc":"ai drawer"}
{"path":"src/components/FormDesigner/ComponentLibrary.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["ComponentLibrary"],"deps":["@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"field lib"}
{"path":"src/components/FormDesigner/DesignCanvas.vue","size":"S","core":false,"pkg":true,"role":"组件","exports":["DesignCanvas"],"deps":["vue","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NTag"],"desc":"canvas ui"}
{"path":"src/components/FormDesigner/FieldPreview.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["FieldPreview"],"deps":["@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NCheckbox","NCheckboxGroup","NDatePicker","NDivider","NInput","NInputNumber","NRadio","NRadioGroup","NRate","NSelect","NSpace","NSwitch","NTimePicker","NUpload"],"desc":"field demo"}
{"path":"src/components/FormDesigner/FormPreview.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["FormPreview"],"deps":["vue","naive-ui"],"routes":[],"apis":[],"store":null,"naive":["NButton","NDivider","NForm","NFormItem","NSpace"],"desc":"preview core"}
{"path":"src/components/FormDesigner/FormSettings.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["FormSettings"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":["NDatePicker","NForm","NFormItem","NInput","NInputNumber","NRadio","NRadioGroup","NSpace","NSwitch"],"desc":"form base"}
{"path":"src/components/FormDesigner/index.vue","size":"M","core":false,"pkg":true,"role":"组件","exports":["FormDesigner"],"deps":["vue","vue-router","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NDivider","NDrawer","NDrawerContent","NIcon","NInput","NSpace","NTag"],"desc":"designer hub"}
{"path":"src/components/FormDesigner/LogicRuleEditor.vue","size":"M","core":false,"pkg":false,"role":"组件","exports":["LogicRuleEditor"],"deps":["vue","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NDivider","NForm","NFormItem","NInput","NRadio","NRadioGroup","NScrollbar","NSelect","NSpace","NSwitch"],"desc":"logic edit"}
{"path":"src/components/FormDesigner/PropertyPanel/BasicConfig.vue","size":"S","core":false,"pkg":true,"role":"组件","exports":["BasicConfig"],"deps":["vue","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NForm","NFormItem","NInput","NScrollbar","NSwitch","NTag"],"desc":"basic conf"}
{"path":"src/components/FormDesigner/PropertyPanel/DefaultValueInput.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["DefaultValueInput"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":["NCheckbox","NCheckboxGroup","NDatePicker","NInput","NInputNumber","NRadio","NRadioGroup","NRate","NSelect","NSpace","NSwitch","NTimePicker"],"desc":"default input"}
{"path":"src/components/FormDesigner/PropertyPanel/FormulaEditor.vue","size":"M","core":false,"pkg":false,"role":"组件","exports":["FormulaEditor"],"deps":["vue","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NCollapse","NCollapseItem","NInput","NSelect","NTag"],"desc":"formula edit"}
{"path":"src/components/FormDesigner/PropertyPanel/index.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["PropertyPanel"],"deps":["@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NTabPane","NTabs"],"desc":"panel root"}
{"path":"src/components/FormDesigner/PropertyPanel/OptionsEditor.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["OptionsEditor"],"deps":["vue","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NInput"],"desc":"options edit"}
{"path":"src/components/FormDesigner/PropertyPanel/PropsConfig.vue","size":"M","core":false,"pkg":false,"role":"组件","exports":["PropsConfig"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":["NForm","NFormItem","NInput","NInputNumber","NScrollbar","NSlider","NSwitch"],"desc":"props conf"}
{"path":"src/components/FormDesigner/PropertyPanel/ValidationConfig.vue","size":"M","core":false,"pkg":false,"role":"组件","exports":["ValidationConfig"],"deps":["vue","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NButton","NDivider","NForm","NFormItem","NInput","NInputNumber","NRadio","NRadioGroup","NScrollbar","NSpace"],"desc":"validate cfg"}
{"path":"src/components/FormRenderer/index.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["FormRenderer"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"form render"}
{"path":"src/components/home/DataDashboard.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["DataDashboard"],"deps":["vue","echarts"],"routes":[],"apis":[],"store":null,"naive":["NSkeleton","NTag"],"desc":"data board"}
{"path":"src/components/home/FlowCanvas.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["FlowCanvas"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"flow svg"}
{"path":"src/components/home/FlowPlayground.vue","size":"M","core":false,"pkg":false,"role":"组件","exports":["FlowPlayground"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":["NCheckbox","NNumberAnimation","NPopover","NSlider","NStatistic","NTag"],"desc":"flow play"}
{"path":"src/components/home/HeroNLGenerator.vue","size":"M","core":false,"pkg":true,"role":"组件","exports":["HeroNLGenerator"],"deps":["vue","vue-router","naive-ui","@vicons/ionicons5"],"routes":[],"apis":[],"store":null,"naive":["NAlert","NBadge","NButton","NDivider","NIcon","NInput","NProgress","NSpace","NStatistic","NTag"],"desc":"hero ai"}
{"path":"src/components/home/QuickActions.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["QuickActions"],"deps":["vue-router"],"routes":[],"apis":[],"store":null,"naive":["NBadge"],"desc":"quick cards"}
{"path":"src/components/home/ScenarioSelector.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["ScenarioSelector"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"scenario sel"}
{"path":"src/composables/useTokenMonitor.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["useTokenMonitor"],"deps":["vue"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"token watch"}
{"path":"src/constants/errorCodes.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["ERROR_CODES","AUTH_ERROR_CODES","PERMISSION_ERROR_CODES","VALIDATION_ERROR_CODES","NOT_FOUND_ERROR_CODES","BUSINESS_ERROR_CODES","RATE_LIMIT_ERROR_CODES","DATABASE_ERROR_CODES","EXTERNAL_SERVICE_ERROR_CODES","SYSTEM_ERROR_CODES","ERROR_MESSAGES","getErrorMessage","isAuthError","isPermissionError","isSystemError","isValidationError"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"error codes"}
{"path":"src/constants/fieldTemplates.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["FIELD_TEMPLATES"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"field temps"}
{"path":"src/constants/fieldTypes.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["FieldType","FIELD_GROUPS","FIELD_TYPE_LABELS","FIELD_TYPE_ICONS"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"field types"}
{"path":"src/constants/formulaFunctions.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["FORMULA_FUNCTIONS","FORMULA_SYNTAX_HELP"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"formula help"}
{"path":"src/layout/index.vue","size":"S","core":false,"pkg":true,"role":"组件","exports":["LayoutIndex"],"deps":["vue","vue-router","element-plus"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"layout shell"}
{"path":"src/layout/components/SidebarItem.vue","size":"S","core":false,"pkg":true,"role":"组件","exports":["SidebarItem"],"deps":["vue","vue-router","path-browserify"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"sidebar item"}
{"path":"src/layout/components/TagsView.vue","size":"S","core":false,"pkg":false,"role":"组件","exports":["TagsView"],"deps":["vue","vue-router"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"tags view"}
{"path":"src/router/guards.ts","size":"S","core":true,"pkg":false,"role":"路由","exports":["setGuardMessageInstance","setupRouterGuards"],"deps":["vue-router","nprogress"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"route guards"}
{"path":"src/router/index.ts","size":"S","core":true,"pkg":false,"role":"路由","exports":["default"],"deps":["vue-router"],"routes":[{"name":"TenantSelect","path":"/tenant-select"},{"name":"Login","path":"/login"},{"name":"NotFound","path":"/404"},{"name":"Forbidden","path":"/403"},{"name":"Home","path":"/"},{"name":"Form","path":"/form"},{"name":"FormList","path":"/form/list"},{"name":"FormDesigner","path":"/form/designer"},{"name":"FormPreview","path":"/form/:id/preview"},{"name":"FormFill","path":"/form/:id/fill"},{"name":"SubmissionList","path":"/submissions"},{"name":"SubmissionDetail","path":"/submissions/:id"},{"name":"ApprovalList","path":"/approvals"},{"name":null,"path":"/:pathMatch(.*)*"}],"apis":[],"store":null,"naive":[],"desc":"router map"}
{"path":"src/stores/auth.ts","size":"M","core":true,"pkg":false,"role":"状态","exports":["useAuthStore"],"deps":["pinia"],"routes":[],"apis":[],"store":{"id":"auth","state":["userInfo","userBasicInfo","accessToken","refreshToken","tokenExpiry","refreshPromise"],"actions":["saveTokens","clearAuth","initTokens","login","register","refreshAccessToken","getUserInfo","logout","getAccessToken","checkAuth","hasRole","hasPermission","updateAccessToken","updateRefreshToken"]},"naive":[],"desc":"auth store"}
{"path":"src/stores/formDesigner.ts","size":"S","core":true,"pkg":false,"role":"状态","exports":["useFormDesignerStore"],"deps":["pinia","vue"],"routes":[],"apis":[],"store":{"id":"formDesigner","state":["formId","formName","formCategory","accessMode","allowEdit","maxEditCount","submitDeadline","fields","selectedFieldId","uiSchema","logicSchema"],"actions":["addField","updateField","deleteField","moveField","selectField","clearSelection","getFormConfig","loadFormConfig","reset"]},"naive":[],"desc":"design store"}
{"path":"src/stores/homeInteractive.ts","size":"M","core":false,"pkg":false,"role":"状态","exports":["useHomeInteractive"],"deps":["pinia","vue"],"routes":[],"apis":[],"store":{"id":"homeInteractive","state":["scenario","formSchema","controls","flowData","autoDecision","etaMinutes","scenarioConfig"],"actions":["changeScenario","updateControl","generateFormFromNL","computeFlow","updateMetrics"]},"naive":[],"desc":"home store"}
{"path":"src/stores/tenant.ts","size":"S","core":true,"pkg":false,"role":"状态","exports":["useTenantStore"],"deps":["pinia","vue"],"routes":[],"apis":[],"store":{"id":"tenant","state":["currentTenant","tenantList","loading","tenantId","tenantName","hasTenant"],"actions":["fetchTenantList","selectTenant","validateCurrentTenant","clearTenant","initTenant"]},"naive":[],"desc":"tenant store"}
{"path":"src/types/ai.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["ThinkingType","AIFormGenerateRequest","AIFormGenerateResponse","FormConfig","FormSchema","FormField","FieldType","FieldValidation","UISchema","UIRow","LogicSchema","LogicRule","LogicAction"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"ai types"}
{"path":"src/types/api.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["Response","PageResponse","PageParams","BatchOperationResult","UploadResponse"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"api types"}
{"path":"src/types/attachment.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["AttachmentInfo"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"file types"}
{"path":"src/types/auth.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["LoginRequest","LoginUserInfo","LoginResponse","TokenResponse","RefreshTokenRequest","RegisterRequest","RegisterResponse","TenantInfo","ValidateTenantRequest","ValidateTenantResponse"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"auth types"}
{"path":"src/types/field.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["FieldType","FormField","FieldValidation","SelectOption","TextFieldProps","NumberFieldProps","SelectFieldProps","DateFieldProps","UploadFieldProps","CalculatedFieldProps"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"field types"}
{"path":"src/types/form.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["FormStatus","AccessMode","FormConfig","FormCreateRequest","FormUpdateRequest","FormResponse"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"form types"}
{"path":"src/types/global.d.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"global dts"}
{"path":"src/types/iconify.d.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"iconify dts"}
{"path":"src/types/logic.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["LogicRule","LogicTrigger","LogicCondition","ConditionOperator","LogicAction","ActionType","LogicSchema"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"logic types"}
{"path":"src/types/schema.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["FormSchema","UISchema","FormLayoutSettings","FormRow","FormGroup"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"schema types"}
{"path":"src/types/submission.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["SubmissionData","SubmissionBase","SubmissionDraftData","SubmissionDraft","CreateSubmissionRequest","UpdateSubmissionRequest","MessageResponse","SubmissionListItem","SubmissionDetail","SnapshotData","SubmissionQueryParams","SubmissionListResponse","SubmissionStatistics","SubmissionExportRequest","SubmissionExportSyncResponse","SubmissionExportAsyncResponse","SubmissionExportTask"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"submit types"}
{"path":"src/types/tenant.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["Tenant"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"tenant type"}
{"path":"src/types/user.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":["UserBase","UserCreate","UserUpdate","UserInDB","UserResponse","UserProfile","UserInfo","PasswordChange","UserBasicInfo"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"user types"}
{"path":"src/types/vuedraggable.d.ts","size":"S","core":false,"pkg":false,"role":"类型","exports":[],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"drag dts"}
{"path":"src/utils/configTransfer.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["ConfigTransfer"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"config cache"}
{"path":"src/utils/formValidation.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["FormValidation"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"form check"}
{"path":"src/utils/idGenerator.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["generateFieldId","generateRuleId","generateGroupId"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"id helpers"}
{"path":"src/utils/request.ts","size":"M","core":true,"pkg":false,"role":"工具","exports":["setNaiveUIInstances","service","requestQueue","HttpRequest","CustomAxiosRequestConfig","PendingRequest","Response","PageResponse","http","request"],"deps":["axios","nprogress"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"http client"}
{"path":"src/utils/submission.ts","size":"S","core":false,"pkg":false,"role":"工具","exports":["transformToBackend","transformToFrontend"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"submit utils"}
{"path":"src/views/HomeView.vue","size":"M","core":false,"pkg":false,"role":"页面","exports":["HomeView"],"deps":["vue","vue-router"],"routes":[],"apis":[],"store":null,"naive":["NButton","NIcon","NSpace"],"desc":"home page"}
{"path":"src/views/approvals/ApprovalListView.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["ApprovalListView"],"deps":[],"routes":[],"apis":[],"store":null,"naive":["NBadge","NButton","NCard","NEmpty","NPageHeader"],"desc":"approval stub"}
{"path":"src/views/auth/LoginView.vue","size":"M","core":false,"pkg":true,"role":"页面","exports":["LoginView"],"deps":["vue","vue-router","naive-ui"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"login page"}
{"path":"src/views/auth/TenantSelect.vue","size":"M","core":false,"pkg":true,"role":"页面","exports":["TenantSelect"],"deps":["vue","vue-router","element-plus"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"tenant page"}
{"path":"src/views/dashboard/index.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["DashboardIndex"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"dashboard"}
{"path":"src/views/error/403.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["Error403"],"deps":["vue-router"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"error 403"}
{"path":"src/views/error/404.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["Error404"],"deps":["vue-router"],"routes":[],"apis":[],"store":null,"naive":[],"desc":"error 404"}
{"path":"src/views/form/Designer.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["FormDesignerPage"],"deps":[],"routes":[],"apis":[],"store":null,"naive":[],"desc":"designer page"}
{"path":"src/views/form/Fill.vue","size":"S","core":false,"pkg":true,"role":"页面","exports":["FormFill"],"deps":["vue","vue-router","naive-ui"],"routes":[],"apis":[],"store":null,"naive":["NCard","NSpin"],"desc":"fill page"}
{"path":"src/views/form/List.vue","size":"M","core":false,"pkg":true,"role":"页面","exports":["FormList"],"deps":["vue","vue-router","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NPageHeader","NSpace","NButton","NIcon","NCard","NInput","NSelect","NDataTable","NModal","NSpin","NForm","NFormItem","NTag"],"desc":"form list"}
{"path":"src/views/form/Preview.vue","size":"S","core":false,"pkg":true,"role":"页面","exports":["FormPreviewPage"],"deps":["vue","vue-router","naive-ui","@iconify/vue"],"routes":[],"apis":[],"store":null,"naive":["NPageHeader","NSpace","NButton","NCard","NSpin"],"desc":"form preview"}
{"path":"src/views/forms/FormNewView.vue","size":"S","core":false,"pkg":false,"role":"页面","exports":["FormNewView"],"deps":["naive-ui"],"routes":[],"apis":[],"store":null,"naive":["NPageHeader","NCard","NEmpty","NSpace","NButton"],"desc":"form new"}
{"path":"src/views/submissions/SubmissionDetailView.vue","size":"S","core":false,"pkg":true,"role":"页面","exports":["SubmissionDetailView"],"deps":["vue","vue-router","naive-ui"],"routes":[],"apis":[],"store":null,"naive":["NSpin","NPageHeader","NAlert","NGrid","NGi","NCard","NDescriptions","NDescriptionsItem","NTag","NSpace","NDataTable","NButton","NA","NCollapse","NCollapseItem","NCode"],"desc":"sub detail"}
{"path":"src/views/submissions/SubmissionListView.vue","size":"M","core":false,"pkg":true,"role":"页面","exports":["SubmissionListView"],"deps":["vue","vue-router","naive-ui","@vicons/ionicons5"],"routes":[],"apis":[],"store":null,"naive":["NSpin","NPageHeader","NButton","NCard","NForm","NFormItem","NInputNumber","NSelect","NInput","NSpace","NIcon","NDataTable","NPagination","NModal","NTag"],"desc":"sub list"}
END FILE INDEX JSON
```
快捷索引
- 路由：Home → / → src/views/HomeView.vue；FormDesigner → /form/designer → src/views/form/Designer.vue；SubmissionList → /submissions → src/views/submissions/SubmissionListView.vue；ApprovalList → /approvals → src/views/approvals/ApprovalListView.vue
- 服务：POST /api/v1/forms → src/api/form.ts → createForm；GET /api/v1/submissions → src/api/submission.ts → getSubmissionList；POST /api/v1/ai/generate-form → src/api/ai.ts → generateFormByAI
- Store：auth → src/stores/auth.ts → state userInfo/accessToken 等，actions login/checkAuth/refreshAccessToken；tenant → src/stores/tenant.ts → state currentTenant/tenantList，actions fetchTenantList/validateCurrentTenant；formDesigner → src/stores/formDesigner.ts → state fields/uiSchema，actions addField/reset

编码规范
- 命名遵循：页面/组件 PascalCase.vue，组合式函数 useXxx.ts，Pinia 仓库 *.ts 保留 useXxxStore，路由 path 使用 kebab-case
- 风格统一 <script setup lang="ts">，组件避免副作用，跨组件通信优先 Pinia；Naive 组件采用插件全量注册，必要时显式引入图标或函数
- 路由新增请保持懒加载 import 且在 src/router/index.ts 中集中管理，并根据 guards 需要补充 meta
- 请求示例：
  ```ts
  import { listForms } from '@/api/form'
  
  const loadForms = async () => {
    const { data } = await listForms({ page: 1, size: 10 })
    console.log(data.items)
  }
  ```

快速参考
- 常用命令：`npm install` 安装依赖；`npm run dev` 启动开发；`npm run build` 产出构建；`npm run preview` 本地预览；`npm run type-check`/`npm run lint` 静态检查
- 核心配置：vite.config.ts（构建与代理）、tsconfig*.json（TS 约束）、.env.development / .env.production（环境变量）
- 环境变量：VITE_APP_TITLE（应用标题），VITE_API_BASE_URL（后端地址），VITE_APP_ENV（环境标记）
- API 前缀：所有接口使用 /api/v1，开发态通过 vite.config.ts 将 /api 代理到 VITE_API_BASE_URL；静态资源从 public 直出
