# Trinetri AI — Humanization & Next-Gen AI Experience Roadmap

> **Purpose of This Document:**  
> This is a self-contained, step-by-step execution blueprint for the next engineering agent. Every phase addresses a specific human-experience gap identified in our audit of the `prompts/`, `engines/trinetri_orchestrator.py`, `engines/ai_context.py`, `services/llm.py`, and `frontend/js/app.js` pipeline.  
>
> **Core Engineering Constraints to Preserve at All Times:**
> 1. **Zero Emojis** inside any LLM prompt template or rendered Pillar 1 / Three Eyes cards (`tests/test_api.py` enforces regex assertions against unicode emojis).
> 2. **Zero-Hallucination Math:** Never allow the LLM to calculate degrees, house cusps, or dasha dates; all math stays deterministic in Python.
> 3. **Backward-Compatible JSON Keys:** Keep existing JSON schema keys (`constitution`, `traits`, `the_why`, `qualities`, `operating_manual`, `growth_levers`, `arenas`, `astrological_proof`, etc.) intact so existing tests and frontend fallbacks continue to pass.
> 4. **Run `.venv\Scripts\pytest.exe -v` and `node -c frontend/js/app.js`** after every phase.

---

## Overview of the 7 Phases

| Phase | Focus Area | Primary Files Affected | Human Impact |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **De-Biasing Schema Examples & Softening Tone** | `prompts/*.py`, `engines/trinetri_orchestrator.py` | Stops every person from sounding like a "Stoic Software Architect"; replaces productivity-bro buzzwords with warm, everyday human insight. |
| **Phase 2** | **Giving the Three Eyes Distinct Human Lenses** | `prompts/parashari_prompt.py`, `prompts/kp_prompt.py`, `prompts/jaimini_prompt.py`, `frontend/js/app.js` | Eliminates "4x Déjà Vu" when clicking between Maha-Synthesis, Parashari, KP, and Jaimini tabs. |
| **Phase 3** | **Fixing Pillar Switching & Three-Eyes Cache Bleed** | `frontend/js/app.js`, `engines/trinetri_orchestrator.py` | Clicking Career, Relationships, or Dasha no longer shows Pillar 1's Personality Deck under a broken banner or reuses generic personality verdicts. |
| **Phase 4** | **Tailored Chapter Blueprints for Pillars 2, 3 & 4** | `prompts/synthesizer_prompt.py`, `engines/trinetri_orchestrator.py` | Users consulting on Love/Marriage no longer have to read chapters about workplace management; every pillar gets its own dedicated 5-chapter arc. |
| **Phase 5** | **Human Stage-Progress Streaming UI (No Raw JSON)** | `frontend/js/app.js`, `frontend/css/style.css` | Replaces scrolling raw JSON code during Pillar 1 generation with a live stage checklist and an instant 2-second Archetype + Verdict reveal. |
| **Phase 6** | **Connecting the Chat Mentor to the Active Reading** | `main.py`, `engines/trinetri_orchestrator.py`, `prompts/chat_prompt.py`, `frontend/js/app.js` | When a user asks *"Tell me more about the shadow you just mentioned"*, the chat AI actually remembers the reading on screen. |
| **Phase 7** | **Human-Voiced Conversation Starters in Chat** | `frontend/index.html`, `frontend/js/app.js`, `frontend/css/style.css` | Gives users 4 warm, one-click questions in the chat drawer so they never face writer's block. |

---

## Phase 1: De-Biasing Schema Examples & Softening the "Stoic Architect" Voice

### The Problem
1. Across `prompts/synthesizer_prompt.py`, `prompts/parashari_prompt.py`, `prompts/kp_prompt.py`, and `prompts/jaimini_prompt.py`, almost every JSON schema placeholder example uses stoic engineering/executive terms:
   - `"The Grounded Architect"`, `"The Resilient Strategist"`, `"The Sovereign Builder"`, `"The Precision Strategist"`, `"Calculated Architect with High Standards"`, `"Quiet Master Craftsman"`, `"Vetted Inner Sanctuary"`.
   - Because LLMs heavily mimic the tone of prompt examples, even a deeply emotional Water-dominant native or a spontaneous Fire-dominant artist gets painted as a "Resilient Architect who builds checklists."
