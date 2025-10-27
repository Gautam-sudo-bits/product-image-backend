"""
Simplified Veo Prompt Generator
Generates prompts via Gemini, extracts veo_prompt strings, logs what Veo will receive
"""
import json
import time
import re
import math
from google import genai
from google.genai import types
from config import (
    TEXT_MODEL, 
    ALLOW_PEOPLE_IN_VIDEO, 
    SAVE_PROMPTS_TO_FILE, 
    DEFAULT_TOTAL_DURATION, 
    DEFAULT_SEGMENT_DURATION
)
total_duration = DEFAULT_TOTAL_DURATION
segment_duration = DEFAULT_SEGMENT_DURATION
num_segments = total_duration/segment_duration

class VeoPromptGenerator:
    """Generates Veo prompts via Gemini with verification logging"""
    
    def __init__(self, model=TEXT_MODEL):
        self.client = genai.Client()
        self.model = model
    
    def generate_simple_prompts(self, image_paths, product_overview, brand_guidelines, 
                                total_duration, segment_duration):
        """
        Generate prompts for Veo.
        Returns list of dicts, each with 'veo_prompt' string ready for Veo API.
        """
        num_segments = int(math.ceil(total_duration / segment_duration))
        primary_image_path = image_paths[0]
        
        # Build instruction (your long, effective instruction - unchanged)
        instruction = self._build_instruction(
            num_segments, product_overview, brand_guidelines, segment_duration
        )
        
        # Read image
        with open(primary_image_path, "rb") as f:
            image_data = f.read()
        mime = self._guess_mime(primary_image_path)
        
        # Call Gemini with retry
        for attempt in range(5):
            try:
                print(f"🎬 Generating {num_segments} segment prompts... (attempt {attempt + 1}/5)")
                
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        instruction,
                        types.Part.from_bytes(data=image_data, mime_type=mime)
                    ],
                )
                
                raw_text = (response.text or "").strip()
                if not raw_text:
                    print("⚠️ Empty response from LLM")
                    time.sleep((attempt + 1) * 10)
                    continue
                
                # Parse (JSON or text)
                prompts = self._parse_any_format(raw_text, num_segments, segment_duration)
                
                if not prompts:
                    print("⚠️ No valid prompts extracted")
                    time.sleep((attempt + 1) * 10)
                    continue
                
                # Display and verify
                self._display_prompts(prompts)
                self._verify_veo_prompts(prompts)
                
                if SAVE_PROMPTS_TO_FILE:
                    self._save_prompts(prompts)
                
                return prompts
                
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    print(f"⚠️ API error, retrying in {(attempt + 1) * 10}s...")
                    time.sleep((attempt + 1) * 10)
                else:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
        
        print("❌ Failed after 5 attempts")
        return None
    
    def _parse_any_format(self, text, num_segments, segment_duration):
        """Parse JSON array/object or raw text; always return list of dicts with veo_prompt"""
        # Strip markdown fences
        clean = re.sub(r'```(?:json)?', '', text).strip()
        
        # Try JSON first
        prompts = self._try_json(clean)
        
        # If not JSON, wrap as text
        if not prompts:
            print("ℹ️ Not JSON; wrapping as text prompts")
            prompts = [{
                "segment_number": i + 1,
                "veo_prompt": clean,
                "duration": segment_duration
            } for i in range(num_segments)]
        
        # Ensure each has veo_prompt string
        for i, p in enumerate(prompts):
            if not isinstance(p, dict):
                p = {"veo_prompt": str(p)}
                prompts[i] = p
            
            p.setdefault("segment_number", i + 1)
            p.setdefault("duration", segment_duration)
            
            # Extract veo_prompt if missing
            if not p.get("veo_prompt"):
                p["veo_prompt"] = self._extract_prompt_text(p)
        
        # Adjust count
        if len(prompts) < num_segments:
            while len(prompts) < num_segments:
                prompts.append({
                    "segment_number": len(prompts) + 1,
                    "veo_prompt": prompts[-1]["veo_prompt"] if prompts else "",
                    "duration": segment_duration
                })
        elif len(prompts) > num_segments:
            prompts = prompts[:num_segments]
        
        return prompts
    
    def _try_json(self, text):
        """Try to parse JSON array or object; return list or None"""
        # Find JSON boundaries
        arr_start, arr_end = text.find("["), text.rfind("]")
        obj_start, obj_end = text.find("{"), text.rfind("}")
        
        candidate = None
        if arr_start != -1 and arr_end > arr_start:
            candidate = text[arr_start:arr_end+1]
        elif obj_start != -1 and obj_end > obj_start:
            candidate = text[obj_start:obj_end+1]
        
        if not candidate:
            return None
        
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                print(f"✅ Parsed JSON array with {len(parsed)} items")
                return parsed
            elif isinstance(parsed, dict):
                print(f"✅ Parsed single JSON object")
                return [parsed]
        except:
            pass
        
        return None
    
    def _extract_prompt_text(self, segment_dict):
        """Build veo_prompt string from any available fields"""
        parts = []
        for key in ["veo_prompt", "description", "prompt", "scene_summary", "subject", "context", "action"]:
            val = segment_dict.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())
        return " ".join(parts) if parts else "Product commercial, 8 seconds"
    
    def _verify_veo_prompts(self, prompts):
        """Log exactly what will go to Veo"""
        print("\n" + "🔍 VEO TRANSMISSION VERIFICATION ".center(70, "="))
        for p in prompts:
            seg = p.get("segment_number", "?")
            prompt_str = p.get("veo_prompt", "")
            print(f"\n📤 SEGMENT {seg} → VEO API")
            print(f"   Length: {len(prompt_str)} chars")
            print(f"   First 200 chars: {prompt_str[:200]}...")
            print(f"   Last 150 chars: ...{prompt_str[-150:]}")
        print("="*70 + "\n")
    
    def _display_prompts(self, prompts):
        """Display prompts in readable format"""
        print("\n" + "="*70)
        print("📋 GENERATED PROMPTS")
        print("="*70)
        for p in prompts:
            seg = p.get("segment_number", "?")
            summary = p.get("scene_summary", "N/A")
            duration = p.get("duration", "?")
            prompt_len = len(p.get("veo_prompt", ""))
            print(f"\n🎬 Segment {seg}:")
            print(f"   Summary: {summary[:80]}...")
            print(f"   Duration: {duration}s")
            print(f"   Prompt length: {prompt_len} chars")
        print("="*70 + "\n")
    
    def _save_prompts(self, prompts, filename="veo_generated_prompts_vertex.json"):
        """Save prompts to JSON"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)
            print(f"✅ Prompts saved to '{filename}'")
        except Exception as e:
            print(f"❌ Error saving: {e}")
    
    def _guess_mime(self, path):
        """Guess MIME from extension"""
        p = path.lower()
        if p.endswith(".png"): return "image/png"
        if p.endswith((".jpg", ".jpeg")): return "image/jpeg"
        if p.endswith(".webp"): return "image/webp"
        return "image/png"
    
    def _build_instruction(self, num_segments, product_overview, brand_guidelines, segment_duration):
        """Your long, effective instruction - UNCHANGED"""
        
        safety_note = ""
        if not ALLOW_PEOPLE_IN_VIDEO:
            safety_note = """
