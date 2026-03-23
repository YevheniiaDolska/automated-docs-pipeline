# Architecture overview

Auto-generated architecture diagram from documentation cross-references.

```mermaid
graph TD
    subgraph Concept
        Concepts["Concepts"]
        Core_components["Core components"]
        Why_this_improves_documentatio["Why this improves documentation quality"]
        Data_model["Data model"]
        Operational_flow["Operational flow"]
        RAG_integration_contract["RAG integration contract"]
        Advanced_retrieval_pipeline["Advanced retrieval pipeline"]
        Security_and_governance["Security and governance"]
        How_the_workflow_execution_mod["How the workflow execution model works"]
        Data_structure_between_nodes["Data structure between nodes"]
        Execution_flow["Execution flow"]
        Execution_modes["Execution modes"]
        Error_handling["Error handling"]
        Key_implications_for_documenta["Key implications for documentation writers"]
        Related["Related"]
        Documentation_Pipeline_Demo["Documentation Pipeline Demo"]
        What_this_demo_shows["What this demo shows"]
        Browse_by_type["Browse by type"]
        Browse_by_tag["Browse by tag"]
    end
    subgraph How To
        Where_smart_merge_runs["Where smart-merge runs"]
        Merge_rules["Merge rules"]
        Where_reviewer_sees_required_e["Where reviewer sees required edits"]
    end
    subgraph Reference
        Overview["Overview"]
        Features["Features"]
        Usage["Usage"]
        GitHub_Actions["GitHub Actions"]
        Configuration["Configuration"]
        Validation_Rules["Validation Rules"]
        Lifecycle_Management["Lifecycle Management"]
        Search_Ranking_Factors["Search Ranking Factors"]
        Monitoring["Monitoring"]
        Best_Practices["Best Practices"]
        Troubleshooting["Troubleshooting"]
        Integration_with_Other_Tools["Integration with Other Tools"]
        Next_steps["Next steps"]
        How_to_Use_Variables["How to Use Variables"]
        Cloud_specific_Instructions["Cloud-specific Instructions"]
        Self_hosted_Instructions["Self-hosted Instructions"]
        Available_Variables["Available Variables"]
        Setup_Requirements["Setup Requirements"]
        Adding_New_Variables["Adding New Variables"]
        Examples["Examples"]
        Prerequisites["Prerequisites"]
        Limits["Limits"]
        Support["Support"]
        Variable_Categories_Reference["Variable Categories Reference"]
        Top_level_Keys["Top-level Keys"]
        Channels["Channels"]
        Interactive_AsyncAPI_Tester["Interactive AsyncAPI Tester"]
        Operations["Operations"]
        Interactive_GraphQL_Playground["Interactive GraphQL Playground"]
        Service_Methods["Service Methods"]
        Interactive_gRPC_Tester["Interactive gRPC Tester"]
        Notes["Notes"]
        Channels_Events["Channels/Events"]
        Interactive_WebSocket_Tester["Interactive WebSocket Tester"]
        1__Core_promise["1. Core promise"]
        2__One_time_setup__you_do_this["2. One-time setup (you do this)"]
        3__Weekly_automation__no_manua["3. Weekly automation (no manual commands)"]
        4__Human_role["4. Human role"]
        5__Operator_manual_checks_afte["5. Operator manual checks after setup"]
        6__Licensing["6. Licensing"]
        7__Plan_packaging["7. Plan packaging"]
        8__What_to_say_in_sales_calls["8. What to say in sales calls"]
        9__Compatibility_mode["9. Compatibility mode"]
        10__Deep_references["10. Deep references"]
        _______________["Главное правило"]
        ______________________________["Что именно вы настраиваете (и где)"]
        ______________["Команда сборки"]
        ________________________["Как это ставится клиенту"]
        _________________gitignore____["Что добавить в `.gitignore` клиента"]
        RAG_knowledge_________________["RAG/knowledge без ручных запусков"]
        ___________________["Два простых примера"]
        Supported_protocols__core_5_["Supported protocols (core-5)"]
        Unified_stage_flow["Unified stage flow"]
        Engine_and_adapters["Engine and adapters"]
        Protocol_specific_validators["Protocol-specific validators"]
        Regression["Regression"]
        Docs___publish["Docs + publish"]
        Test_assets_and_smart_merge["Test assets and smart-merge"]
        Advanced_RAG_retrieval_pipelin["Advanced RAG retrieval pipeline"]
        Template_and_snippet_parity["Template and snippet parity"]
        How_to_enable_any_capability_f["How to enable any capability for a client"]
        Direct_CLI_entry_points__not_e["Direct CLI entry points (not exposed as npm scripts)"]
        Multi_protocol_contract_pipeli["Multi-protocol contract pipeline"]
        Test_assets_generation_and_sma["Test assets generation and smart merge"]
        Quality_checks__32_automated_["Quality checks (32 automated)"]
        RAG_retrieval_pipeline["RAG retrieval pipeline"]
        Public_docs_auditor_and_execut["Public docs auditor and executive PDF"]
        API_first_external_sandbox_not["API-first external sandbox note"]
        PR_auto_doc_workflow_capabilit["PR auto-doc workflow capability"]
        Templates["Templates"]
        Policy_Packs["Policy Packs"]
        Knowledge_Modules["Knowledge Modules"]
        Docker_Compose_Profiles["Docker Compose Profiles"]
        1__Feature_matrix["1. Feature matrix"]
        2__Default_plan_presets["2. Default plan presets"]
        3__How_to_apply_a_plan_for_a_c["3. How to apply a plan for a client"]
        4__License_enforcement["4. License enforcement"]
        5__Plan_upgrade_path["5. Plan upgrade path"]
        1__Client_identity["1. Client identity"]
        2__Bundle_packaging["2. Bundle packaging"]
        3__LLM_instruction_packaging["3. LLM instruction packaging"]
        4__Automation_schedule__weekly["4. Automation schedule (weekly)"]
        5__Runtime_behavior["5. Runtime behavior"]
        6__API_first_configuration__on["6. API-first configuration (one branch, not the whole product)"]
        7__Module_switches["7. Module switches"]
        8__Universal_tasks__core_UTP__["8. Universal tasks (core UTP, not optional extras)"]
        9__Integrations__single_contro["9. Integrations (single control point)"]
        9__Private_tuning["9. Private tuning"]
        10__Licensing["10. Licensing"]
        11__Legal_labeling["11. Legal labeling"]
        12__Flow_presets__copy_paste_["12. Flow presets (copy-paste)"]
        9__Fully_automated_RAG_knowled["9. Fully automated RAG/knowledge flow"]
        Provider_options["Provider options"]
        Configure_this_page["Configure this page"]
        Playground["Playground"]
        Security_guidance["Security guidance"]
        Old_Webhook_API["Old Webhook API"]
        Example_Code["Example Code"]
        Reference["Reference"]
        Included_modules["Included modules"]
        Generated_docs_pages["Generated docs pages"]
        Generated_bundle_outputs["Generated bundle outputs"]
        Retrieval_artifact["Retrieval artifact"]
        Source_of_truth["Source of truth"]
        Validation_commands["Validation commands"]
        Related_pages["Related pages"]
        Zero_client_data_guarantee["Zero client data guarantee"]
        Complete_outgoing_request_inve["Complete outgoing request inventory"]
        Requests_the_pipeline_never_ma["Requests the pipeline never makes"]
        How_to_audit_the_pipeline_your["How to audit the pipeline yourself"]
        Machine_fingerprint_details["Machine fingerprint details"]
        Capability_pack_contents["Capability pack contents"]
        Summary_of_data_flow["Summary of data flow"]
        Webhook_node_reference["Webhook node reference"]
        Parameters["Parameters"]
        Authentication_options["Authentication options"]
        URLs["URLs"]
        Output["Output"]
        Smoke_checked_examples["Smoke-checked examples"]
        Environment_variables["Environment variables"]
        Start_a_sandbox_endpoint["Start a sandbox endpoint"]
        Playground_embed["Playground embed"]
        Multi_language_request_example["Multi-language request examples"]
        What_this_validates["What this validates"]
        Input_artifact_location["Input artifact location"]
        How_the_pipeline_uses_this_inp["How the pipeline uses this input"]
        Notes_format__demo_excerpt_["Notes format (demo excerpt)"]
        Browse_documentation_by_tag["Browse documentation by tag"]
    end
    Overview --> Concepts
    Overview --> Documentation_Pipeline_Demo
    Overview --> Reference
    Overview --> Generated_docs_pages
    How_to_Use_Variables --> Concepts
    How_to_Use_Variables --> Documentation_Pipeline_Demo
    How_to_Use_Variables --> Reference
    How_to_Use_Variables --> Generated_docs_pages
    Core_components --> How_the_workflow_execution_mod
    How_the_workflow_execution_mod --> Concepts
    How_the_workflow_execution_mod --> Documentation_Pipeline_Demo
    How_the_workflow_execution_mod --> Reference
    How_the_workflow_execution_mod --> Generated_docs_pages
    Documentation_Pipeline_Demo --> Concepts
    Documentation_Pipeline_Demo --> Reference
    Documentation_Pipeline_Demo --> Browse_documentation_by_tag
    Provider_options --> Concepts
    Provider_options --> Documentation_Pipeline_Demo
    Provider_options --> Reference
    Provider_options --> Generated_docs_pages
    Old_Webhook_API --> Concepts
    Old_Webhook_API --> Documentation_Pipeline_Demo
    Old_Webhook_API --> Reference
    Old_Webhook_API --> Generated_docs_pages
    Zero_client_data_guarantee --> Concepts
    Zero_client_data_guarantee --> Documentation_Pipeline_Demo
    Zero_client_data_guarantee --> Reference
    Zero_client_data_guarantee --> Generated_docs_pages
    Start_a_sandbox_endpoint --> Input_artifact_location
    Start_a_sandbox_endpoint --> Concepts
    Start_a_sandbox_endpoint --> Documentation_Pipeline_Demo
    Start_a_sandbox_endpoint --> Reference
    Start_a_sandbox_endpoint --> Generated_docs_pages
    Input_artifact_location --> Provider_options
    Input_artifact_location --> Start_a_sandbox_endpoint
    Browse_documentation_by_tag --> Concepts
    Browse_documentation_by_tag --> Documentation_Pipeline_Demo
    Browse_documentation_by_tag --> Reference
    Browse_documentation_by_tag --> Generated_docs_pages
```

