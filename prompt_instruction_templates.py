# prompt_templates

"""
This file stores the master instruction templates for the Gemini 2.5 Pro model (The Planner).
Each template is designed to guide the LLM in creating a detailed, structured prompt
for the Nano Banana model (The Artist).
"""

SOLID_BACKGROUND_INSTRUCTION = """
Instructions:
**LLM instruction (what to output):**

Output one Nano Banana prompt for a studio packshot with a seamless background and physically correct shadows. Do not include any text/CTA/price overlays.
Provide the prompt with these sections and rules:

Portrayal (precise)
Show the referenced product as a standalone, centered hero.
Choose angle that best reveals form:
Front if symmetrical/flat face is key.
3/4 if depth, handles, or side details matter (default).
Top‑down for broad, planar items (e.g., pans, rugs).
Scale: product occupies ~55–70% of frame height; keep entire product in frame.

Fidelity: preserve exact proportions, materials, and colors from the image (brushed steel, powder‑coat, oak grain, glass). Keep any existing brand mark as is; do not invent logos/features.

Layout of the image:
Background: seamless studio sweep in one of:
Pure white #FFFFFF, or
Light gray #F4F5F7, or
Charcoal #121212 (use only if product is light‑colored).
Subtle studio gradient allowed. Ground the product with:
Soft contact shadow beneath (15–25% opacity).
Optional faint reflection (10–12%) only if surface would realistically reflect.
Safe margins: 48–64 px on all sides. No props, borders, or frames.

Text position:
None. Explicitly instruct the model: no text, no CTA, no price, no badges.

Lighting & shadows:
Two‑softbox studio setup: key light upper‑left; fill front‑right; gentle rim highlight to define edges.
Speculars controlled on metal/ceramic; avoid blown highlights; deep focus so the entire product is sharp.

Composition rules:
Product centered; no cropping of important parts; one hero item only (no duplicates).

Negative prompt:
text, numbers, watermark, invented logos, extra props, duplicate products, patterned/busy backgrounds, warped geometry, unrealistic shadows, strong color casts.

Aspect: [1:1 1080×1080 | 4:5 1080×1350 | 9:16 1080×1920]

"""