CRITICAL SAFETY RULE:
- Never show people, hands, or product in operation
- Static product showcase only with camera movement
- Include "negative prompt: no people, no hands, not in use" in each veo_prompt
"""
        
        return f"""
---------------------------------------------------------
You are generating a Veo 3.1 prompt in JSON form for a fast-paced roundtable (turntable-style) product commercial. Output only a JSON array with exactly {{num_segments}} objects (one per 8-second segment). No extra text.

Inputs:
Product overview: {product_overview}
Brand_guidelines: {brand_guidelines}
Assume the best inpput fiels when unspecified.
- {{product_overview}}: official name; exact color(s); materials; textures/finishes; dimensions; printed/engraved marks; logo/wordmark placement; defining geometry; packaging if shown; environment constraints.
- {{brand_guidelines}}: palette; typography; logo usage; motion/animation principles; tone; forbidden treatments.
- {{total_duration}}: multiple of 8 seconds.
- {{aspect_ratio}}: e.g., 16:9, 9:16, 1:1.
- {{resolution}}: e.g., 4K.
- {{fps}}: e.g., 24 or 30.
- {{music_style}}: e.g., cinematic pulse, minimalist piano, percussive tech, and so on...
- {{audio_sfx}}: e.g., airy risers, whoosh, tactile clicks, subtle chimes, and so on...
- {{set_environment}}: round table/plinth material/finish/color; background (e.g., seamless black cove, white infinity, gradient); any minimal props (brand-approved only).
- {{lighting_mood}}: e.g., high-contrast rim + crisp speculars; soft wrap; neon edge accents; volumetric slits; and so on...
- {{camera_language_preferences}}: e.g., dolly-in, orbit (degrees + direction), tracking skim, crane drop, rack focus, whip-pan, low-angle hero, dutch (subtle), and so on...
- {{feature_priority}}: list of features to reveal; each converted to 2–3 words only.
- {{typography}}: brand font or exact fallback.
- {{palette_for_text}}: brand-approved colors with contrast guidance.
- {{plinth_rotation_allowed}}: true/false. If true, slow constant rotation only (not implying product operation).