## Components

| Component | Source | Type |
|-----------|--------|------|
| Overview | SEO_GUIDE.md | reference |
| Features | SEO_GUIDE.md | reference |
| Usage | SEO_GUIDE.md | reference |
| GitHub Actions | SEO_GUIDE.md | reference |
| Configuration | SEO_GUIDE.md | reference |
| Validation Rules | SEO_GUIDE.md | reference |
| Lifecycle Management | SEO_GUIDE.md | reference |
| Search Ranking Factors | SEO_GUIDE.md | reference |
| Monitoring | SEO_GUIDE.md | reference |
| Best Practices | SEO_GUIDE.md | reference |
| Troubleshooting | SEO_GUIDE.md | reference |
| Integration with Other Tools | SEO_GUIDE.md | reference |
| Next steps | SEO_GUIDE.md | reference |
| How to Use Variables | VARIABLES_GUIDE.md | reference |
| Cloud-specific Instructions | VARIABLES_GUIDE.md | reference |
| Self-hosted Instructions | VARIABLES_GUIDE.md | reference |
| Available Variables | VARIABLES_GUIDE.md | reference |
| Setup Requirements | VARIABLES_GUIDE.md | reference |
| Adding New Variables | VARIABLES_GUIDE.md | reference |
| Examples | VARIABLES_GUIDE.md | reference |
| Prerequisites | VARIABLES_GUIDE.md | reference |
| Limits | VARIABLES_GUIDE.md | reference |
| Support | VARIABLES_GUIDE.md | reference |
| Variable Categories Reference | VARIABLES_GUIDE.md | reference |
| Top-level Keys | assets/protocols/asyncapi/asyncapi-api.md | reference |
| Channels | assets/protocols/asyncapi/asyncapi-api.md | reference |
| Interactive AsyncAPI Tester | assets/protocols/asyncapi/asyncapi-api.md | reference |
| Operations | assets/protocols/graphql/graphql-api.md | reference |
| Interactive GraphQL Playground | assets/protocols/graphql/graphql-api.md | reference |
| Service Methods | assets/protocols/grpc/grpc-api.md | reference |
| Interactive gRPC Tester | assets/protocols/grpc/grpc-api.md | reference |
| Notes | assets/protocols/rest/rest-api.md | reference |
| Channels/Events | assets/protocols/websocket/websocket-api.md | reference |
| Interactive WebSocket Tester | assets/protocols/websocket/websocket-api.md | reference |
| Concepts | concepts/index.md | concept |
| Core components | concepts/intelligent-knowledge-system.md | concept |
| Why this improves documentation quality | concepts/intelligent-knowledge-system.md | concept |
| Data model | concepts/intelligent-knowledge-system.md | concept |
| Operational flow | concepts/intelligent-knowledge-system.md | concept |
| RAG integration contract | concepts/intelligent-knowledge-system.md | concept |
| Advanced retrieval pipeline | concepts/intelligent-knowledge-system.md | concept |
| Security and governance | concepts/intelligent-knowledge-system.md | concept |
| How the workflow execution model works | concepts/workflow-execution-model.md | concept |
| Data structure between nodes | concepts/workflow-execution-model.md | concept |
| Execution flow | concepts/workflow-execution-model.md | concept |
| Execution modes | concepts/workflow-execution-model.md | concept |
| Error handling | concepts/workflow-execution-model.md | concept |
| Key implications for documentation writers | concepts/workflow-execution-model.md | concept |
| Related | concepts/workflow-execution-model.md | concept |
| Documentation Pipeline Demo | index.md | concept |
| What this demo shows | index.md | concept |
| Browse by type | index.md | concept |
| Browse by tag | index.md | concept |
| 1. Core promise | operations/CANONICAL_FLOW.md | reference |
| 2. One-time setup (you do this) | operations/CANONICAL_FLOW.md | reference |
| 3. Weekly automation (no manual commands) | operations/CANONICAL_FLOW.md | reference |
| 4. Human role | operations/CANONICAL_FLOW.md | reference |
| 5. Operator manual checks after setup | operations/CANONICAL_FLOW.md | reference |
| 6. Licensing | operations/CANONICAL_FLOW.md | reference |
| 7. Plan packaging | operations/CANONICAL_FLOW.md | reference |
| 8. What to say in sales calls | operations/CANONICAL_FLOW.md | reference |
| 9. Compatibility mode | operations/CANONICAL_FLOW.md | reference |
| 10. Deep references | operations/CANONICAL_FLOW.md | reference |
| Главное правило | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Что именно вы настраиваете (и где) | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Команда сборки | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Как это ставится клиенту | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Что добавить в `.gitignore` клиента | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| RAG/knowledge без ручных запусков | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Два простых примера | operations/CENTRALIZED_CLIENT_BUNDLES.md | reference |
| Supported protocols (core-5) | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Unified stage flow | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Engine and adapters | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Protocol-specific validators | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Regression | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Docs + publish | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Test assets and smart-merge | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Advanced RAG retrieval pipeline | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| Template and snippet parity | operations/MULTI_PROTOCOL_ARCHITECTURE.md | reference |
| How to enable any capability for a client | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Direct CLI entry points (not exposed as npm scripts) | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Multi-protocol contract pipeline | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Test assets generation and smart merge | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Quality checks (32 automated) | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| RAG retrieval pipeline | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Public docs auditor and executive PDF | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| API-first external sandbox note | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| PR auto-doc workflow capability | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Templates | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Policy Packs | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Knowledge Modules | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| Docker Compose Profiles | operations/PIPELINE_CAPABILITIES_CATALOG.md | reference |
| 1. Feature matrix | operations/PLAN_TIERS.md | reference |
| 2. Default plan presets | operations/PLAN_TIERS.md | reference |
| 3. How to apply a plan for a client | operations/PLAN_TIERS.md | reference |
| 4. License enforcement | operations/PLAN_TIERS.md | reference |
| 5. Plan upgrade path | operations/PLAN_TIERS.md | reference |
| Where smart-merge runs | operations/SMART_MERGE_REVIEW.md | how-to |
| Merge rules | operations/SMART_MERGE_REVIEW.md | how-to |
| Where reviewer sees required edits | operations/SMART_MERGE_REVIEW.md | how-to |
| 1. Client identity | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 2. Bundle packaging | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 3. LLM instruction packaging | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 4. Automation schedule (weekly) | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 5. Runtime behavior | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 6. API-first configuration (one branch, not the whole product) | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 7. Module switches | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 8. Universal tasks (core UTP, not optional extras) | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 9. Integrations (single control point) | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 9. Private tuning | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 10. Licensing | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 11. Legal labeling | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 12. Flow presets (copy-paste) | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| 9. Fully automated RAG/knowledge flow | operations/UNIFIED_CLIENT_CONFIG.md | reference |
| Provider options | reference/api-playground.md | reference |
| Configure this page | reference/api-playground.md | reference |
| Playground | reference/api-playground.md | reference |
| Security guidance | reference/api-playground.md | reference |
| Old Webhook API | reference/deprecated-example.md | reference |
| Example Code | reference/deprecated-example.md | reference |
| Reference | reference/index.md | reference |
| Included modules | reference/intent-experiences/automate-developer.md | reference |
| Generated docs pages | reference/intent-experiences/index.md | reference |
| Generated bundle outputs | reference/intent-experiences/index.md | reference |
| Retrieval artifact | reference/intent-experiences/index.md | reference |
| Source of truth | reference/intent-experiences/index.md | reference |
| Validation commands | reference/intent-experiences/index.md | reference |
| Related pages | reference/intent-experiences/index.md | reference |
| Zero client data guarantee | reference/network-transparency.md | reference |
| Complete outgoing request inventory | reference/network-transparency.md | reference |
| Requests the pipeline never makes | reference/network-transparency.md | reference |
| How to audit the pipeline yourself | reference/network-transparency.md | reference |
| Machine fingerprint details | reference/network-transparency.md | reference |
| Capability pack contents | reference/network-transparency.md | reference |
| Summary of data flow | reference/network-transparency.md | reference |
| Webhook node reference | reference/nodes/webhook.md | reference |
| Parameters | reference/nodes/webhook.md | reference |
| Authentication options | reference/nodes/webhook.md | reference |
| URLs | reference/nodes/webhook.md | reference |
| Output | reference/nodes/webhook.md | reference |
| Smoke-checked examples | reference/nodes/webhook.md | reference |
| Environment variables | reference/nodes/webhook.md | reference |
| Start a sandbox endpoint | reference/taskstream-api-playground.md | reference |
| Playground embed | reference/taskstream-api-playground.md | reference |
| Multi-language request examples | reference/taskstream-api-playground.md | reference |
| What this validates | reference/taskstream-api-playground.md | reference |
| Input artifact location | reference/taskstream-planning-notes.md | reference |
| How the pipeline uses this input | reference/taskstream-planning-notes.md | reference |
| Notes format (demo excerpt) | reference/taskstream-planning-notes.md | reference |
| Browse documentation by tag | tags.md | reference |