2. Startup/productivity jargon (`"10x habit"`, `"high-leverage multiplier"`, `"execution velocity"`, `"unfair advantage"`, `"empirical deconstruction"`, `"irreversible execution"`) makes the reading feel like a corporate performance review rather than a wise human consultation.
3. In `engines/trinetri_orchestrator.py` (`compute_constitutional_blueprint`, lines 227–252), `paradox_narrative` only has **4 hardcoded `if/elif/else` buckets** based solely on whether Lagna and Moon are Earth/Water vs. Fire/Air. Two completely different people with Earth rising and Air Moon receive the exact same verbatim inner paradox.

### Step-by-Step Implementation
1. **Update `WHAT_WHY_HOW_SYSTEM_PROMPT` in `prompts/synthesizer_prompt.py`**:
   - Add **Rule 7: ANTI-CLONE & PLAIN-SPOKEN WARMTH LAW**:
     - Explicitly instruct the LLM: *"Never default to calling everyone an 'Architect', 'Strategist', 'Sovereign', or 'Builder' unless their chart is genuinely Saturn/Capricorn/Virgo dominant. Match your tone and archetype to their actual elemental and planetary nature—whether they are a tender caretaker, a fierce catalyst, a restless storyteller, a quiet healer, or a steady builder."*
     - Ban startup/hustle buzzwords: *"Avoid productivity-bro phrases like '10x habit', 'high-leverage multiplier', 'execution velocity', 'empirical deconstruction', or 'operating posture'. Write in warm, plainspoken, emotionally resonant everyday English."*
   - Diversify the schema placeholder examples inside `WHAT_WHY_HOW_SYSTEM_PROMPT`:
     - `archetype`: `"<2 to 3 word human identity matching their actual chart, e.g. 'The Quiet Harbor', 'The Restless Spark', 'The Steady Craftsman', 'The Fierce Protector'>"`
     - `natural_instinct_tag`, `emotional_anchor_tag`, `core_drive_tag`, `deepest_hunger_tag`: Provide 2 contrasting examples (one soft/intuitive, one structured/active) instead of a single stoic example.
     - Replace `"The single most transformative 10x habit"` in `golden_lever` with `"The single daily shift that unlocks the most peace and momentum for how you are wired"`.
2. **Enrich `compute_constitutional_blueprint` in `engines/trinetri_orchestrator.py` (lines 211–263)**:
   - Include the specific **Lagna Sign, Moon Sign, Moon Nakshatra, and Moon House** in the paradox context, plus any planets conjunct Moon or Ascendant.
   - Expand the paradox buckets to account for Same-Element combinations (Fire-Fire, Earth-Earth, Air-Air, Water-Water) and specific Water/Fire, Air/Water, Earth/Water nuances.
   - In `build_constitutional_ground_truth` (line 293), keep the exact requirement for `constitution.elements` and `constitution.ayurvedic_prakriti` labels, while instructing the LLM to weave the native's specific Lagna/Moon/Nakshatra/Ketu-Rahu houses into `the_why.inner_paradox` so no two charts ever read like a copy-paste template.
3. **Soften UI Card Sub-Labels in `frontend/js/app.js`**:
   - In `renderArenaPanel` (lines 2727–2756), soften cold military/corporate subtitles while keeping the outer tags intact for test compatibility:
     - Change `"Default Operating Posture"` $\to$ `"How You Naturally Show Up"`
     - Change `"High-Leverage Multiplier"` $\to$ `"The One Rule That Protects Your Best Self"`

### Verification
- Run `.venv\Scripts\pytest.exe -v` (ensure `test_three_eyes_wwh_deck_assets_and_prompts` and `test_interactive_polarity_and_arena_switcher` pass with 0 emojis and all required schema keys intact).

---

## Phase 2: Giving the Three Eyes Distinct Human Lenses (Ending "4x Déjà Vu")