Rules (apply to every frame, in every segment):
- ABSOLUTE PRODUCT FIDELITY: never alter/invent/misrepresent any feature, color, material, texture, finish, logo placement/kerning, or dimensions. No exploded/internal views. No variant colorways.
- NO HUMAN INTERACTION: no hands/faces/operators.
- NOT IN OPERATION: the product must remain stationary (only camera and/or plinth may move).
- TEXT OVERLAYS: exactly 2–3 words, rendered by Veo in-frame (no post). Use {{typography}} with {{palette_for_text}}. Place in safe areas without occluding critical details.
- CONTINUITY: identical product instance across all segments (same geometry, markings, finishes, colors).
- COLOR ACCURACY: lighting must not shift true product color. Control reflections/refractions physically plausibly.
- CLEANLINESS: no dust/fingerprints/smudges unless brand-authorized.

Camera/lighting guidance:
Favor slow tactile surface glides (dolly-in/orbit) to reveal the brand/logo under dramatic lighting, followed by fast transitions (whip-pan or on-beat cut) into the next feature. Maintain level horizon unless a subtle dutch is requested. Chain moves when needed. Use 35–50mm for hero, 85–105mm for macro textures. Use the {{camera_language_preferences}} list and the option catalogs (and so on...).

Output format:
Output only a JSON array with exactly {{num_segments}} segment objects.
Mini timestamps in a 8 second window is also allowed but each should follow the schema
Each object must use this schema:
{{
  "segment": <1-based integer>,
  "time_range": "MM:SS–MM:SS",              // e.g., "00:00–00:08" or "00:00–00:02"
  "scene_purpose": "One clear visual goal",
  "feature_label": "2–3 words only (from {{feature_priority}})",
  "product_lock": {{
    "name": "...",
    "exact_colors": ["..."],
    "materials": ["..."],
    "finishes": ["..."],
    "logos_and_marks": "exact wording + placement per {{product_overview}}",
    "dimensions": "exact units",
    "fidelity_rules": [
      "Do not alter features/colors/materials/finishes/dimensions",
      "Maintain exact logo placement/kerning",
      "No variants, no internals, no operation"
    ]
  }},
  "brand_lock": {{
    "typography": "{{typography}}",
    "palette_for_text": "{{palette_for_text}}",
    "logo_rules": "per {{brand_guidelines}}",
    "tone": "per {{brand_guidelines}}"
  }},
  "environment": {{
    "set": "{{set_environment}}",
    "round_table": {{
      "material": "...",
      "finish": "...",
      "color": "...",
      "diameter_mm": 0,
      "rotation": {{ "enabled": {{plinth_rotation_allowed}}, "speed": "slow" }}
    }},
    "background": "seamless/gradient/etc",
    "props": []
  }},
  "camera": {{
    "framing": "macro/mid/hero/wide",
    "movement": ["dolly-in", "orbit CW 45°", "rack focus", "whip-pan", "and so on..."],
    "speed": "slow/medium/fast",
    "easing": "linear/ease-in/ease-out/ease-in-out",
    "lens": "35mm/50mm/85mm/100mm macro, and so on...",
    "focus": {{
      "technique": "static/rack focus/focus pull",
      "from": "what starts in focus",
      "to": "what ends in focus",
      "aperture": "e.g., f/2.8",
      "depth_of_field": "shallow/medium/deep"
    }}
  }},
  "lighting": {{
    "key": {{ "direction": "frame-left/right/top", "quality": "hard/soft", "intensity": "relative", "color_temp_K": 3200–6500 }},
    "fill": {{ "ratio": "e.g., 1:4", "color_temp_K": 3200–6500 }},
    "rim": {{ "direction": "back-left/back-right", "intent": "edge separation" }},
    "accents": ["specular sweep at 05s", "logo highlight at 06s", "and so on..."],
    "color_accuracy": "no unwanted casts; preserve true product color"
  }},
  "composition": {{
    "subject_position": "center/thirds",
    "logo_visibility": "ensure legibility at specific moment",
    "negative_space": "for overlay placement",
    "horizon": "level or subtle dutch ≤ 5°"
  }},
  "overlay": {{
    "text": "2–3 words",
    "start": "MM:SS",
    "end": "MM:SS",
    "position": "top-left/top-right/bottom-left/bottom-right/center-top/center-bottom",
    "safe_margins_percent": 8,
    "style": {{
      "font": "{{typography}}",
      "size": "e.g., 48 px @ 4K",
      "weight": "Regular/SemiBold/Bold",
      "tracking": "e.g., +2%",
      "color": "{{palette_for_text}}",
      "shadow_or_stroke": "subtle for legibility"
    }},
    "animation": {{ "in": "fade 200ms", "out": "fade 200ms" }}
  }},
  "audio": {{
    "music_style": "{{music_style}}",
    "sfx": ["{{audio_sfx}}", "and so on..."]
  }},
  "transition_out": {{
    "type": "whip-pan/hard cut/match cut/parallax crossfade",
    "direction": "left/right/up/down",
    "on_beat": true
  }},
  "negatives": [
    "no humans",
    "not in operation",
    "no variant colors",
    "no internals/exploded",
    "no text beyond overlays",
    "no inaccurate refractions/reflections"
  ],
  "notes_for_veo": "One concise directive combining camera+lighting+fidelity in cinematic terms."
}}