LIFESTYLE_INSTRUCTION = """
LLM Instructions: Follow this template precisely.
Pay close attention to the User Guidelines to determine if a human subject is required.
Generate a prompt that tells a complete story within a single frame.

Prompt Structure:

// [1] CORE SCENE: A high-level summary of the photograph, showcasing the product's function, design, or the lifestyle it enables.
// - Snow Blower Example: "A cinematic photo showing the power and efficiency of a snow blower clearing deep snow."
// - Faucet Example: "An architectural photograph of a minimalist bathroom, highlighting a modern matte black faucet as the centerpiece."
// - Patio Furniture Example: "A warm, inviting lifestyle shot of a perfectly arranged patio set at dusk, ready for relaxation."
     and so on... [Adapt to the product usecase]

// [2] PRIMARY SUBJECT & PRODUCT FIDELITY: Defines the main subject (human or product) and ensures product accuracy. [Adapt to the product usecase]
// **IMPORTANT: Only include a human subject if explicitly requested in the User Guidelines.** If no human is requested, this section focuses solely on the product's placement and state.

//  --- IF A HUMAN SUBJECT IS REQUESTED ---
// - Persona & Attire: [e.g., "A man in his 40s wearing a heavy-duty work jacket for winter."]
// - Stance & Gaze: [e.g., "He stands firmly, looking with focus at the path he is clearing."]
// - Product Handling: [e.g., "His gloved hands are firmly on the handlebars, guiding the machine with confident control."]

//  --- IF PRODUCT-ONLY (NO HUMAN) ---
// - Product Placement: [e.g., "The faucet is perfectly centered on a white marble vanity," or "The espresso machine sits on a clean, dark quartz countertop."]
// - Product State: [e.g., "The faucet is off, with a single, perfect water droplet on its spout," or "The oven's interior light is on, showcasing the racks inside."]

// --- ALWAYS INCLUDE ---
// - High Fidelity: "Preserve the exact design, proportions, materials (e.g., brushed steel, powder-coated paint, oak grain, glass), and branding from the provided product image. Do not invent features or logos."
    
// [3] THREE-PART ENVIRONMENT (Before, During, After): **(CRITICAL SECTION)** Defines the logical states of the scene to show the product's full impact in one frame. This tells the story.
// - A. The 'Contextual / Untransformed' Zone: The state of the environment BEFORE or AROUND the product's core function.
//    - Snow Blower Example: "IN FRONT of the machine, a path is covered in a thick, undisturbed blanket of powdery snow."
//    - Faucet Example: "The pristine, dry, white porcelain basin SURROUNDS the base of the faucet."
//    - Patio Furniture Example: "BEYOND the furniture set, an empty section of the wooden deck is visible, waiting to be used."
        and so on... [Adapt to the product usecase]

// - B. The 'Focal / Interaction' Zone: The product itself, as the hero of the scene.
//    - Snow Blower Example: "AT THE MOUTH of the snow blower, the auger is actively churning the snow."
//    - Faucet Example: "The matte black FAUCET itself stands as a sculptural element."
//    - Patio Furniture Example: "The plush, modern patio SOFA and chairs, arranged in a cozy, conversational grouping."
        and so on... [Adapt to the product usecase]

// - C. The 'Resulting / Transformed' Zone: The state of the environment AFTER or as a direct RESULT of the product's presence or action.
//    - Snow Blower Example: "BEHIND the machine, a perfectly clean, wet, black asphalt path is now visible."
//    - Faucet Example: "BENEATH the spout, a small, elegant pool of clear water has formed near the drain."
//    - Patio Furniture Example: "ON the sofa, a cozy throw blanket is artfully draped and a book rests on a cushion, implying comfort and relaxation."
        and so on... [Adapt to the product usecase]

// [4] DYNAMIC INTERACTION & EFFECT: Describes the product's action or its passive interaction with the environment.
// - A. Product Action (The Cause):
//    - Espresso Machine Example: "The machine is forcing hot water through a portafilter packed with fine coffee grounds."
//    - Faucet Example (if on): "The handle is turned, causing a valve to release a controlled flow of water."
//    - Patio Furniture Example (passive): "The setting sun casts long, dramatic shadows from the furniture's legs across the deck."
        and so on... [Adapt to the product usecase]

// - B. Material Reaction (The Effect):
//    - Espresso Machine Example: "Two streams of rich, dark espresso with a thick golden crema are flowing into a small glass cup."
//    - Faucet Example (if on): "A perfectly clear, non-splashing, aerated stream of water falls from the spout."
//    - Patio Furniture Example (passive): "The warm light of dusk highlights the texture of the cushion fabric and the smooth finish of the frame."
        and so on... [Adapt to the product usecase]

// [5] COMPOSITION & PHOTOGRAPHY: The technical details of the shot.
// - Shot & Angle: [e.g., "Dynamic low-angle shot," "Architectural-style straight-on shot," "Intimate eye-level medium shot," "Top-down flat lay."]
// - Background & Lighting: [e.g., "Bright, even light from a large window," "Warm, ambient string lights at twilight," "Crisp, direct winter sunlight."]
// - Focus & Depth: [e.g., "Razor-sharp focus on the product, with a soft-focus background (shallow depth of field)."]
     and so on... [Adapt to the product usecase]

// [6] STYLE & QUALITY: The overall aesthetic.
// - Genre & Mood: [e.g., "Professional commercial photography," "Spa-like tranquility," "Cozy and inviting lifestyle," "Minimalist and modern."]
// - Color Palette: [e.g., "High contrast (red, white, black)," "Monochromatic with metallic accents," "Warm, earthy tones."]
// - Technical Specs: [e.g., "Photorealistic, 8K, highly detailed, sharp focus."]
     and so on... [Adapt to the product usecase]

// [7] NEGATIVE PROMPT: Explicitly forbid logical fallacies and common errors.
// - e.g., "illogical scene, unreal physics, text, logos (other than the product's), watermarks, cartoon, illustration, deformed, blurry, discolored grout, water spots, smudges, dirty cushions, rust."
"""
"""**Example prompt that achieved great results:**(Do not copy the brand name and setting from this exactly- This is provided for structural and creative reference only.)

You could follow similar structure as above to create the prompt for the given input image with appropraiate context related to the product.
"""