### The Problem
In Pillar 1 (`What, Why and How You Are`), when a user clicks from **Maha-Synthesis** to **Parashari (BPHS)**, **KP Stellar**, and **Jaimini Sutras**, all three Eye prompts currently ask for the exact same personality summary (`what_you_are`, `why_you_are`, `how_you_operate`) without astrological terms. As a result, all 4 tabs read like slightly reworded versions of the same personality test.

### Step-by-Step Implementation
Keep the exact JSON schema keys (`school`, `archetype`, `summary_verdict`, `metrics`, `what_you_are`, `why_you_are`, `how_you_operate`, `astrological_proof`) so `renderSchoolEyeDeck` and all tests work seamlessly, **but specialize the human question each school answers**:

1. **Eye 1 — `EYE_1_PARASHARI_WWH_SYSTEM_PROMPT` (`prompts/parashari_prompt.py`)**:
   - **Human Lens:** *"Your Roots, Conditioning & Character Foundation"*
   - `what_you_are`: Focus on **Innate Temperament & Upbringing** — who you have always been since childhood, your natural stamina, and how your inner character holds up when tested (`headline`: e.g. *"Your Root Temperament & Inner Backbone"*).
   - `why_you_are`: Focus on **Lifelong Blessings vs. Recurring Life Lessons** — the natural protection and grace you carry vs. the recurring emotional or worldly tests life uses to mature you.
   - `how_you_operate`: Focus on **Your Current Multi-Year Life Season** — what the current major chapter of your life is asking you to outgrow and build.

2. **Eye 2 — `EYE_2_KP_WWH_SYSTEM_PROMPT` (`prompts/kp_prompt.py`)**:
   - **Human Lens:** *"Real-World Outcomes, Open Doors & Timing Triggers"* (Zero personality fluff—focus on *results*!)
   - `what_you_are`: Focus on **How Results Actually Materialize in Your Life** — why certain things (work, money, or agreements) come together quickly for you while other areas always seem to require a second or third attempt.
   - `why_you_are`: Focus on **Your Green Lights vs. Hidden Bottlenecks** — `strengths` = the concrete arenas where doors swing wide open when you knock; `friction_points` = the exact last-minute delays, paperwork snags, or overthinking traps that stall your momentum (and how to bypass them).
   - `how_you_operate`: Focus on **What Is Unlocked Right Now** — what concrete actions, negotiations, or decisions are favored in your current sub-period vs. what to avoid forcing.

3. **Eye 3 — `EYE_3_JAIMINI_WWH_SYSTEM_PROMPT` (`prompts/jaimini_prompt.py`)**:
   - **Human Lens:** *"The Public Mask vs. The Private Soul"*
   - `what_you_are`: Focus on **First Impressions vs. Who You Are When the Door Closes** — the contrast between how colleagues, strangers, and society perceive your status/demeanor (`Arudha Lagna`) vs. the private standards and quiet longings of your soul (`Atmakaraka`).
   - `why_you_are`: Focus on **What Feeds Your Soul vs. Worldly Detours** — `strengths` = where your inner calling and public role align; `friction_points` = where chasing external approval, image, or rivalry (`Gnatikaraka`) drains your spirit.
   - `how_you_operate`: Focus on **Your Mirror in Intimacy & Soul Alignment** — what kind of partner or close ally mirrors your truest self (`Darakaraka` / `Upapada`), and how to keep your outer reputation honest to your inner peace.

4. **Update `SCHOOL_METRIC_CONFIGS` in `frontend/js/app.js` (lines 3159–3225)**:
   - Update the section subtitles/tags in `renderSchoolEyeDeck` so the user immediately sees *why* each tab is different:
     - Parashari: *"Classical BPHS Lens — Your Roots, Conditioning & Character Foundation"*
     - KP Stellar: *"KP Stellar Lens — Real-World Doors, Bottlenecks & Action Timing"*
     - Jaimini Sutras: *"Jaimini Lens — Your Public Mask vs. Your Private Soul"*

### Verification
- Run `.venv\Scripts\pytest.exe -v` and `node -c frontend/js/app.js`.

---