Output constraints:
- Generate exactly {num_segments} objects.
- Each segment must reveal exactly one distinct feature from {{feature_priority}} via text overlay and visuals.
- Keep the same product instance across segments (duplicate product_lock each time).

End of instructions. Output only the JSON array.
""".strip()
# version 1 prompt version gpt 5 high LMARENA
"""
----------------------------------------
Prompt structure hierarchy: Subject → Context → Action → Style → Ambiance to reduce ambiguity and drift.
Cinematic language control: Dolly, pan, tracking, crane/aerial, POV, wide/close/low-angle, Dutch, rack focus. We adapt these to product showcases (surface reveals, brand mark reveals, feature macro shots).
Camera chaining: “Dolly-in, then rack focus” + lens/light cues: “golden-hour glow, 35 mm anamorphic.”
8-second caps: We split total duration into 8-second segments and plan one cohesive scene per segment to maintain continuity.
Text overlays: 2–3 words only, time-coded, rendered by Veo in-frame (no post).
Cinematic fragments adapted to marketing products (swap/chain/mix as needed)

Dolly-in: “…gentle dolly-in along the brushed aluminum bevel; logo emerges in crisp specular highlights…”
Pan: “…measured pan right to trace the contour seam; silhouette pops against a gradient backdrop…”
Tracking: “…dynamic tracking shot skimming the product’s surface micro-texture; reflections glide…”
Crane/Aerial: “…overhead crane drop to a centered hero on a round table; descending reveal of the brand mark…”
POV: “…macro POV as if the lens is grazing the glass edge; refractions remain accurate to material…”
Wide: “…wide hero of the product within a minimalist infinity cove; scale and symmetry established…”
Close/Extreme close: “…extreme close-up of the knurled dial; clean engraved type remains pin-sharp…”
Low-angle: “…low-angle hero framing to feel iconic and monolithic; no distortion of dimensions…”
Dutch: “…subtle dutch-angle to inject tension before a whip-pan transition to the logo reveal…”
Rack focus: “…rack focus from the brushed edge in foreground to the embossed brand crest in background…”
How to direct the model (for Gemini → Veo)

Swap nouns/adjectives to match your product scene (e.g., “artisan” → “engineer,” “tapestry” → “circuit board”).
Chain moves for richer plans: “slow dolly-in, then rack focus, then whip-pan transition.”
Mix with lighting/lens cues for specificity: “hard key with razor speculars, 100mm macro, shallow DOF.”
Absolute constraints for product commercials

Absolute Product Fidelity (primary directive): Never alter, invent, or misrepresent any feature, color, material, texture, finish, logo, or dimension. No exploded views, no internals, no variant colorways or prototypes. Preserve geometry, scale, and printed/engraved elements in every frame.
No Human Interaction: No hands, models, operators, or usage demos. The product is an autonomous, pristine artifact.
Not in Operation: Do not depict the product operating, emitting, folding, disassembling, or changing state.
Text Overlays: Must be rendered by Veo, 2–3 words max, in the brand’s style. Time-coded per segment. No post.
Continuity: The same exact product instance must persist across all segments with locked features/colors/materials.
Meta-prompting framework for Gemini 2.5 Pro
Goal: Get Gemini to output one precise Veo prompt with time-coded segments, camera/lighting/lens controls, overlay schedule, brand fidelity locks, and cinematic continuity.

