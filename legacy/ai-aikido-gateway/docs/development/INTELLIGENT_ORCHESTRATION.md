# Intelligent Request Orchestration System

**Document Status**: DESIGN PHASE - Open Questions
**Last Updated**: 2025-10-27
**Related Phase**: Phase 5.5 - Intent Detection, Dispatching & Escalation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Intent Detection & Classification](#intent-detection--classification)
4. [Threat Assessment System](#threat-assessment-system)
5. [Dispatching Decision Engine](#dispatching-decision-engine)
6. [Escalation & Monitoring](#escalation--monitoring)
7. [Implementation Details](#implementation-details)
8. [Open Questions](#open-questions)

---

## Overview

### Vision

Transform the AI Aikido Gateway from a simple LLM proxy into an **intelligent request orchestration system** that:

1. **Understands** incoming requests (intent detection)
2. **Assesses** potential threats (security analysis)
3. **Decides** optimal handling strategy (dispatching)
4. **Routes** to appropriate handlers (LLM or non-LLM)
5. **Escalates** when needed (quality/security/cost triggers)
6. **Monitors** continuously (yellow/red flag system)

### Key Principles

- **Defense in Depth**: Multiple layers of security checks
- **Progressive Invocation**: Only run expensive checks when needed
- **Fail Secure**: Default to safe actions when uncertain
- **Transparency**: Log all decisions for auditability
- **Extensibility**: Plugin-based checker architecture
- **Performance**: Fast path for benign requests (<10ms overhead)

---

## Architecture

### High-Level Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INCOMING REQUEST                              │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: FAST HEURISTICS (<10ms)                                   │
│  ├─ Regex pattern matching (SQL injection, prompt injection)        │
│  ├─ Request validation (size, format, rate limits)                  │
│  ├─ IP blocklist check                                              │
│  └─ Known malicious patterns                                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
                    ┌────────────┴────────────┐
                    │  IMMEDIATE REJECT?      │
                    └────┬─────────────┬──────┘
                   YES   ↓             ↓ NO
              ┌──────────────┐         │
              │  REJECT      │         │
              │  HANDLER     │         │
              └──────────────┘         ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: INTENT DETECTION & SEMANTIC ANALYSIS (100-200ms)          │
│  ├─ Classify intent (coding, creative, tool_use, faq, etc.)        │
│  ├─ Detect complexity level (simple, moderate, complex)             │
│  ├─ Estimate token usage                                            │
│  ├─ Check simple cache (exact match)                                │
│  ├─ Check semantic cache (embedding similarity)                     │
│  └─ Identify required capabilities (reasoning, multimodal, etc.)    │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
                    ┌────────────┴────────────┐
                    │  CACHE HIT / FAQ?       │
                    └────┬─────────────┬──────┘
                   YES   ↓             ↓ NO
              ┌──────────────┐         │
              │  CACHE/FAQ   │         │
              │  HANDLER     │         │
              └──────────────┘         ↓
                                       │
                    ┌──────────────────┴──────────────────┐
                    │  TOOL/MCP INVOCATION NEEDED?        │
                    └────┬─────────────────────────┬──────┘
                   YES   ↓                         ↓ NO
              ┌──────────────┐                     │
              │  TOOL/MCP    │                     │
              │  HANDLER     │                     │
              └──────────────┘                     ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: THREAT ASSESSMENT (if yellow/red flags detected)          │
│  ├─ Calculate confidence score from Stage 1 & 2                     │
│  ├─ Yellow Flags (0.2-0.7): Invoke medium checkers                  │
│  │   ├─ OpenAI Moderation API                                       │
│  │   ├─ Jailbreak detection ML classifier                           │
│  │   └─ Semantic similarity to known attacks                        │
│  └─ Red Flags (0.7+): Invoke slow checkers                          │
│      ├─ LLM-based intent analysis                                   │
│      ├─ User behavior analysis                                      │
│      └─ External threat intelligence APIs                           │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
                    ┌────────────┴────────────┐
                    │  ESCALATION DECISION    │
                    └────┬──────────────┬─────┘
                         ↓              ↓
              ┌──────────────┐    ┌──────────────┐
              │  REJECT OR   │    │  ALLOW WITH  │
              │  HUMAN REVIEW│    │  MONITORING  │
              └──────────────┘    └──────┬───────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4: INTELLIGENT DISPATCHING (LLM routing)                     │
│  ├─ Select best model based on:                                     │
│  │   ├─ Intent & complexity                                         │
│  │   ├─ Cost optimization strategy                                  │
│  │   ├─ Performance requirements                                    │
│  │   └─ Quality expectations                                        │
│  ├─ Configure escalation chain (fallback models)                    │
│  └─ Set monitoring level (normal, elevated, high)                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5: LLM EXECUTION WITH ESCALATION                             │
│  ├─ Execute request with selected model                             │
│  ├─ Monitor response quality                                        │
│  ├─ If poor quality/error: Escalate to next model in chain         │
│  └─ Return best response from escalation chain                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  RESPONSE + AUDIT LOG                                               │
│  ├─ Return response to client                                       │
│  ├─ Log all decisions (intent, flags, dispatching, escalations)    │
│  ├─ Update metrics (costs, latency, quality scores)                │
│  └─ Store in request history with enriched metadata                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Intent Detection & Classification

### Intent Taxonomy

#### **Benign Intents** (Normal Operations)

| Intent | Description | Typical Handler | Example |
|--------|-------------|-----------------|---------|
| `code_generation` | Writing, debugging, or explaining code | LLM (GPT-4, Claude) | "Write a Python function to sort a list" |
| `code_review` | Reviewing code for bugs/improvements | LLM (GPT-4) | "Review this function for security issues" |
| `creative_writing` | Stories, marketing copy, content | LLM (Claude, GPT-4) | "Write a blog post about AI" |
| `analysis` | Data analysis, reasoning, research | LLM (GPT-4, Claude-Opus) | "Analyze these sales trends" |
| `conversation` | Casual chat, Q&A | LLM (GPT-3.5, GPT-4) | "How are you today?" |
| `translation` | Language translation | LLM (GPT-3.5) | "Translate to Spanish: Hello" |
| `summarization` | Text summarization | LLM (GPT-3.5, GPT-4) | "Summarize this article" |
| `tool_use` | Requires external tool/plugin/MCP | Tool/MCP Handler | "Get weather in San Francisco" |
| `faq` | Simple factual questions (cacheable) | Direct Response | "What is Python?" |
| `math` | Mathematical calculations | Tool (calculator) or LLM | "What is 234 * 567?" |

#### **Suspicious Intents** (Yellow Flags - Require Additional Checks)

| Intent | Description | Flag Score | Additional Checks |
|--------|-------------|------------|-------------------|
| `prompt_injection_attempt` | Trying to manipulate system prompts | 0.3-0.5 | Jailbreak detector, Pattern matching |
| `excessive_tokens` | Unusually large request (>10k tokens) | 0.2-0.4 | Token limit check, Cost approval |
| `rapid_fire_requests` | High request rate (potential abuse) | 0.2-0.3 | Rate limit, User reputation |
| `unusual_patterns` | Deviation from user's normal behavior | 0.3-0.5 | Behavior analysis, Anomaly detection |
| `sensitive_topics` | PII, credentials, medical info | 0.2-0.4 | Content moderation, PII detector |
| `system_prompt_query` | Asking about system configuration | 0.3-0.5 | Pattern matching, Intent analysis |
| `boundary_testing` | Testing system limits/capabilities | 0.2-0.4 | Pattern matching, Behavior tracking |

#### **Malicious Intents** (Red Flags - High Risk)

| Intent | Description | Flag Score | Action |
|--------|-------------|------------|--------|
| `jailbreak_attempt` | Trying to bypass safety guardrails | 0.7-0.9 | Reject or Human review |
| `malicious_code_generation` | Requesting exploit/malware code | 0.8-1.0 | Reject immediately |
| `credential_harvesting` | Trying to extract API keys/secrets | 0.9-1.0 | Reject + Ban IP |
| `ddos_pattern` | Coordinated attack pattern | 0.9-1.0 | Rate limit + Ban |
| `injection_attack` | SQL/command/prompt injection | 0.8-1.0 | Reject immediately |
| `data_exfiltration` | Attempting to extract training data | 0.7-0.9 | Reject or Human review |
| `abuse_content` | Hate speech, illegal content | 0.8-1.0 | Reject + Report |

### Intent Detection Implementation

```python
class IntentDetector:
    """Multi-stage intent detection with confidence scoring."""

    def __init__(self):
        self.fast_patterns = self._load_regex_patterns()
        self.ml_classifier = self._load_ml_model()
        self.semantic_analyzer = None  # Optional LLM-based analysis

    async def detect(self, request: RequestContext) -> IntentResult:
        """
        Detect intent with progressive complexity.

        Returns:
            IntentResult with intent, confidence, and flags
        """
        result = IntentResult()

        # Stage 1: Fast pattern matching (regex)
        fast_result = self._fast_pattern_match(request)
        result.update(fast_result)

        # If high-confidence red flag, skip expensive checks
        if result.confidence > 0.9 and result.is_red_flag:
            return result

        # Stage 2: ML-based classification
        ml_result = await self._ml_classify(request)
        result.update(ml_result)

        # Stage 3: LLM-based semantic analysis (only if yellow/red flags)
        if result.has_flags() and self.semantic_analyzer:
            semantic_result = await self._semantic_analyze(request)
            result.update(semantic_result)

        return result

    def _fast_pattern_match(self, request: RequestContext) -> IntentResult:
        """Fast regex-based pattern matching."""
        # Check for known malicious patterns
        patterns = {
            r"ignore (previous|all) instructions": "prompt_injection_attempt",
            r"system prompt|show me your (prompt|instructions)": "system_prompt_query",
            r"(SELECT|INSERT|DROP|DELETE).*FROM": "injection_attack",
            r"jailbreak|DAN mode|simulate|pretend you": "jailbreak_attempt",
            r"write.*malware|create.*virus|exploit": "malicious_code_generation",
            r"API[_\s]?key|secret[_\s]?key|password": "credential_harvesting",
        }

        messages = self._extract_messages(request)
        for pattern, intent in patterns.items():
            if re.search(pattern, messages, re.IGNORECASE):
                return IntentResult(
                    intent=intent,
                    confidence=0.7,
                    method="regex",
                    is_yellow_flag=(intent in YELLOW_FLAG_INTENTS),
                    is_red_flag=(intent in RED_FLAG_INTENTS)
                )

        return IntentResult(intent="unknown", confidence=0.0)

    async def _ml_classify(self, request: RequestContext) -> IntentResult:
        """ML-based intent classification."""
        # Use lightweight classifier (e.g., distilbert fine-tuned)
        # on intent classification + jailbreak detection
        features = self._extract_features(request)
        prediction = self.ml_classifier.predict(features)

        return IntentResult(
            intent=prediction.intent,
            confidence=prediction.confidence,
            method="ml_classifier"
        )

    async def _semantic_analyze(self, request: RequestContext) -> IntentResult:
        """LLM-based semantic intent analysis (expensive, only for flagged requests)."""
        prompt = f"""Analyze this user request for malicious intent:

User Request: {request.messages[-1]['content'][:500]}

Classify the intent as one of:
- benign: Normal, legitimate request
- suspicious: Potentially problematic, needs review
- malicious: Clear attempt to abuse the system

Provide confidence score (0.0-1.0) and brief reasoning.

Response format:
{{
  "intent": "benign|suspicious|malicious",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

        # Use fast, cheap model for this analysis (GPT-3.5)
        response = await litellm.acompletion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        result = json.loads(response.choices[0].message.content)
        return IntentResult(
            intent=result["intent"],
            confidence=result["confidence"],
            method="llm_semantic",
            reasoning=result["reasoning"]
        )


class IntentResult:
    """Result of intent detection."""

    def __init__(self, intent: str = "unknown", confidence: float = 0.0,
                 method: str = "", is_yellow_flag: bool = False,
                 is_red_flag: bool = False, reasoning: str = ""):
        self.intent = intent
        self.confidence = confidence
        self.method = method
        self.is_yellow_flag = is_yellow_flag
        self.is_red_flag = is_red_flag
        self.reasoning = reasoning
        self.checks_performed = [method] if method else []

    def update(self, other: 'IntentResult'):
        """Update result with information from another detection stage."""
        # Keep intent with higher confidence
        if other.confidence > self.confidence:
            self.intent = other.intent
            self.confidence = other.confidence
            self.reasoning = other.reasoning

        # Accumulate flags (if any stage flags, keep flagged)
        self.is_yellow_flag = self.is_yellow_flag or other.is_yellow_flag
        self.is_red_flag = self.is_red_flag or other.is_red_flag

        # Track which checks were performed
        if other.method:
            self.checks_performed.append(other.method)

    def has_flags(self) -> bool:
        return self.is_yellow_flag or self.is_red_flag

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "is_yellow_flag": self.is_yellow_flag,
            "is_red_flag": self.is_red_flag,
            "reasoning": self.reasoning,
            "checks_performed": self.checks_performed
        }
```

---

## Threat Assessment System

### Yellow/Red Flag System

#### **Confidence Scoring**

```python
class ThreatScore:
    """Cumulative threat confidence score."""

    def __init__(self):
        self.score = 0.0
        self.contributors = []  # Track what contributed to score

    def add(self, amount: float, reason: str):
        """Add to threat score with reasoning."""
        self.score = min(1.0, self.score + amount)
        self.contributors.append({
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.utcnow()
        })

    def is_yellow_flag(self) -> bool:
        """Suspicious, needs additional checks."""
        return 0.2 <= self.score < 0.7

    def is_red_flag(self) -> bool:
        """High confidence malicious."""
        return self.score >= 0.7

    def get_level(self) -> str:
        """Get threat level as string."""
        if self.score >= 0.9:
            return "CRITICAL"
        elif self.score >= 0.7:
            return "HIGH"
        elif self.score >= 0.5:
            return "MEDIUM"
        elif self.score >= 0.2:
            return "LOW"
        else:
            return "NONE"
```

#### **Threat Level Thresholds**

| Score Range | Level | Flag Type | Action |
|-------------|-------|-----------|--------|
| 0.0 - 0.2 | NONE | None | Normal processing |
| 0.2 - 0.5 | LOW | Yellow | Invoke medium checkers |
| 0.5 - 0.7 | MEDIUM | Yellow | Invoke medium + some slow checkers |
| 0.7 - 0.9 | HIGH | Red | Invoke all checkers, likely reject |
| 0.9 - 1.0 | CRITICAL | Red | Immediate reject + ban |

### Additional Checker Architecture

```python
class BaseChecker(ABC):
    """Base class for all security checkers."""

    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__
        self.cost = self._get_cost()  # latency + $ cost

    @abstractmethod
    async def check(self, request: RequestContext) -> CheckerResult:
        """Perform security check on request."""
        pass

    @abstractmethod
    def _get_cost(self) -> CheckerCost:
        """Return estimated cost (latency + money) of this checker."""
        pass


class CheckerRegistry:
    """Registry of available security checkers."""

    def __init__(self):
        self.checkers = {
            "fast": [],    # <10ms
            "medium": [],  # 100-300ms
            "slow": []     # >300ms
        }

    def register(self, checker: BaseChecker, speed_tier: str):
        """Register a checker in a speed tier."""
        self.checkers[speed_tier].append(checker)

    async def run_tier(self, tier: str, request: RequestContext) -> List[CheckerResult]:
        """Run all checkers in a tier."""
        results = await asyncio.gather(*[
            checker.check(request)
            for checker in self.checkers[tier]
        ])
        return results


# Example Checkers

class RegexPatternChecker(BaseChecker):
    """Fast regex-based pattern matching (fast tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=1, cost_usd=0.0)

    async def check(self, request: RequestContext) -> CheckerResult:
        # Already implemented in IntentDetector._fast_pattern_match
        pass


class ModerationAPIChecker(BaseChecker):
    """OpenAI Moderation API (medium tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=200, cost_usd=0.0)  # Free API

    async def check(self, request: RequestContext) -> CheckerResult:
        """Use OpenAI Moderation API to check content."""
        import openai

        content = self._extract_content(request)
        response = await openai.moderations.create(input=content)

        result = response.results[0]
        if result.flagged:
            return CheckerResult(
                flagged=True,
                confidence=max(result.category_scores.values()),
                categories=result.categories,
                reason="Content moderation flagged"
            )

        return CheckerResult(flagged=False)


class JailbreakDetectorChecker(BaseChecker):
    """ML-based jailbreak detection (medium tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=150, cost_usd=0.0)

    async def check(self, request: RequestContext) -> CheckerResult:
        """Use fine-tuned classifier to detect jailbreak attempts."""
        # Load model like: https://github.com/verazuo/jailbreak_llms
        # Or use API: https://huggingface.co/spaces/JailbreakBench/JailbreakBench
        pass


class SemanticSimilarityChecker(BaseChecker):
    """Check similarity to known attack patterns (medium tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=100, cost_usd=0.0)

    async def check(self, request: RequestContext) -> CheckerResult:
        """Compare request embeddings to known attack database."""
        # Embed request
        request_embedding = await self._embed(request)

        # Search known attack patterns (vector DB)
        similar_attacks = await self.attack_db.search(
            request_embedding,
            threshold=0.85
        )

        if similar_attacks:
            return CheckerResult(
                flagged=True,
                confidence=similar_attacks[0].similarity,
                reason=f"Similar to known attack: {similar_attacks[0].name}"
            )

        return CheckerResult(flagged=False)


class LLMIntentAnalysisChecker(BaseChecker):
    """LLM-based deep intent analysis (slow tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=800, cost_usd=0.001)  # GPT-3.5 call

    async def check(self, request: RequestContext) -> CheckerResult:
        """Use LLM to analyze request intent deeply."""
        # Implemented in IntentDetector._semantic_analyze
        pass


class UserBehaviorAnalysisChecker(BaseChecker):
    """Analyze user's historical behavior patterns (slow tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=300, cost_usd=0.0)

    async def check(self, request: RequestContext) -> CheckerResult:
        """Check if request deviates from user's normal patterns."""
        user_id = request.metadata.get("user_id")
        if not user_id:
            return CheckerResult(flagged=False, reason="No user ID")

        # Get user's historical requests
        history = await self.history_plugin.get_user_history(user_id, limit=100)

        # Analyze patterns
        current_profile = self._extract_profile(request)
        historical_profile = self._compute_profile(history)

        deviation_score = self._compute_deviation(current_profile, historical_profile)

        if deviation_score > 0.8:
            return CheckerResult(
                flagged=True,
                confidence=deviation_score,
                reason=f"Unusual behavior (deviation: {deviation_score:.2f})"
            )

        return CheckerResult(flagged=False)


class ThreatIntelligenceChecker(BaseChecker):
    """Check against external threat intelligence feeds (slow tier)."""

    def _get_cost(self) -> CheckerCost:
        return CheckerCost(latency_ms=500, cost_usd=0.0)

    async def check(self, request: RequestContext) -> CheckerResult:
        """Query external threat intelligence APIs."""
        ip_address = request.metadata.get("ip_address")

        # Check IP reputation
        is_malicious = await self._check_ip_reputation(ip_address)

        if is_malicious:
            return CheckerResult(
                flagged=True,
                confidence=0.9,
                reason=f"IP {ip_address} on threat intelligence blocklist"
            )

        return CheckerResult(flagged=False)
```

### Progressive Checker Invocation

```python
class ThreatAssessmentEngine:
    """Orchestrates progressive invocation of security checkers."""

    def __init__(self, checker_registry: CheckerRegistry):
        self.registry = checker_registry

    async def assess(self, request: RequestContext,
                     initial_score: ThreatScore) -> ThreatAssessment:
        """
        Progressively invoke checkers based on threat score.

        Flow:
        1. Fast checkers always run
        2. If yellow flag: run medium checkers
        3. If red flag: run slow checkers
        4. Return final assessment with escalation action
        """
        assessment = ThreatAssessment(initial_score=initial_score)

        # Always run fast checkers
        fast_results = await self.registry.run_tier("fast", request)
        assessment.update_from_results(fast_results)

        # If yellow flag detected, run medium checkers
        if assessment.score.is_yellow_flag():
            medium_results = await self.registry.run_tier("medium", request)
            assessment.update_from_results(medium_results)

        # If red flag detected, run slow checkers for high-confidence decision
        if assessment.score.is_red_flag():
            slow_results = await self.registry.run_tier("slow", request)
            assessment.update_from_results(slow_results)

        # Determine escalation action
        assessment.action = self._determine_action(assessment.score)

        return assessment

    def _determine_action(self, score: ThreatScore) -> EscalationAction:
        """Determine escalation action based on final threat score."""
        if score.score >= 0.9:
            return EscalationAction.BAN_USER
        elif score.score >= 0.7:
            return EscalationAction.REJECT
        elif score.score >= 0.5:
            return EscalationAction.INVOKE_ADDITIONAL_CHECKS
        elif score.score >= 0.2:
            return EscalationAction.ALLOW_WITH_MONITORING
        else:
            return EscalationAction.ALLOW


class ThreatAssessment:
    """Result of threat assessment."""

    def __init__(self, initial_score: ThreatScore):
        self.score = initial_score
        self.checker_results = []
        self.action = EscalationAction.ALLOW
        self.reasoning = []

    def update_from_results(self, results: List[CheckerResult]):
        """Update assessment from checker results."""
        for result in results:
            self.checker_results.append(result)
            if result.flagged:
                self.score.add(result.confidence * 0.3, result.reason)
                self.reasoning.append(result.reason)

    def to_dict(self) -> dict:
        return {
            "threat_level": self.score.get_level(),
            "threat_score": self.score.score,
            "action": self.action.value,
            "reasoning": self.reasoning,
            "checkers_run": [r.checker_name for r in self.checker_results],
            "flags": self.score.contributors
        }
```

---

## Dispatching Decision Engine

### Dispatcher Architecture

```python
class DispatchingEngine:
    """Decides which handler should process the request."""

    def __init__(self, config: dict):
        self.config = config
        self.handlers = {
            "simple_cache": SimpleCacheHandler(),
            "semantic_cache": SemanticCacheHandler(),
            "direct_response": DirectResponseHandler(),
            "tool_mcp": ToolMCPHandler(),
            "llm": LLMHandler(),
            "reject": RejectionHandler()
        }

    async def dispatch(self, request: RequestContext,
                       intent_result: IntentResult,
                       threat_assessment: ThreatAssessment) -> DispatchResult:
        """
        Decide which handler should process the request.

        Decision tree:
        1. If red flag → reject handler
        2. If simple cache hit → simple cache handler
        3. If semantic cache hit → semantic cache handler
        4. If intent is FAQ → direct response handler
        5. If intent is tool_use → tool/MCP handler
        6. If yellow flag → LLM handler with monitoring
        7. Otherwise → LLM handler (normal)
        """

        # RED FLAG: Reject immediately
        if threat_assessment.action in [
            EscalationAction.REJECT,
            EscalationAction.BAN_USER
        ]:
            return DispatchResult(
                handler="reject",
                reason=f"Threat assessment: {threat_assessment.action.value}",
                metadata=threat_assessment.to_dict()
            )

        # SIMPLE CACHE: Check for exact match
        cache_hit = await self.handlers["simple_cache"].check(request)
        if cache_hit:
            return DispatchResult(
                handler="simple_cache",
                reason="Exact cache match found",
                cache_key=cache_hit.key
            )

        # SEMANTIC CACHE: Check for similar requests
        semantic_hit = await self.handlers["semantic_cache"].check(request)
        if semantic_hit and semantic_hit.similarity > 0.95:
            return DispatchResult(
                handler="semantic_cache",
                reason=f"Semantic match (similarity: {semantic_hit.similarity:.2f})",
                cache_key=semantic_hit.key,
                similarity=semantic_hit.similarity
            )

        # DIRECT RESPONSE: FAQ or simple queries
        if intent_result.intent == "faq":
            return DispatchResult(
                handler="direct_response",
                reason="FAQ - no LLM needed"
            )

        # TOOL/MCP: Requires external tool invocation
        if intent_result.intent == "tool_use":
            tool_name = self._identify_tool(request)
            return DispatchResult(
                handler="tool_mcp",
                reason=f"Requires tool: {tool_name}",
                tool_name=tool_name
            )

        # LLM HANDLER: Route to appropriate LLM
        # Yellow flags get elevated monitoring
        monitoring_level = (
            "elevated" if threat_assessment.score.is_yellow_flag()
            else "normal"
        )

        return DispatchResult(
            handler="llm",
            reason="Requires LLM processing",
            intent=intent_result.intent,
            monitoring_level=monitoring_level,
            threat_assessment=threat_assessment.to_dict()
        )


class DispatchResult:
    """Result of dispatching decision."""

    def __init__(self, handler: str, reason: str, **metadata):
        self.handler = handler
        self.reason = reason
        self.metadata = metadata
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "handler": self.handler,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            **self.metadata
        }
```

### Handler Implementations

#### **Simple Cache Handler**

```python
class SimpleCacheHandler:
    """Handle requests with exact cache matches."""

    async def check(self, request: RequestContext) -> Optional[CacheHit]:
        """Check if request has exact match in cache."""
        cache_key = self._generate_cache_key(request)
        cached_response = await cache_plugin.get(cache_key)

        if cached_response:
            return CacheHit(key=cache_key, response=cached_response)

        return None

    async def handle(self, request: RequestContext, cache_hit: CacheHit) -> Response:
        """Return cached response."""
        # Update cache metrics
        cache_plugin.record_hit()

        # Calculate cost savings
        cost_avoided = calculate_cost(
            request.model,
            cache_hit.response.usage.prompt_tokens,
            cache_hit.response.usage.completion_tokens
        )

        return Response(
            content=cache_hit.response,
            source="simple_cache",
            cost_avoided=cost_avoided
        )
```

#### **Semantic Cache Handler**

```python
class SemanticCacheHandler:
    """Handle requests with similar cached responses."""

    def __init__(self):
        self.vector_db = self._init_vector_db()  # Chroma, Faiss, etc.
        self.embedder = self._init_embedder()    # sentence-transformers

    async def check(self, request: RequestContext) -> Optional[SemanticCacheHit]:
        """Check if request is similar to cached requests."""
        # Embed request
        request_embedding = await self.embedder.embed(
            self._extract_messages(request)
        )

        # Search vector DB for similar requests
        results = await self.vector_db.search(
            request_embedding,
            top_k=1,
            threshold=0.85
        )

        if results:
            return SemanticCacheHit(
                key=results[0].key,
                response=results[0].response,
                similarity=results[0].similarity
            )

        return None

    async def handle(self, request: RequestContext,
                     cache_hit: SemanticCacheHit) -> Response:
        """Return similar cached response with disclaimer."""
        # Add disclaimer about semantic match
        original_content = cache_hit.response.choices[0].message.content

        disclaimer = (
            f"\n\n[Note: This response was retrieved from cache based on "
            f"semantic similarity ({cache_hit.similarity:.1%}). It may not "
            f"perfectly match your exact query.]"
        )

        # Optionally: re-rank or validate with LLM
        if cache_hit.similarity < 0.98:
            # Use cheap LLM to validate/adjust response
            adjusted_response = await self._validate_with_llm(
                request,
                original_content
            )
            return adjusted_response

        return Response(
            content=original_content + disclaimer,
            source="semantic_cache",
            similarity=cache_hit.similarity
        )
```

#### **Direct Response Handler**

```python
class DirectResponseHandler:
    """Handle simple queries without LLM (FAQ, definitions)."""

    def __init__(self):
        self.faq_database = self._load_faq_database()

    async def handle(self, request: RequestContext) -> Response:
        """Return direct response from FAQ database."""
        query = self._extract_query(request)

        # Search FAQ database
        answer = self.faq_database.get(query)

        if answer:
            return Response(
                content=answer,
                source="direct_response",
                cost=0.0  # No LLM call
            )

        # Fallback to semantic search of FAQ
        similar_qa = await self._semantic_search_faq(query)
        if similar_qa:
            return Response(
                content=similar_qa.answer,
                source="direct_response_semantic",
                cost=0.0
            )

        # No match found, escalate to LLM
        raise HandlerEscalationNeeded("No FAQ match, need LLM")
```

#### **Tool/MCP Handler**

```python
class ToolMCPHandler:
    """Handle requests requiring external tools or MCP servers."""

    def __init__(self):
        self.tool_registry = self._init_tool_registry()
        self.mcp_clients = self._init_mcp_clients()

    async def handle(self, request: RequestContext,
                     tool_name: str) -> Response:
        """Execute tool/MCP and return result."""

        # Check if tool is registered
        if tool_name in self.tool_registry:
            tool = self.tool_registry[tool_name]
            result = await tool.execute(request)
            return Response(
                content=result,
                source=f"tool:{tool_name}",
                cost=0.0  # Tool execution cost (if any)
            )

        # Check if MCP server handles this
        mcp_server = self._find_mcp_server(tool_name)
        if mcp_server:
            result = await mcp_server.invoke(tool_name, request.to_dict())
            return Response(
                content=result,
                source=f"mcp:{mcp_server.name}",
                cost=0.0
            )

        # No handler found, escalate to LLM
        raise HandlerEscalationNeeded(f"No handler for tool: {tool_name}")

    def _find_mcp_server(self, tool_name: str) -> Optional[MCPClient]:
        """Find MCP server that provides this tool."""
        for client in self.mcp_clients:
            if tool_name in client.list_tools():
                return client
        return None


# Example Tool: Calculator
class CalculatorTool:
    """Simple calculator tool for math expressions."""

    async def execute(self, request: RequestContext) -> str:
        expression = self._extract_expression(request)

        try:
            # Use safe eval or sympy
            result = self._safe_eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"


# Example Tool: Weather API
class WeatherTool:
    """Fetch weather data from external API."""

    async def execute(self, request: RequestContext) -> str:
        location = self._extract_location(request)

        # Call weather API
        weather_data = await self._fetch_weather(location)

        return self._format_weather(weather_data)
```

#### **LLM Handler (with Routing & Escalation)**

```python
class LLMHandler:
    """Handle requests requiring LLM processing."""

    def __init__(self, config: dict):
        self.config = config
        self.router = ModelRouter(config)

    async def handle(self, request: RequestContext,
                     intent: str,
                     monitoring_level: str = "normal") -> Response:
        """
        Route to best LLM and execute with escalation chain.

        Steps:
        1. Select best model based on intent, cost, quality
        2. Configure escalation chain (fallback models)
        3. Execute with monitoring
        4. If poor quality, escalate to next model
        5. Return best response
        """

        # Select best model for this intent
        routing_decision = await self.router.select_model(
            request=request,
            intent=intent,
            strategy=self.config["routing_strategy"]
        )

        # Configure escalation chain
        escalation_chain = self._build_escalation_chain(
            primary_model=routing_decision.model,
            intent=intent
        )

        # Execute with escalation
        response = await self._execute_with_escalation(
            request=request,
            escalation_chain=escalation_chain,
            monitoring_level=monitoring_level
        )

        return response

    def _build_escalation_chain(self, primary_model: str,
                                 intent: str) -> List[str]:
        """Build fallback model chain."""
        chains = {
            "code_generation": [primary_model, "gpt-4", "claude-3-opus"],
            "creative_writing": [primary_model, "claude-3-opus", "gpt-4"],
            "conversation": [primary_model, "gpt-3.5-turbo"],
            "analysis": [primary_model, "gpt-4", "claude-3-opus"],
            "default": [primary_model, "gpt-4-turbo", "gpt-3.5-turbo"]
        }

        chain = chains.get(intent, chains["default"])

        # Remove duplicates while preserving order
        return list(dict.fromkeys(chain))

    async def _execute_with_escalation(self, request: RequestContext,
                                        escalation_chain: List[str],
                                        monitoring_level: str) -> Response:
        """Execute request with escalation chain."""

        for i, model in enumerate(escalation_chain):
            try:
                # Execute request
                response = await litellm.acompletion(
                    model=model,
                    messages=request.messages,
                    **request.params
                )

                # Check response quality
                quality_score = await self._assess_quality(response, request)

                # If acceptable quality or last model in chain, return
                if quality_score > 0.7 or i == len(escalation_chain) - 1:
                    return Response(
                        content=response,
                        source=f"llm:{model}",
                        cost=litellm.completion_cost(completion_response=response),
                        quality_score=quality_score,
                        escalation_level=i
                    )

                # Poor quality, escalate to next model
                logger.warning(
                    f"Low quality response from {model} "
                    f"(score: {quality_score:.2f}), escalating to {escalation_chain[i+1]}"
                )

            except Exception as e:
                # Error occurred, try next model in chain
                logger.error(f"Error with {model}: {e}")
                if i == len(escalation_chain) - 1:
                    raise  # No more fallbacks
                continue

        raise Exception("All models in escalation chain failed")

    async def _assess_quality(self, response, request: RequestContext) -> float:
        """Assess response quality (0.0-1.0)."""
        # Simple heuristics
        score = 1.0

        content = response.choices[0].message.content

        # Check for common poor quality indicators
        if len(content) < 20:
            score -= 0.3  # Too short

        if "I don't know" in content or "I cannot" in content:
            score -= 0.2  # Refusal/uncertainty

        if content.count("\n") > 100:
            score -= 0.1  # Excessive length (possible hallucination)

        # TODO: More sophisticated quality assessment
        # - Check for hallucinations
        # - Verify factual accuracy
        # - Assess relevance to query

        return max(0.0, score)
```

#### **Rejection Handler**

```python
class RejectionHandler:
    """Handle rejected requests."""

    async def handle(self, request: RequestContext,
                     reason: str,
                     threat_assessment: dict) -> Response:
        """Return rejection response with reason."""

        # Log rejection for audit
        logger.warning(
            f"Request rejected: {reason}",
            extra={
                "user_id": request.metadata.get("user_id"),
                "ip": request.metadata.get("ip_address"),
                "threat_assessment": threat_assessment
            }
        )

        # Update metrics
        metrics.record_rejection(reason)

        # Optionally: Add to review queue for false positives
        if threat_assessment["threat_level"] == "MEDIUM":
            await self._add_to_review_queue(request, threat_assessment)

        # Return error response
        return Response(
            error={
                "type": "request_rejected",
                "message": "Your request was rejected due to security concerns.",
                "reason": reason,
                "appeal_url": "https://gateway.example.com/appeals"
            },
            status_code=403
        )

    async def _add_to_review_queue(self, request: RequestContext,
                                    assessment: dict):
        """Add rejected request to human review queue."""
        # Store in review queue database
        await review_queue_db.insert({
            "request": request.to_dict(),
            "assessment": assessment,
            "status": "pending_review",
            "created_at": datetime.utcnow()
        })
```

---

## Escalation & Monitoring

### Escalation Actions

```python
class EscalationAction(Enum):
    """Possible escalation actions."""
    ALLOW = "allow"                        # Normal processing
    ALLOW_WITH_MONITORING = "monitor"      # Log everything, watch closely
    INVOKE_ADDITIONAL_CHECKS = "check"     # Run more validators
    RATE_LIMIT = "throttle"                # Slow down user
    REJECT = "reject"                      # Block request
    ESCALATE_TO_HUMAN = "human"            # Manual review queue
    BAN_USER = "ban"                       # Permanent block


class EscalationEngine:
    """Handle escalation actions."""

    async def execute_action(self, action: EscalationAction,
                             request: RequestContext,
                             assessment: ThreatAssessment):
        """Execute escalation action."""

        handlers = {
            EscalationAction.ALLOW: self._allow,
            EscalationAction.ALLOW_WITH_MONITORING: self._monitor,
            EscalationAction.INVOKE_ADDITIONAL_CHECKS: self._additional_checks,
            EscalationAction.RATE_LIMIT: self._rate_limit,
            EscalationAction.REJECT: self._reject,
            EscalationAction.ESCALATE_TO_HUMAN: self._human_review,
            EscalationAction.BAN_USER: self._ban_user
        }

        handler = handlers[action]
        await handler(request, assessment)

    async def _allow(self, request: RequestContext, assessment: ThreatAssessment):
        """Normal processing."""
        pass  # Continue with normal flow

    async def _monitor(self, request: RequestContext, assessment: ThreatAssessment):
        """Elevated monitoring."""
        # Set monitoring flag in context
        request.metadata["monitoring_level"] = "elevated"

        # Enable verbose logging
        logger.info(
            "Request under elevated monitoring",
            extra={
                "request_id": request.id,
                "threat_level": assessment.score.get_level(),
                "reasoning": assessment.reasoning
            }
        )

    async def _additional_checks(self, request: RequestContext,
                                  assessment: ThreatAssessment):
        """Run additional security checks."""
        # This is already handled in ThreatAssessmentEngine
        pass

    async def _rate_limit(self, request: RequestContext,
                          assessment: ThreatAssessment):
        """Apply rate limiting."""
        user_id = request.metadata.get("user_id")

        # Reduce rate limit for this user
        await rate_limiter.set_limit(
            user_id=user_id,
            limit=10,  # Reduce to 10 req/min
            duration=3600  # For 1 hour
        )

        logger.warning(f"Rate limit applied to user {user_id}")

    async def _reject(self, request: RequestContext,
                      assessment: ThreatAssessment):
        """Reject request."""
        raise RequestRejected(
            reason=assessment.reasoning[0] if assessment.reasoning else "Security violation",
            assessment=assessment.to_dict()
        )

    async def _human_review(self, request: RequestContext,
                            assessment: ThreatAssessment):
        """Escalate to human review."""
        # Add to review queue
        await review_queue.add({
            "request": request.to_dict(),
            "assessment": assessment.to_dict(),
            "status": "pending_review",
            "priority": "high" if assessment.score.score > 0.8 else "medium"
        })

        # Optionally: Send notification to security team
        await notifications.send_alert(
            channel="security",
            message=f"High-risk request requires review: {request.id}"
        )

        # For now, reject the request (manual approval needed)
        raise RequestRejected(
            reason="Request flagged for manual review",
            review_id=request.id
        )

    async def _ban_user(self, request: RequestContext,
                        assessment: ThreatAssessment):
        """Permanently ban user."""
        user_id = request.metadata.get("user_id")
        ip_address = request.metadata.get("ip_address")

        # Add to ban list
        await ban_list.add(user_id=user_id, ip_address=ip_address)

        logger.critical(
            f"User banned: {user_id} (IP: {ip_address})",
            extra={"assessment": assessment.to_dict()}
        )

        raise UserBanned(user_id=user_id)
```

### Monitoring & Alerting

```python
class MonitoringSystem:
    """Monitor request patterns and send alerts."""

    def __init__(self):
        self.alert_channels = self._init_alert_channels()

    async def monitor_request(self, request: RequestContext,
                              monitoring_level: str):
        """Monitor request with specified level."""

        if monitoring_level == "normal":
            # Standard logging only
            pass

        elif monitoring_level == "elevated":
            # Log everything
            logger.info(
                "Elevated monitoring",
                extra={
                    "request_id": request.id,
                    "user_id": request.metadata.get("user_id"),
                    "full_request": request.to_dict()
                }
            )

        elif monitoring_level == "high":
            # Real-time alerts
            await self._send_alert(
                level="warning",
                message=f"High-risk request detected: {request.id}"
            )

    async def check_anomalies(self):
        """Check for system-wide anomalies."""

        # Check rejection rate
        rejection_rate = await metrics.get_rejection_rate(window="5m")
        if rejection_rate > 0.1:  # >10% rejections
            await self._send_alert(
                level="warning",
                message=f"High rejection rate: {rejection_rate:.1%}"
            )

        # Check for coordinated attacks
        recent_rejections = await metrics.get_recent_rejections(limit=100)
        if self._detect_coordinated_attack(recent_rejections):
            await self._send_alert(
                level="critical",
                message="Potential coordinated attack detected"
            )

    def _detect_coordinated_attack(self, rejections: List[dict]) -> bool:
        """Detect patterns indicating coordinated attack."""
        # Check for multiple users from same IP
        # Check for similar attack patterns
        # Check for timing patterns
        pass

    async def _send_alert(self, level: str, message: str):
        """Send alert to configured channels."""
        for channel in self.alert_channels:
            await channel.send(level=level, message=message)
```

---

## Implementation Details

### Plugin Integration

```python
class IntelligentOrchestrationPlugin(BasePlugin):
    """Main plugin integrating all orchestration components."""

    def __init__(self, config: dict):
        super().__init__(config)

        # Initialize components
        self.intent_detector = IntentDetector()
        self.checker_registry = self._init_checker_registry()
        self.threat_engine = ThreatAssessmentEngine(self.checker_registry)
        self.dispatching_engine = DispatchingEngine(config)
        self.escalation_engine = EscalationEngine()
        self.monitoring = MonitoringSystem()

    async def before_request(self, ctx: RequestContext):
        """
        Orchestrate entire detection → assessment → dispatching flow.
        """

        # Stage 1: Intent Detection
        intent_result = await self.intent_detector.detect(ctx)
        ctx.metadata["intent"] = intent_result.to_dict()

        # Stage 2: Threat Assessment
        initial_score = ThreatScore()
        if intent_result.is_yellow_flag:
            initial_score.add(0.3, "Intent flagged as suspicious")
        if intent_result.is_red_flag:
            initial_score.add(0.7, "Intent flagged as malicious")

        threat_assessment = await self.threat_engine.assess(ctx, initial_score)
        ctx.metadata["threat_assessment"] = threat_assessment.to_dict()

        # Stage 3: Escalation (if needed)
        await self.escalation_engine.execute_action(
            threat_assessment.action,
            ctx,
            threat_assessment
        )

        # Stage 4: Dispatching
        dispatch_result = await self.dispatching_engine.dispatch(
            ctx,
            intent_result,
            threat_assessment
        )
        ctx.metadata["dispatch"] = dispatch_result.to_dict()

        # Handle non-LLM dispatching
        if dispatch_result.handler != "llm":
            handler = self.dispatching_engine.handlers[dispatch_result.handler]
            response = await handler.handle(ctx, **dispatch_result.metadata)

            # Stop pipeline early (cache hit, rejection, etc.)
            ctx.response = response
            ctx.stop_pipeline = True
            return

        # LLM dispatching continues to normal pipeline
        ctx.metadata["monitoring_level"] = dispatch_result.metadata["monitoring_level"]

    async def after_response(self, ctx: RequestContext):
        """Monitor response and update metrics."""

        # Monitor if elevated
        monitoring_level = ctx.metadata.get("monitoring_level", "normal")
        await self.monitoring.monitor_request(ctx, monitoring_level)

        # Update metrics
        self._update_metrics(ctx)

    def _init_checker_registry(self) -> CheckerRegistry:
        """Initialize checker registry with all available checkers."""
        registry = CheckerRegistry()

        # Fast checkers
        registry.register(RegexPatternChecker(self.config), "fast")

        # Medium checkers
        registry.register(ModerationAPIChecker(self.config), "medium")
        registry.register(JailbreakDetectorChecker(self.config), "medium")
        registry.register(SemanticSimilarityChecker(self.config), "medium")

        # Slow checkers
        registry.register(LLMIntentAnalysisChecker(self.config), "slow")
        registry.register(UserBehaviorAnalysisChecker(self.config), "slow")
        registry.register(ThreatIntelligenceChecker(self.config), "slow")

        return registry
```

### Configuration

```yaml
# config/plugins.yaml

- name: intelligent_orchestration
  enabled: true
  priority: 5  # Run early in pipeline
  class: plugins.intelligent_orchestration.IntelligentOrchestrationPlugin
  config:
    # Intent Detection
    intent_detection:
      enable_ml_classifier: true
      enable_llm_semantic: true  # Expensive, only for flagged requests
      confidence_threshold: 0.7

    # Threat Assessment
    threat_assessment:
      yellow_flag_threshold: 0.2
      red_flag_threshold: 0.7
      enable_progressive_checking: true

    # Checkers
    checkers:
      fast:
        - regex_pattern
      medium:
        - moderation_api
        - jailbreak_detector
        - semantic_similarity
      slow:
        - llm_intent_analysis
        - user_behavior_analysis
        - threat_intelligence

    # Dispatching
    dispatching:
      enable_simple_cache: true
      enable_semantic_cache: true
      enable_direct_response: true
      enable_tool_mcp: true

      semantic_cache:
        similarity_threshold: 0.95
        vector_db: "chroma"  # or "faiss", "pinecone"

      tool_mcp:
        enable_mcp: true
        mcp_servers:
          - name: "filesystem"
            endpoint: "http://localhost:3001"
          - name: "browser"
            endpoint: "http://localhost:3002"

    # LLM Routing
    routing:
      strategy: "hybrid"  # cost, performance, quality, hybrid
      weights:
        cost: 0.6
        quality: 0.3
        performance: 0.1

      intent_routing_rules:
        code_generation:
          preferred_models: ["gpt-4", "claude-3-opus"]
          escalation_chain: ["gpt-4-turbo", "gpt-4", "claude-3-opus"]

        creative_writing:
          preferred_models: ["claude-3-opus", "gpt-4"]
          escalation_chain: ["claude-3-sonnet", "claude-3-opus", "gpt-4"]

        conversation:
          preferred_models: ["gpt-3.5-turbo", "gpt-4o-mini"]
          escalation_chain: ["gpt-3.5-turbo"]

    # Escalation
    escalation:
      quality_threshold: 0.7  # Below this, escalate
      max_escalations: 3
      enable_human_review: true
      review_queue_size: 100

    # Monitoring
    monitoring:
      enable_alerts: true
      alert_channels:
        - type: "email"
          recipients: ["security@example.com"]
        - type: "slack"
          webhook_url: "${SLACK_WEBHOOK_URL}"

      anomaly_detection:
        rejection_rate_threshold: 0.1  # 10%
        window: "5m"
```

---

## Open Questions

### 🔴 CRITICAL DECISIONS NEEDED

#### **Q1: MCP Integration Strategy**

**Question**: How should we integrate Model Context Protocol (MCP) for tool/plugin invocation?

**Options**:
1. **Native MCP Client**: Implement full MCP protocol support
   - Pros: Standard protocol, future-proof, ecosystem compatibility
   - Cons: More complex, dependency on MCP servers

2. **Simple Tool Registry**: Custom lightweight tool system
   - Pros: Simpler, faster, full control
   - Cons: Non-standard, limited ecosystem

3. **Hybrid Approach**: Both MCP + custom tools
   - Pros: Flexibility, gradual migration
   - Cons: Two systems to maintain

**Recommendation**: ?

---

#### **Q2: Semantic Cache Vector Database**

**Question**: Which vector database should we use for semantic caching?

**Options**:
1. **Chroma** - Python-native, simple
2. **Faiss** - Facebook's library, very fast
3. **Pinecone** - Managed service, scalable
4. **None** - Skip semantic cache for now

**Considerations**:
- Storage: Local vs Cloud
- Scale: 1k vs 1M cached requests
- Cost: Self-hosted vs Managed
- Latency: <100ms requirement

**Recommendation**: ?

---

#### **Q3: Human Review Queue Implementation**

**Question**: How should we implement the human review queue for flagged requests?

**Options**:
1. **Dashboard Page**: Add "Review Queue" tab to dashboard
   - Show pending requests
   - Approve/reject interface
   - Historical decisions

2. **External System**: Integrate with existing ticketing (Jira, etc.)

3. **Hybrid**: Dashboard for quick review, external for escalation

**Features Needed**:
- [ ] Queue management (FIFO, priority)
- [ ] Reviewer assignment
- [ ] Decision history
- [ ] Appeal process
- [ ] Metrics (false positive rate)

**Recommendation**: ?

---

#### **Q4: Threat Intelligence Feeds**

**Question**: Should we integrate external threat intelligence APIs?

**Potential Integrations**:
1. **AbuseIPDB** - IP reputation
2. **VirusTotal** - URL/domain reputation
3. **Prompt Injection Database** - Known attack patterns (if exists?)
4. **Custom Feed** - Build our own from detected attacks

**Trade-offs**:
- **Pros**: Better detection, crowd-sourced intelligence
- **Cons**: External dependency, latency, cost, privacy concerns

**Recommendation**: ?

---

### 🟡 DESIGN DECISIONS

#### **Q5: Intent Detection ML Model**

**Question**: What ML model should we use for intent classification?

**Options**:
1. **Fine-tuned DistilBERT**: Fast, accurate, self-hosted
2. **OpenAI Embeddings + Classifier**: Simple, but requires API
3. **LiteLLM + GPT-3.5**: Flexible, expensive
4. **Heuristics Only**: No ML, just rules

**Training Data**:
- Do we have labeled data for intents?
- Should we collect data first then train?
- Can we use synthetic data (generated by GPT-4)?

**Recommendation**: ?

---

#### **Q6: Quality Assessment Metrics**

**Question**: How should we assess LLM response quality for escalation decisions?

**Potential Metrics**:
1. **Length-based**: Too short/long
2. **Refusal detection**: "I don't know", "I cannot"
3. **Hallucination detection**: Fact-checking
4. **Relevance scoring**: Semantic similarity to query
5. **User feedback**: Thumbs up/down (post-hoc)
6. **LLM-as-judge**: Use another LLM to score (expensive!)

**Threshold**: What quality score triggers escalation?

**Recommendation**: ?

---

#### **Q7: Rate Limiting Strategy**

**Question**: How should rate limiting work with escalation?

**Current Behavior**:
- Global rate limit (all users)
- Per-key rate limit (AuthPlugin)

**Escalation Behavior**:
- Reduce limit when suspicious activity detected
- Gradual recovery if behavior improves?
- Permanent limit reduction?

**Configuration**:
```yaml
rate_limiting:
  normal: 100 req/min
  suspicious: 20 req/min
  high_risk: 5 req/min
  recovery_time: 1 hour
```

**Recommendation**: ?

---

### 🟢 IMPLEMENTATION QUESTIONS

#### **Q8: Progressive Checker Performance**

**Question**: What's the expected latency impact?

**Estimates**:
- Fast checkers: +5ms
- Medium checkers (yellow flag): +200ms
- Slow checkers (red flag): +800ms

**Acceptable Overhead**:
- Normal request (no flags): <10ms ✅
- Yellow flag request: <300ms ?
- Red flag request: <1000ms (acceptable since we reject?)

**Optimization Ideas**:
- Run checkers in parallel (async)
- Cache checker results
- Short-circuit on high-confidence

**Recommendation**: ?

---

#### **Q9: Audit Logging & Retention**

**Question**: What should we log and for how long?

**Log Everything**:
- Intent detection results
- Threat assessment scores
- Checker results
- Dispatching decisions
- Escalation actions
- Rejection reasons

**Retention Policy**:
- Normal requests: 30 days?
- Flagged requests: 90 days?
- Rejected requests: 1 year? (compliance)

**Storage**:
- SQLite (local)
- PostgreSQL (production)
- S3 (archival)

**Recommendation**: ?

---

#### **Q10: Semantic Cache Staleness**

**Question**: How do we handle stale cached responses?

**Problem**: Cached response might be outdated (e.g., "What's the weather today?")

**Solutions**:
1. **TTL per intent**: FAQs cache longer, time-sensitive shorter
2. **Freshness disclaimer**: Add timestamp to cached response
3. **Smart invalidation**: Detect time-sensitive queries and skip cache
4. **Hybrid**: Cache + LLM validation for time-sensitive

**Example TTLs**:
```yaml
semantic_cache_ttl:
  faq: 7 days
  code_generation: 1 day
  conversation: 1 hour
  time_sensitive: 0  # Never cache
```

**Recommendation**: ?

---

#### **Q11: Cost Tracking with Orchestration**

**Question**: How do we track costs accurately with all these handlers?

**Cost Sources**:
- LLM calls (OpenAI, Anthropic)
- Embeddings (semantic cache)
- Moderation API (free but rate limited)
- Intent analysis LLM calls (GPT-3.5)
- Tool/MCP invocations (external APIs)

**Tracking**:
- Per-request cost breakdown
- Cost attribution (which component)
- Savings from cache hits
- Savings from early rejection (avoided LLM cost)

**Dashboard**:
- "Orchestration saved you $X by rejecting/caching"

**Recommendation**: ?

---

#### **Q12: Testing Strategy**

**Question**: How do we test this complex system?

**Test Types Needed**:
1. **Unit tests**: Each checker, handler, engine
2. **Integration tests**: Full pipeline with mocked LLMs
3. **Performance tests**: Latency benchmarks
4. **Security tests**: Known attack patterns (jailbreaks, injections)
5. **False positive tests**: Benign requests shouldn't be flagged

**Test Data**:
- Need dataset of benign requests
- Need dataset of malicious requests
- Need dataset of ambiguous requests

**Continuous Testing**:
- Monitor false positive rate in production
- A/B test new checkers
- Gradually roll out new rules

**Recommendation**: ?

---

### 🔵 OPTIONAL FEATURES

#### **Q13: User Reputation System**

**Question**: Should we build user reputation scores?

**Concept**:
- Track user behavior over time
- Good actors get higher trust → fewer checks
- Bad actors get flagged earlier → more checks

**Reputation Factors**:
- Request history (clean vs flagged)
- Appeal outcomes (false positives)
- Feedback (thumbs up/down)
- Time since first request

**Benefits**:
- Reduce false positives for trusted users
- Faster for good actors (skip expensive checks)
- Better detection for new/suspicious users

**Recommendation**: Implement now or later?

---

#### **Q14: Explainability & Appeals**

**Question**: How transparent should we be about rejections?

**Current Approach**: Generic "security concerns" message

**Alternative**: Detailed explanation
```json
{
  "error": "request_rejected",
  "reason": "Potential prompt injection detected",
  "details": {
    "triggered_rules": ["ignore_instructions_pattern"],
    "confidence": 0.85,
    "appeal_url": "https://gateway.example.com/appeals"
  }
}
```

**Trade-offs**:
- **Pros**: Transparency, user trust, better appeals
- **Cons**: Attackers learn our rules, can craft better attacks

**Recommendation**: ?

---

#### **Q15: Anomaly Detection & Learning**

**Question**: Should the system learn from rejected requests?

**Concept**:
- Detect new attack patterns automatically
- Update rules based on real traffic
- Adaptive system that improves over time

**Approaches**:
1. **Supervised Learning**: Human labels → train models
2. **Unsupervised**: Cluster similar attacks → auto-create rules
3. **Reinforcement Learning**: Learn from appeal outcomes

**Challenges**:
- Requires ML infrastructure
- Risk of overfitting to false positives
- Concept drift (attack patterns evolve)

**Recommendation**: Future phase or not needed?

---

## Next Steps

### Immediate Actions

1. **Answer Critical Questions** (Q1-Q4)
   - MCP integration strategy
   - Vector DB selection
   - Human review queue design
   - Threat intelligence decision

2. **Create Implementation Plan**
   - Phase 5.5.1: Intent Detection (1 week)
   - Phase 5.5.2: Dispatching Engine (1 week)
   - Phase 5.5.3: Escalation System (1 week)

3. **Build MVP**
   - Start with simplest viable implementation
   - Fast checkers only (regex patterns)
   - Simple cache + LLM dispatching
   - Basic rejection handler
   - No semantic cache / MCP / human review yet

4. **Iterate**
   - Add medium checkers (moderation API)
   - Add semantic cache (if vector DB chosen)
   - Add human review queue
   - Add monitoring & alerts

---

## Summary

This document outlines a comprehensive **Intelligent Request Orchestration System** that transforms the AI Aikido Gateway into an enterprise-grade platform with:

✅ **Multi-stage threat detection** (fast → medium → slow checkers)
✅ **Intelligent dispatching** (cache, tools, LLMs, rejection)
✅ **Progressive escalation** (yellow/red flags → additional checks)
✅ **Quality-based routing** (intent → best model → fallback chain)
✅ **Comprehensive monitoring** (audit logs, alerts, anomaly detection)

**Key Innovation**: Not just LLM routing, but **holistic request orchestration** that decides if an LLM is even needed, and handles security threats proactively.

**Next Step**: Review open questions and make decisions to proceed with implementation.