## Phase 3: Fixing Pillar Switching & Three-Eyes Cache Bleed

### The Problem
1. **Frontend Bug (`frontend/js/app.js`, lines 3635–3637 & 3656–3662):**
   - When a user generates Pillar 1 (`comprehensive`), it caches the JSON Bento Deck (`WHAT_WHY_HOW_SYSTEM_PROMPT`).
   - When the user then clicks Pillar 2 (`career`), Pillar 3 (`relationships`), or Pillar 4 (`dasha`), `selectAiPillar()` sees `state.ai_readings_cache[compKey]` and calls `displayAiReadingFromComprehensive()`.
   - `displayAiReadingFromComprehensive()` puts a banner at the top saying *"Viewing Chapter 3: Career, Wealth & Professional Rise"*—and then renders the **Pillar 1 Identity Blueprint Bento Deck** underneath it and tries to scroll to `#chapter-3` (which doesn't exist in the Bento deck!).
2. **Backend Cache Bleed (`engines/trinetri_orchestrator.py`, lines 727–730):**
   - In `run_three_eyes()`, lines 728–730 say:
     ```python
     if not clean_query and macro_key in _THREE_EYES_CACHE:
         return _THREE_EYES_CACHE[macro_key]
     ```
   - `macro_key` is `f"{chart_fp}_comprehensive_"`. When `comprehensive` runs, the Three Eyes use `EYE_X_WWH_SYSTEM_PROMPT` (which outputs JSON decks focused on Pillar 1 "What, Why and How You Are").
   - When the user later generates `career`, `relationships`, or `dasha`, `run_three_eyes` returns the cached Pillar 1 WWH JSON instead of running `EYE_X_SYSTEM_PROMPT` focused on Career (10th house/AmK), Relationships (7th house/DK/UL), or Dasha!

### Step-by-Step Implementation
1. **Fix `run_three_eyes` in `engines/trinetri_orchestrator.py` (lines 721–731)**:
   - Remove the cross-pillar fallback `if not clean_query and macro_key in _THREE_EYES_CACHE:` (or restrict it so `comprehensive` WWH JSON is NEVER returned for non-`comprehensive` pillars).
   - Each pillar (`comprehensive`, `career`, `relationships`, `dasha`) has its own `cache_key = f"{chart_fp}_{pillar}_{clean_query}"`, so exact cache hits for the same pillar will still be instant (0 LLM calls), while switching to `career` or `relationships` will properly evaluate the Three Eyes for that specific life domain!
   - Check `tests/test_ai_hardening.py::test_three_eyes_cache_avoids_repeated_llm_calls` to see what it tests!
     - *Important Note:* Check `tests/test_ai_hardening.py` before removing `macro_key` reuse! If `test_three_eyes_cache_avoids_repeated_llm_calls` specifically tests that calling `comprehensive` and then `career` reuses the cache, inspect that test first and update either the test or the caching strategy accordingly.
2. **Fix `selectAiPillar` & `displayAiReadingFromComprehensive` in `frontend/js/app.js` (lines 3630–3705)**:
   - In `displayAiReadingFromComprehensive(readingData, pillar)`:
     - Check if `readingData.fullSynthesisMarkdown` is a `What, Why and How You Are` JSON deck (`metadata && (metadata.traits || metadata.the_why || metadata.archetype)`).
     - If it IS a WWH JSON deck (meaning it does NOT have Markdown `#chapter-2`, `#chapter-3`, `#chapter-4`), do **not** render the full WWH deck again with a broken *"Viewing Chapter 3"* banner!
     - Instead, render a clean, focused **Pillar Preview & Launch Card** that:
       1. Shows the relevant **Arena Snapshot** from the cached blueprint (e.g., for `career`, show the `work` Arena panel; for `relationships`, show the `relationships` Arena panel; for `dasha`, show the Operating Manual / Stress & Season summary).
       2. Clearly invites the user with a prominent call-to-action banner:
          - *"Here is your quick Career & Leadership snapshot from your core blueprint. Ready for your complete 5-Chapter Career, Wealth & Timing Consultation?"*
          - Button: **`✦ Generate Full Career & Wealth Reading ➔`** (calling `triggerAiSynthesis(true)`).
     - If `readingData` is a multi-chapter Markdown reading that actually contains `#chapter-${info.chapter}`, keep the smooth scroll to `#chapter-${info.chapter}` behavior.

### Verification
- Run `.venv\Scripts\pytest.exe -v` (especially `tests/test_ai_hardening.py` and `tests/test_api.py`).

---

## Phase 4: Tailored Chapter Blueprints for Career (Pillar 2), Relationships (Pillar 3), and Dasha (Pillar 4)

### The Problem
Currently, `MAHA_SYNTHESIZER_SYSTEM_PROMPT` in `prompts/synthesizer_prompt.py` hardcodes the same 6 chapters for every non-comprehensive pillar:
- Chapter 1: Who You Are Underneath
- Chapter 2: Current Life Season
- Chapter 3: Career & Vocation
- Chapter 4: Love & Intimacy
- Chapter 5: The Road Ahead
- Chapter 6: Daily Practices

When someone clicks **Relationships, Marriage & Compatibility** and generates a dedicated reading, they are forced to read chapters about their career and workplace politics before getting to love.

### Step-by-Step Implementation
1. **In `prompts/synthesizer_prompt.py`**, keep `MAHA_SYNTHESIZER_SYSTEM_PROMPT` as the base mentor persona and laws (so any test importing `MAHA_SYNTHESIZER_SYSTEM_PROMPT` and checking for `## Chapter 1:` continues to pass), and add pillar-specific chapter blueprints inside `build_synthesizer_prompt()` based on `pillar_key`:

   - **When `pillar_key == "career"` (`Career, Wealth & Professional Rise`)**:
     Instruct the synthesizer to use this 5-chapter structure:
     - `# Your Vocational & Financial Blueprint`
     - `## Chapter 1: What You Were Built to Build — Your Natural Work Genius` (How you work best, autonomy vs. structure, and the craft where you naturally excel)
     - `## Chapter 2: Authority, Office Politics & How You Lead` (Your relationship with bosses, hierarchy, delegation, and the work environment that brings out your best)
     - `## Chapter 3: How Money Flows to You & Your Financial Blindspot` (Wealth creation patterns, risk tolerance, and the financial leak to guard against)
     - `## Chapter 4: Your Career Weather Report — Key Timings (Next 18–24 Months)` (Concrete dated windows from active Dashas and transits for promotions, job switches, launches, or consolidation)
     - `## Chapter 5: Grounded Career Moves & Daily Anchors` (Practical workplace adjustments and daily habits)
     - `## Astrological Footnotes & Technical Derivations`

   - **When `pillar_key == "relationships"` (`Relationships, Marriage & Soul Compatibility`)**:
     Instruct the synthesizer to use this 5-chapter structure:
     - `# The Heart's Mirror: Love, Intimacy & Partnership`
     - `## Chapter 1: How Your Heart Is Wired — What You Need to Feel Loved` (What emotional safety looks like to you, and the quiet ways you show devotion)
     - `## Chapter 2: Your Protective Walls & Recurring Relationship Patterns` (What makes you shut down, test your partner, or pull away—and how to break the cycle)
     - `## Chapter 3: The Partner Who Truly Fits Your Soul` (The character, emotional rhythm, and real-life dynamic of the person who brings you peace rather than drama)
     - `## Chapter 4: Relationship Timing & Shifts (Next 18–24 Months)` (Concrete dated windows for deepening commitment, healing friction, or meeting someone significant)
     - `## Chapter 5: Protecting Intimacy — Practical Heart Anchors` (Real-time habits for conflict, vulnerability, and trust)
     - `## Astrological Footnotes & Technical Derivations`

   - **When `pillar_key == "dasha"` (`Current Dasha & Timing of Upcoming Shifts`)**:
     Instruct the synthesizer to use this 5-chapter structure:
     - `# Your Living Timeline: The Current Season & Road Ahead`
     - `## Chapter 1: Making Sense of Right Now — Why This Season Feels the Way It Does` (Validating their recent emotional and external reality under the active Mahadasha/Antardasha)
     - `## Chapter 2: What Life Is Asking You to Shed vs. Build` (The deeper purpose of this period—what old habits or attachments are expiring)
     - `## Chapter 3: Your 24-Month Timeline — Key Windows & Turning Points` (Clear, dated breakdown of the current and upcoming Antardashas and major Saturn/Jupiter/Rahu transits)
     - `## Chapter 4: How to Move With the Current — When to Push vs. Pause` (Practical strategy for career, money, and relationships during this specific window)
     - `## Chapter 5: Grounded Anchors for This Life Season` (Simple daily practices to steady your energy during these transits)
     - `## Astrological Footnotes & Technical Derivations`

   - **When `custom_query` is provided**:
     Explicitly instruct the synthesizer to open **Chapter 1** by directly and thoroughly answering the seeker's exact custom question in plain, compassionate human terms before expanding into timing and chapters.

### Verification
- Run `.venv\Scripts\pytest.exe -v` and confirm all prompt assertions and zero-emoji checks pass.

---

## Phase 5: Replacing the Raw JSON Stream with a Live Human Stage-Progress Experience

### The Problem
In `frontend/js/app.js` (`renderSynthesisProgressive`, lines 3547–3561), while Pillar 1 streams its 3,500-token JSON object, `JSON.parse()` cannot succeed until the final `}` arrives. During those 10–15 seconds, line 3558 renders:
```javascript
${escapeHtml(trimmed.slice(-350))}
```
The user stares at raw JSON syntax (`"tripwire": "...", "defuser": "..."`) scrolling in a monospace box, which breaks the feeling of a wise human consultation and spoils fragments of the reading out of context.

### Step-by-Step Implementation
1. **Update `renderSynthesisProgressive(markdown)` in `frontend/js/app.js` (lines 3531–3566)**:
   - While `trimmed.startsWith("```json") || trimmed.startsWith("{")` and `metadata` is not yet fully parsed:
     - Use lightweight regexes on `trimmed` to extract early fields that arrive within the first 2 seconds of streaming:
       - `const archMatch = trimmed.match(/"archetype"\s*:\s*"([^"]+)"/);`
       - `const verdMatch = trimmed.match(/"summary_verdict"\s*:\s*"([^"]+)"/);`
     - Check which sections have started streaming by testing for key presence in `trimmed`:
       - Stage 1: `"constitution"` $\to$ *"Reading your elemental balance & inner temperament"*
       - Stage 2: `"traits"` $\to$ *"Mapping your emotional armor & cognitive reflexes"*
       - Stage 3: `"the_why"` $\to$ *"Uncovering your core inner paradox & growth edge"*
       - Stage 4: `"qualities"` $\to$ *"Identifying your natural gifts & blindspots"*
       - Stage 5: `"arenas"` $\to$ *"Building your work, love, and pressure arenas"*
       - Stage 6: `"astrological_proof"` $\to$ *"Compiling classical BPHS, KP & Jaimini footnotes"*
     - Render an elegant, warm **Live Blueprint Assembly Card** showing:
       - If `archMatch` / `verdMatch` have arrived: A live preview banner revealing their **Archetype** and **Summary Verdict** right away so the user has something meaningful to read after just 2 seconds!
       - The 6-step progress checklist where completed stages show `[✓]`, the active stage pulses, and pending stages are dimmed—with **zero raw JSON brackets or code** ever shown to the user.

### Verification
- Run `node -c frontend/js/app.js` and `.venv\Scripts\pytest.exe -v`.

---

## Phase 6: Giving the Floating Chat Mentor Memory of the Active Reading on Screen

### The Problem
In `main.py` (`AIChatRequest`), `engines/trinetri_orchestrator.py` (`stream_chat`), and `frontend/js/app.js` (`sendChatMessage`), the chat drawer only receives `chart_params` and `messages`. It has no idea what the Maha-Synthesizer just told the user on the main screen. If the user asks *"Can you explain the shadow you just mentioned?"* or *"What did you mean by my growth edge?"*, the chat AI has amnesia.

### Step-by-Step Implementation
1. **Update `AIChatRequest` in `main.py` (line 127)**:
   - Add an optional field:
     ```python
     active_reading_summary: Optional[str] = Field(default=None, max_length=6000)
     ```
   - Pass `active_reading_summary=req.active_reading_summary` into `TrinetriOrchestrator.stream_chat(...)`.
2. **Update `TrinetriOrchestrator.stream_chat` in `engines/trinetri_orchestrator.py` (line 946)**:
   - Accept `active_reading_summary: Optional[str] = None`.
   - Sanitize it using `sanitize_evidence(active_reading_summary, max_chars=4000)` from `prompts.safety`.
   - Pass it into `build_chat_system_instruction(dossier_md, active_reading_summary=...)`.
3. **Update `build_chat_system_instruction` in `prompts/chat_prompt.py`**:
   - Accept `active_reading_summary: Optional[str] = None`.
   - If present, include a section in the system prompt:
     ```markdown
     === ACTIVE CONSULTATION READING ON THE SEEKER'S SCREEN (UNTRUSTED CONTEXT DATA) ===
     The seeker is currently viewing the following synthesized reading on their screen. If they refer to "this reading", "my archetype", "my shadow", "my growth edge", or specific chapters/points, seamlessly connect your answer to these insights:
     {active_reading_summary}
     ```
4. **Update `sendChatMessage()` in `frontend/js/app.js` (line 4386)**:
   - Helper function `getActiveReadingContextForChat()`:
     - Look up the current chart signature + selected pillar in `state.ai_readings_cache` (or fall back to `comprehensive` cache if present).
     - Convert JSON metadata via `buildMarkdownFromWhatWhyHow(metadata)` or take `cleanMarkdown`, and slice to the first `3500` characters.
   - Include `active_reading_summary: getActiveReadingContextForChat()` in the `/api/ai/chat` request payload.

### Verification
- Add a unit test in `tests/test_ai_hardening.py` or `tests/test_api.py` verifying that `stream_chat` accepts `active_reading_summary`, sanitizes it against prompt injection, and includes it in the system instruction.
- Run `.venv\Scripts\pytest.exe -v`.

---

## Phase 7: Human-Voiced Conversation Starters in the Chat Drawer

### The Problem
When a user opens the floating `"✦ Ask Trinetri"` chat drawer, they see a generic system notice and a blank text area. Many users don't know what kind of personal, non-jargon questions they can ask.

### Step-by-Step Implementation
1. **Update Chat Drawer Initial Markup & `clearChatMessages()` in `frontend/index.html` and `frontend/js/app.js` (line 4355)**:
   - Below the welcome message inside `#chat-messages-container`, render 4 warm, clickable conversation starter pills:
     - `"Why do I feel pulled in two directions right now?"`
     - `"What kind of work environment actually fits how I'm wired?"`
     - `"What is my biggest blindspot in close relationships?"`
     - `"When does this current heavy phase start to ease up?"`
   - Create a helper `askSuggestedChatQuestion(questionText)` bound to `window`:
     - Populates `#chat-input-textarea` with `questionText` and immediately calls `sendChatMessage()`.
2. **Style `.chat-starter-chips` in `frontend/css/style.css`**:
   - Clean, subtle pill buttons that work in both Light Mode and Dark Mode and disappear once the conversation begins.

### Verification
- Run `node -c frontend/js/app.js` and `.venv\Scripts\pytest.exe -v`.

---

## Final Checklist for Next Agent Before Completion
- [ ] All 7 phases implemented cleanly.
- [ ] Zero emojis in `prompts/synthesizer_prompt.py`, `prompts/parashari_prompt.py`, `prompts/kp_prompt.py`, `prompts/jaimini_prompt.py` (verified by regex test).
- [ ] `node -c frontend/js/app.js` exits with code 0.
- [ ] `.venv\Scripts\pytest.exe -v` passes 100% of existing + new tests.
- [ ] Bump asset cache version query string in `frontend/index.html` (e.g., `style.css?v=...` and `app.js?v=...`).