Inputs Gemini should request or parse

{{product_overview}}: official name, exact color(s), materials, textures, finishes, dimensions, logos/marks, surface features, unique design elements, packaging if shown, environment constraints.
{{brand_guidelines}}: color palette, typography, logo usage, tone, motion/animation principles, do/don’ts.
{{total_duration}}: must be a multiple of 8 seconds. Segments = {total_duration}/8.
{{aspect_ratio}}: 16:9, 9:16, 1:1, etc.
{{resolution}} and {{fps}}: e.g., 4K 3840×2160, 24/30 fps.
{{music_style}}: e.g., minimalist piano, modern electronic pulses, percussive tech, ambient cinematic, and so on…
{{set_environment}}: e.g., black void, seamless white cove, sculpted light stage, reflective marble, brushed metal surface, and so on…
{{lighting_mood}}: e.g., dramatic high-contrast, rim-lit silhouette, golden-hour warmth, neon edge light, volumetric beams, and so on…
{{camera_language_preferences}}: e.g., dolly-in, macro pass, whip-pan, orbit, crane drop, rack focus, dutch angle, and so on…
{{feature_priority}}: 3–6 top benefits. Each converted to 2–3-word overlays.
{{typography}}: brand font or fallback instructions from {brand_guidelines}.
{{palette_for_text}}: brand-approved colors and contrast rules from {brand_guidelines}.
Gemini’s output schema to Veo (one single prompt)

Global header: product identity locks + brand fidelity constraints.
Global visual/audio style.
Segment plan: per 8-second segment, specify a single cohesive scene with camera/lens/lighting/motion, plus the specific overlay text and exact timecode within that segment.
Transitions between segments.
Strict negations: no humans, no operation, no altering features, no changing colors/materials.
Continuity locks: exact product maintained across all segments/angles.
Self-check Gemini must run before finalizing

Does every visual claim exist in {product_overview}? If not, remove or ask for clarification.
Are all overlays 2–3 words, brand-safe, and non-obscuring?
Is the total duration a multiple of 8, and segments equal {total_duration}/8?
Are camera/lens/light instructions unambiguous and physically plausible?
Are there any depictions of operation or interaction? Remove if yes.
Is product geometry/color/logo identical across segments?
Template A — Roundtable (Turntable-Style) Product Commercial
Use this when you want a premium 360-style hero on a round table/turntable with dynamic camera and fast transitions.

You are crafting a single Veo 3/3.1 prompt to generate a fast-paced, premium roundtable product commercial. Follow all constraints below. Output only the final Veo prompt.

Inputs:

{{product_overview}} = [Paste verbatim official product details: name, exact color(s), materials, textures/finishes, dimensions, printed/engraved marks, logos/wordmarks, unique features, packaging if shown, any environmental constraints.]
{{brand_guidelines}} = [Paste: palette, typography, logo usage, motion/animation principles, tone, forbidden treatments.]
{{total_duration}} = [e.g., 16, 24, 32 seconds; must be multiple of 8]
{{aspect_ratio}} = [16:9, 9:16, 1:1, etc.]
{{resolution}} = [e.g., 4K]
{{fps}} = [e.g., 24 or 30]
{{music_style}} = [e.g., modern electronic pulses, minimalist piano, ambient cinematic, percussive tech, and so on...]
{{set_environment}} = [e.g., matte black round table in seamless black cove; glass round plinth on white infinity cyclorama; brushed steel disc on gradient backdrop; and so on...]
{{lighting_mood}} = [e.g., high-contrast rim light with crisp speculars; golden-hour warm key with cool fill; neon edge lights; volumetric slits; and so on...]
{{camera_language_preferences}} = [Pick multiple and allow chaining: dolly-in, orbit, tracking skim, overhead crane drop, whip-pan, rack focus, macro pass, dutch angle, low-angle hero, tilt-up reveal, and so on...]
{{feature_priority}} = [3–6 short benefit labels, each 2–3 words max. Example: “Aerospace Alloy,” “True Color,” “Ultra Slim,” and so on...]
{{typography}} = [brand font specifics; fallback sans if unknown]
{{palette_for_text}} = [brand color guidance and contrast]
{{audio_sfx}} = [optional: subtle chimes, airy risers, tactile clicks, deep whoosh, and so on...]
Non-negotiable directives (apply to every frame):