MARKETING_CREATIVE_INSTRUCTION = """
**Instructions for LLM prompt generation:**

The generated image should be ready to be put as commercials in Instagram reels, facebook posts.
One image input of the product(the same image will be provided to Nano Banana), second a constructive prompt. The prompt can be constructed based on this:
Precisely mention how to potray the given product.(standalone or with human using it or so on..)
Layout of the image. Here the the product is centred with a backdrop template, simple but well adapted to the product. (human language may not know the correct words to guide the model to generate an image like this)
Text position. If the image is for an instagram marketing campaign then, the suitable texts, brand name and widgets can be added just like in the image.(Should have some lines describing the product for marketing)
so a prompt structure is crucial.
Add festival themed elements if mentioned in User Guidelines. (e.g., Diwali lights, Christmas decorations, thanksgiving, etc.)

**Example prompt that had achieved greater response from the same model:**(Do not copy the brand name and setting from this exactly- This is provided for structural and creative reference only.)
Lifestyle with woman, natural setup (Instagram/Facebook)
Input image: Use the provided product photo of the earrings exactly as-is; clean cutout; preserve metal finish, pearl details, aqua beads, and square mirror studs; keep true color and proportions; no redesign.
Goal: A natural, editorial-style photo of a woman wearing these earrings; warm, romantic vibe; ready for Instagram feed (4:5) and Reels/Stories (9:16 crop-safe).
Portrayal:
Focus on the woman from shoulders to head; hair softly tied back or tucked behind ears to fully reveal both earrings.
Slight three-quarter head turn toward camera-left; soft smile; minimal, dewy makeup.
Wardrobe: pastel blouse or chiffon kurta in ivory/sage; no other statement jewelry.
Ensure earrings hang naturally, symmetrical pair, accurate scale and clasp orientation.
Environment and lighting:
Outdoor terrace or garden at golden hour; soft bokeh greenery with faint blush-pink roses to echo the product palette.
Warm directional key light from camera-left; subtle rim light to define contours; no blown highlights on metal or beads.
Composition and layout:
Aspect ratio: 4:5 vertical (1080×1350) with a 9:16 safe crop overlay for Reels.
Place the model slightly off-center (rule of thirds); leave clean negative space top-right for text.
Depth of field: portrait lens look (85mm equivalent, f/2.8) for creamy background.
Color direction:
Palette: sage green, blush rose, ivory, and soft gold to harmonize with aqua beads and pearls.
On-image text (marketing copy and widgets):
Top-right: {BrandName} logo (If user provides brand name in guidelines, else ignore).
Headline (2 lines max): “Bloom in Every Moment”
Subhead: “Handcrafted aqua & pearl chandeliers in luxe gold tone.”
Micro-features row with small icons: Lightweight | Nickel‑free | Secure clasp
CTA pill button bottom-right: “Shop Now ▸”
Footer micro text bottom-left: @{BrandHandle} • brandname.com (Only If user provides brand name in guidelines, else ignore)
Add a subtle vertical gradient behind text (0–30% black) for legibility.
Technical/finishing:
sRGB, gentle contrast, natural skin texture, realistic shadows beneath earrings.
Remove stray hair overlapping earrings; no dust or scratches; no color cast on pearls.
Negative prompts (avoid):
No extra earrings, no duplication or distortion of beads, no altered colors, no hard flash, no busy props or branded clutter, no face of a recognizable public figure.

You could follow similar structure as above to create the prompt for the given input image with appropraiate context related to the product.
"""