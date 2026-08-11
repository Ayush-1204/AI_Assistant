import asyncio
import json
import logging
import uuid
import typing
from collections.abc import AsyncGenerator
from datetime import datetime

from app.config import settings
from app.schemas.ai_pipeline import CuratedContext, ExecutionTrace, NormalizedToolResult, ValidationReport
from app.schemas.tool import ToolRequest, ToolResponse
from app.services.ai.planner.editor import EditorStage
from app.services.ai.planner.evaluator import EvaluatorStage
from app.services.ai.planner.planner import Planner
from app.services.ai.planner.presentation_planner import PresentationPlanner
from app.services.ai.planner.upfront_planner import UpfrontPlanner
from app.services.ai.planner.validator import ValidatorStage
from app.services.ai.tools.orchestrator import ToolOrchestrator
from app.services.ai.tools.router import ToolRouter
from app.services.ai.tools.strategies import ToolInvocationStrategy

logger = logging.getLogger(__name__)

class AgentExecutor:
    """
    Phase 3 Adaptive Graph Executor:
    Replaces the static DAG with an adaptive pipeline supporting:
    - Capability-Based Routing
    - Partial Replanning
    - Execution Tracing
    - Final Quality Evaluation
    """
    def __init__(
        self,
        planner: Planner,
        orchestrator: ToolOrchestrator,
        strategy: ToolInvocationStrategy,
        intent: str = "general",
    ):
        self.planner = planner
        self.orchestrator = orchestrator
        self.strategy = strategy
        self.intent = intent
        self.upfront = UpfrontPlanner(self.planner.provider)
        self.validator = ValidatorStage(self.planner.provider)
        self.editor = EditorStage(self.planner.provider)
        self.evaluator = EvaluatorStage(self.planner.provider)
        self.tool_router = ToolRouter(self.planner.provider, self.orchestrator.registry)
        self.presentation_planner = PresentationPlanner(self.planner.provider)

    async def execute_task_graph(self, tasks: list[dict], context: dict, trace: ExecutionTrace, progress_callback=None) -> list[NormalizedToolResult]:
        """
        Executes a list of DAG tasks using capability routing.
        """
        results = []
        
        async def run_task(task_def: dict) -> NormalizedToolResult:
            trace.tasks_executed += 1
            capability = str(task_def.get("capability") or "")
            
            # Step 1: Capability Routing
            tool_name = await self.tool_router.resolve_capability(capability) if capability else None
            if not tool_name:
                trace.tasks_failed += 1
                return NormalizedToolResult(
                    tool_name=capability or "Unknown",
                    source="Router",
                    confidence=0.0,
                    rawData=f"Failed to find tool for capability: {capability}"
                )
                
            req = ToolRequest(
                id=task_def.get("id"),
                name=tool_name,
                arguments=task_def.get("tool_arguments", {})
            )
            
            if progress_callback:
                await progress_callback(f"Executing {tool_name}...")
            
            # Step 2: Execution
            resp = await self.orchestrator.execute_tool(req, context)
            if resp.normalized_result:
                return resp.normalized_result
            else:
                trace.tasks_failed += 1
                return NormalizedToolResult(
                    tool_name=req.name,
                    source=req.name,
                    confidence=0.0,
                    rawData="Failed to normalize result."
                )

        tasks_to_run = [t for t in tasks if not t.get("dependencies")]
        if tasks_to_run:
            coroutines = [run_task(t) for t in tasks_to_run]
            batch_results = await asyncio.gather(*coroutines, return_exceptions=True)
            for res in batch_results:
                if isinstance(res, NormalizedToolResult):
                    results.append(res)
                elif isinstance(res, Exception):
                    trace.tasks_failed += 1
                    logger.error(f"Task failed with exception: {res}")
                    results.append(NormalizedToolResult(
                        tool_name="Unknown",
                        source="Executor",
                        confidence=0.0,
                        rawData=f"Fatal exception during task execution: {str(res)}"
                    ))
                    
        return results

    async def run(self, query: str, context: dict, messages: list[dict], tools_payload: list[dict]) -> str:
        trace = ExecutionTrace(id=str(uuid.uuid4()))
        
        # Step 1: Upfront Planning
        plan = await self.upfront.generate_plan(query, context_messages=messages)
        if not plan or not plan.get("tools_needed", False):
            res, _, _, text = await self.planner.plan_step(messages, tools_payload)
            empty_context = CuratedContext(summary=text, missing_information=[])
            layout = await self.presentation_planner.plan_layout(query, empty_context, context_messages=messages)
            nodes = await self.presentation_planner.generate_content(query, layout, empty_context, context_messages=messages)
            final_presentation_json = json.dumps(nodes, indent=2)
            
            trace.end_time = datetime.now()
            logger.info(f"[Trace] {trace.model_dump_json()}")
            return final_presentation_json

        # Step 2: Parallel Tool Execution (DAG)
        raw_results = await self.execute_task_graph(plan.get("tasks", []), context, trace)
        
        # Step 3: Validation & Adaptive Replanning
        valid_results = []
        for i, r in enumerate(raw_results):
            report = await self.validator.validate(query, r)
            if report.is_trustworthy:
                valid_results.append(r)
            else:
                logger.warning(f"Task result rejected by validator: {r.tool_name}. Reason: {report.reason}")
                trace.tasks_failed += 1
                
                # Adaptive Replan Trigger
                original_task = plan.get("tasks", [])[i] if i < len(plan.get("tasks", [])) else {}
                replan_task = await self.upfront.replan_branch(query, original_task, report.reason)
                
                if replan_task:
                    trace.replans_triggered += 1
                    logger.info(f"Executing replanned task: {replan_task.get('name')}")
                    replan_results = await self.execute_task_graph([replan_task], context, trace)
                    for rr in replan_results:
                        rr_report = await self.validator.validate(query, rr)
                        if rr_report.is_trustworthy:
                            valid_results.append(rr)
                
        # Step 4: Editor Layer
        curated_context = await self.editor.curate(query, valid_results)
        
        # Step 5: Presentation Planning (Decide UI First)
        layout = await self.presentation_planner.plan_layout(query, curated_context, context_messages=messages)
        
        # Step 6: Content Generation (Fill in the UI)
        presentation_nodes = await self.presentation_planner.generate_content(query, layout, curated_context, context_messages=messages)
        final_presentation_json = json.dumps(presentation_nodes, indent=2)
        
        # Step 7: Final Quality Evaluation
        passed = await self.evaluator.evaluate(final_presentation_json, curated_context)
        trace.final_quality_score = 1.0 if passed else 0.0
        
        if not passed:
            logger.warning("[Executor] Final response failed quality check. Triggering rewrite.")
            # Simple rewrite logic: Re-generate content using the same layout
            presentation_nodes = await self.presentation_planner.generate_content(
                query + " (Ensure you STRICTLY follow the Curated Context)", 
                layout, 
                curated_context,
                context_messages=messages
            )
            final_presentation_json = json.dumps(presentation_nodes, indent=2)
            
        trace.end_time = datetime.now()
        logger.info(f"[Trace] {trace.model_dump_json()}")
        return final_presentation_json
        
    async def stream_run(self, query: str, context: dict, messages: list[dict], tools_payload: list[dict], fastapi_request: typing.Any | None = None) -> AsyncGenerator[str, None]:
        trace = ExecutionTrace(id=str(uuid.uuid4()))
        plan = await self.upfront.generate_plan(query, context_messages=messages)
        if not plan or not plan.get("tools_needed", False):
            # No tools needed, stream raw conversational text directly using the fast model
            import typing
            from app.services.ai.providers.router import ProviderRouter
            router_inst = typing.cast(ProviderRouter, self.planner.provider)
            
            async for chunk in router_inst.stream_chat(messages, tools=None, intent=self.intent):
                if fastapi_request and await fastapi_request.is_disconnected():
                    raise asyncio.CancelledError("Client disconnected")
                if isinstance(chunk, str):
                    payload = json.dumps({"type": "content", "delta": chunk})
                    yield f"data: {payload}\n\n"
            
            trace.end_time = datetime.now()
            logger.info(f"[Trace] Raw text stream completed. {trace.model_dump_json()}")
            return

        import typing
        queue: asyncio.Queue[typing.Any] = asyncio.Queue()
        async def put_progress(msg: str):
            await queue.put({"type": "tool", "name": msg})

        async def _run_dag_and_curate():
            try:
                raw_results = await self.execute_task_graph(plan.get("tasks", []), context, trace, put_progress)
                
                valid_results = []
                for i, r in enumerate(raw_results):
                    report = await self.validator.validate(query, r)
                    if report.is_trustworthy:
                        valid_results.append(r)
                    else:
                        original_task = plan.get("tasks", [])[i] if i < len(plan.get("tasks", [])) else {}
                        await put_progress(f"Replanning {r.tool_name}...")
                        replan_task = await self.upfront.replan_branch(query, original_task, report.reason)
                        if replan_task:
                            trace.replans_triggered += 1
                            replan_results = await self.execute_task_graph([replan_task], context, trace, put_progress)
                            for rr in replan_results:
                                rr_report = await self.validator.validate(query, rr)
                                if rr_report.is_trustworthy:
                                    valid_results.append(rr)
                        
                await put_progress("Curating results...")
                cc = await self.editor.curate(query, valid_results)
                await queue.put({"type": "done", "curated_context": cc})
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[Executor] DAG task failed: {str(e)}")
                await queue.put({"type": "error", "error": str(e)})

        dag_task = asyncio.create_task(_run_dag_and_curate())
        
        curated_context = typing.cast(CuratedContext, None)
        while True:
            if fastapi_request and await fastapi_request.is_disconnected():
                dag_task.cancel()
                raise asyncio.CancelledError("Client disconnected")
            
            try:
                msg = typing.cast(dict, await asyncio.wait_for(queue.get(), timeout=1.0))
                if msg.get("type") == "done":
                    curated_context = msg.get("curated_context")
                    break
                elif msg.get("type") == "error":
                    dag_task.cancel()
                    raise Exception(msg.get("error"))
                else:
                    yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            except asyncio.CancelledError:
                dag_task.cancel()
                raise
        
        assert curated_context is not None
        # Stream Mode: Decide UI, then Generate Content progressively
        layout = await self.presentation_planner.plan_layout(query, curated_context, context_messages=messages)
        
        # Stream out the Presentation Nodes as they are completed
        # Accumulate the final JSON to evaluate for quality
        accumulated_nodes = []
        async for event in self.presentation_planner.generate_content_stream(query, layout, curated_context, context_messages=messages):
            if fastapi_request and await fastapi_request.is_disconnected():
                raise asyncio.CancelledError("Client disconnected")
                
            if event.get("event_type") == "presentation_node":
                accumulated_nodes.append(event["node"])
            
            if "event_type" in event:
                event["type"] = event.pop("event_type")
                
            payload = json.dumps(event)
            yield f"data: {payload}\n\n"
            
        final_presentation_json = json.dumps(accumulated_nodes, indent=2)
        passed = await self.evaluator.evaluate(final_presentation_json, curated_context)
        trace.final_quality_score = 1.0 if passed else 0.0
                 
        trace.end_time = datetime.now()
        logger.info(f"[Trace] Streaming completed. {trace.model_dump_json()}")