ABSOLUTE PRODUCT FIDELITY: Use the exact product in {{product_overview}}. Do not alter, invent, or misrepresent any feature, color, material, texture, finish, printed/engraved detail, or dimension. No exploded views, no internals, no variant colorways. Maintain identical geometry and logo placement across all segments.
NO HUMAN INTERACTION: No hands, faces, operators, or usage demonstrations.
NOT IN OPERATION: Do not depict the product operating, emitting, changing state, or being handled.
LOGO/TYPE LOCK: Render brand marks exactly as specified (size, placement, kerning/engraving fidelity).
MATERIAL PHYSICS: Preserve physically correct reflections/refractions for glass/metal/coatings; no smearing or warping.
BACKGROUND CONSISTENCY: Keep set and props consistent across segments unless explicitly updated for a planned transition.
CLEANLINESS: No dust, fingerprints, smudges, or scratches unless explicitly stated in {brand_guidelines}.
Global style:

Aspect ratio: {{aspect_ratio}}; Resolution: {{resolution}}; Frame rate: {{fps}}; Photorealistic, premium commercial look. Shallow DOF for macro shots; crisp, controlled specular highlights; subtle bloom only if brand-appropriate.
Set: {{set_environment}}. Round table/plinth is central; product remains fixed precisely at center; if the table rotates, rotation speed is slow and constant for elegance, never implying operation.
Lighting: {{lighting_mood}}. Use controlled rim and key lights to sculpt form and showcase real materials. Avoid color casts that misrepresent true product color.
Lens/Grade: Mix of 35mm–85mm for hero shots; 90–105mm macro for texture. Anamorphic bokeh only if brand-appropriate. Color grade honors {brand_guidelines} palette and true-to-life product colors.
Music: {{music_style}}. Add tasteful SFX: {{audio_sfx}}. No voiceover.
Text overlay policy:

Veo must render text in-frame. No post-production. Use {{typography}} with {{palette_for_text}}, high legibility, positioned in safe areas that do not occlude critical product features. Each overlay must be 2–3 words max.
Cinematic language (examples to use and chain):

Orbit around the product on the round table; gentle dolly-in along surface lines; tracking skim over edges; overhead crane drop to hero; rack focus logo reveal; whip-pan between details; low-angle iconic hero; tilt-up brand crest reveal; dutch used sparingly for tension; macro pass on textures; and so on...
Plan by 8-second segments:

Total duration = {total_duration} seconds. Segments = {total_duration}/8. Each segment is one cohesive scene with dynamic camera and a single clear visual idea. Do NOT split into 2-second micro-beats. Ensure continuity of product instance.
Segment blueprint structure (repeat for each segment):

Segment {{i}}:
Scene purpose: [state the single cinematic goal for this segment]
Camera + lens: [e.g., 45° orbit clockwise, slow dolly-in, 85mm hero; or 100mm macro glide along edge; chain moves as needed]
Motion speed: [slow/medium/fast; specify acceleration if any]
Lighting: [key/fill/rim; specular behavior; any motivated light sweeps]
Background/set: [confirm same round table/plinth and set continuity]
Composition: [framing, negative space, logo positioning; avoid warping]
Transition out: [e.g., whip-pan right; match cut on logo; hard cut on beat]
Overlay text: [2–3 words from {{feature_priority}}], on-screen at [mm:ss to mm:ss within this 8s], [position], [entry/exit style: subtle fade/slide], adhere to {{typography}}/{{palette_for_text}}
Transitions between segments:

Specify exact transition type and direction (e.g., whip-pan right → left match; on-beat hard cut; parallax crossfade), synchronized to music beats to preserve energy.
Hard negatives:
NOTE: The product should not be depicted in operating state. It is stationary and only the camera moves around it in a captivating way, placed in a roundtable appropriate for the product.
No hands, no operation, no variant colors, no environment reflections with people, no inaccurate refractions, no exploding/tearing the product, no text beyond overlays defined here.
Deliver the final Veo prompt as a valid JSON array with exactly {num_segments} objects, one per 8-second segment.
Do NOT write as a single narrative prompt. Do NOT include explanatory text outside the JSON. Be precise and elaborate about every frames.
Start generating now.
"""