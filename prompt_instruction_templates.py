# prompt_templates
SOLID_BACKGROUND_INSTRUCTION = """
===== STUDIO BACKGROUND IMAGE GENERATION - STRICT PROTOCOL =====

YOU MUST FOLLOW THESE STEPS IN EXACT ORDER:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: ANALYZE INPUT IMAGE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IF INPUT IMAGE IS PROVIDED:
Examine the image carefully and extract these EXACT details:

A) PRODUCT IDENTITY:

What is the exact product shown?

Specific model characteristics, design features

B) PHYSICAL ATTRIBUTES:

Precise colors (include hex codes if discernible):

Material finishes (matte/glossy/textured/metallic, etc.,):

Shape and form factor:

Dimensions and proportions:

C) BRAND ELEMENTS (CRITICAL - PRESERVE EXACTLY):

Any visible logos (describe position, style, clarity):

Any text/labels on product (transcribe exactly as shown, even if blurry):

Any badges, stickers, brand marks:

Typography style if readable:

D) COMPONENT DETAILS:

Buttons, knobs, controls, screens:

Handles, legs, stands, attachments:

Openings, vents, ports, connectors:

Surface textures and patterns:

Stitching, seams, joints (for fabric/leather products):

E) CURRENT STATE:

Product condition in image:

Any wear, reflections, or characteristics to maintain:

WRITE THIS ANALYSIS EXPLICITLY BEFORE GENERATING THE PROMPT.

IF NO INPUT IMAGE:
Use the provided product type to describe a standard, accurate representation of that product category.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: CONSTRUCT STUDIO SCENE SPECIFICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now define the studio setup:

BACKGROUND:

Color: [Choose ONE: Pure white (#FFFFFF) / Light gray (#F5F5F5) / Soft beige (#FAF9F6) / Pale neutral tone]

Texture: Seamless, perfectly smooth, gradient-free

Type: Infinity curve backdrop OR flat surface with reflective floor

PRODUCT POSITIONING:

Placement: Centered in frame

Angle: [Select based on product type]

Small items (jewelry, accessories, phones): Slightly elevated, 30-45° angle

Appliances/Electronics: Front-facing 3/4 view showing controls and main features

Furniture: Front or angled view showing design and legs

Fashion/Apparel: Flat lay OR hanging OR on invisible mannequin

Tools/Equipment: Angled to show primary functional side

Distance: 15-20% margin from all frame edges

LIGHTING SETUP:

Primary: Three-point studio lighting (key + fill + rim)

Quality: Soft, diffused, professional

Shadows: Subtle, falling to [left/right/back] opposite key light, 30-40% opacity

Reflections: Natural floor reflection showing 40-50% opacity of product base

Highlights: Gentle specular highlights on shiny surfaces without overexposure

PRODUCT STATE:

Condition: Pristine, brand new appearance

Operational status: OFF/CLOSED/RESTING (no power, no operation)

Configuration: [Specify based on product - doors closed, screens off, blades retracted, etc.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: GENERATE FINAL PROMPT WITH STRICT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT (USE EXACTLY THIS STRUCTURE):

"Professional studio product photography.

PRODUCT: [Insert EXACT description from Step 1 - all physical details, colors, materials, dimensions]. [CRITICAL: List ALL brand text/logos exactly as they appear, with exact positioning]. [List all components, buttons, features from Step 1].

SCENE: Product isolated and centered on [background color] seamless infinity backdrop. Product positioned at [specific angle from Step 2].

LIGHTING: Professional three-point studio lighting with soft diffused key light from [direction], fill light reducing shadows, rim light creating edge definition. Soft shadow cast [direction] at 30-40% opacity. Natural reflection beneath product on glossy floor at 40-50% opacity showing product underside.

STATE: Product in pristine, non-operational condition, [specific state - powered off/closed/resting].

TECHNICAL: High-resolution commercial product photography, tack-sharp focus throughout entire product, no depth-of-field blur, neutral white balance (5500K), minimal lens distortion, e-commerce platform ready.

PRESERVE: Exact product appearance from input image including all logos, text, material finishes, and design details without any alterations."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CHECKS BEFORE SUBMITTING PROMPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Have I described the EXACT product from the input image with specific details?
□ Have I listed ALL visible brand text/logos exactly as shown?
□ Have I specified exact colors, materials, and finishes from the input?
□ Is the background a solid studio color (not lifestyle scene)?
□ Is the product state non-operational?
□ Have I included studio lighting with shadows and reflections?
□ Is the output format followed precisely?

CRITICAL REMINDER: You are NOT creating a new product. You are describing how to photograph the EXACT product shown in the input image in a professional studio setting. Every detail must match the input.

***Generate the detailed product description from Step 1 and final prompt (Step 3) for the product imgage provided.*** 
"""

LIFESTYLE_INSTRUCTION = """
===== LIFESTYLE IMAGE GENERATION - STRICT PROTOCOL =====

YOU MUST FOLLOW THESE STEPS IN EXACT ORDER:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: ANALYZE INPUT IMAGE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IF INPUT IMAGE IS PROVIDED:
Examine the image and document these EXACT details:

A) PRODUCT COMPLETE DESCRIPTION:

Exact product type and model:

Precise color palette (all colors present):

Material composition (fabric/metal/plastic/wood/glass/leather):

Texture and finish (matte/glossy/brushed/woven/smooth):

Exact dimensions and proportions:

B) BRAND PRESERVATION (MUST MAINTAIN):

All visible logos (position, size, clarity level):

All text on product (exact wording, even if partially visible or blurry):

Brand marks, symbols, badges:

Maintain the same viewing angle/ camera angle as in the input product image if possible.

Color schemes associated with branding:

C) DESIGN FEATURES:

All buttons, controls, displays, interfaces:

Structural elements (handles, wheels, stands, feet, lids):

Unique design characteristics:

Any attachments or accessories visible:

WRITE THIS ANALYSIS EXPLICITLY.

IF NO INPUT IMAGE:
Describe standard accurate features of the stated product type.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: DETERMINE SCENE TYPE FROM THEME GUIDELINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read the Theme Guidelines and decide:

OPTION A - WITH HUMAN INTERACTION:
(If guidelines mention: person, man, woman, model, someone using, human interaction, etc.)

Define human subject:

Type: [man/woman/young adult/child/professional/athlete - based on product and theme]

Approximate age: [age range appropriate to product]

Ethnicity/appearance: [diverse, natural, relatable - based on theme]

Clothing: [Specific attire matching environment and activity]

Expression: [Specific: warm smile/focused/relaxed/confident/joyful]

Pose detail: [SPECIFIC pose - e.g., "standing with left hand resting on product, right hand in pocket, left leg slightly forward, looking at camera with gentle smile"]

Eye direction: [looking at camera OR looking at product OR looking away naturally]

OPTION B - STANDALONE PRODUCT:
(If guidelines mention: product alone, no people, standalone, product focus, etc.)

Define contextual props:

Supporting items that suggest product use

Environmental elements that tell product story

Props positioned to complement, not compete, aim for real-world natural setting depiction.

STATE YOUR CHOICE: [ ] Option A - Human Interaction  [ ] Option B - Standalone

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: DEFINE LOGICAL ENVIRONMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on product type, select appropriate setting where this product ACTUALLY exists/is used:

ENVIRONMENT LOGIC TABLE:

Coffee makers/Kitchen appliances → Kitchen counter, breakfast nook, home kitchen

Outdoor power equipment → Driveway, yard, garage, appropriate outdoor terrain

Fitness equipment → Home gym, yoga studio, fitness room, outdoor exercise space

Electronics/Gaming → Living room, home office, entertainment area, desk setup

Fashion/Accessories → Urban café, home bedroom, outdoor lifestyle location

Beauty products → Bathroom vanity, spa-like setting, bedroom dresser

Tools → Workshop, garage workbench, construction site (if commercial)

Furniture → Living room, bedroom, patio, appropriately decorated space

Baby/Kids products → Nursery, playroom, family living area

Automotive accessories → Garage, driveway, car interior

SELECTED ENVIRONMENT: [Specific setting based on above logic]

ENVIRONMENTAL DETAILS:

Primary surface: [What product sits on/near]

Background elements: [3-5 specific items visible in background]

Environmental storytelling: [Evidence of product's purpose WITHOUT showing it working]
Examples:

Snow blower → Cleared path behind, deep snow in front

Coffee maker → Filled cup beside machine, coffee beans nearby

Vacuum → Clean, tidy room environment

Lawn mower → Freshly cut grass edge, outdoor setting

Depth: [Sharp throughout OR soft background blur keeping product sharp]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: DEFINE LIGHTING & ATMOSPHERE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIGHTING TYPE:
[ ] Natural window light (soft, directional)
[ ] Golden hour sunlight (warm, low-angle)
[ ] Bright daylight (even, clear)
[ ] Soft overcast (diffused, no harsh shadows)
[ ] Warm interior lighting (cozy, ambient)

SELECTED: [Choose based on theme and environment]

ATMOSPHERIC MOOD:

Color temperature: [Warm/Neutral/Cool]

Overall feeling: [Cozy/Fresh/Energetic/Serene/Professional]

Shadow quality: Soft and natural

Time of day suggestion: [Morning/Midday/Afternoon/Evening]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: GENERATE FINAL PROMPT WITH STRICT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FOR HUMAN INTERACTION (Option A):

"Lifestyle product photography with human interaction.

PRODUCT: [EXACT description from Step 1 - all colors, materials, finishes, dimensions, visible text/logos with exact wording and positioning, all design features and components]. Product in non-operational, resting state.

HUMAN SUBJECT: [Detailed description from Step 2 - specific age, gender, ethnicity, exact clothing description], [exact detailed pose with body positioning], [facial expression], [eye direction].

PRODUCT INTERACTION: [Specific description of how human is positioned relative to product - e.g., "standing beside product with right hand resting on top surface, casual lean" OR "holding product naturally in both hands at chest height"].

ENVIRONMENT: [Specific setting from Step 3], [surface product is on], [3-5 specific background elements], [environmental storytelling details showing product purpose evidence].

COMPOSITION: Product remains clearly visible occupying 30-40% of frame, human subject complementing but not overshadowing product, [rule of thirds/balanced composition].

LIGHTING: [Specific lighting type from Step 4], [color temperature], creating [atmospheric mood], soft natural shadows, realistic and inviting ambiance.

TECHNICAL: Photorealistic lifestyle photography, natural perspective, [depth of field specification], authentic moment, e-commerce ready.

PRESERVE: Exact product appearance from input image with all logos, text, and design details maintained without alteration."

FOR STANDALONE (Option B):

"Lifestyle product photography, standalone presentation.

PRODUCT: [EXACT description from Step 1 - all colors, materials, finishes, dimensions, visible text/logos with exact wording and positioning, all design features and components]. Product in non-operational, resting state.

PRODUCT POSITIONING: [Specific placement and angle in environment].

CONTEXTUAL PROPS: [Specific complementary items from Step 2 - e.g., "White ceramic mug positioned beneath espresso spout, scattered whole coffee beans on counter surface, small milk pitcher to the right"].

ENVIRONMENT: [Specific setting from Step 3], [surface details], [background elements creating context], [environmental storytelling showing product purpose without operation].

COMPOSITION: Product as hero element in foreground, [specific framing], contextual environment supporting product story.

LIGHTING: [Specific lighting type from Step 4], [color temperature], creating [atmospheric mood], soft natural shadows, authentic setting.

TECHNICAL: Photorealistic lifestyle photography, natural perspective, [depth of field specification], authentic context, e-commerce ready.

PRESERVE: Exact product appearance from input image with all logos, text, and design details maintained without alteration."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CHECKS BEFORE SUBMITTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Have I described the EXACT product from input with all specific details?
□ Have I preserved ALL brand text/logos exactly as shown?
□ Is the environment logical for where this product is actually used?
□ Is the product in NON-OPERATIONAL state?
□ If human included, is the pose specifically detailed?
□ Are contextual props appropriate and specific?
□ Does environmental storytelling show product purpose without showing it working?

CRITICAL: You are describing how to photograph the EXACT input product in a realistic lifestyle context, not inventing a new product.

NOTE:
***Generate the detailed product description from Step 1 and final prompt (Step 3) for the product imgage provided.*** 
"""

MARKETING_CREATIVE_INSTRUCTION = """
===== MARKETING CREATIVE IMAGE GENERATION - STRICT PROTOCOL =====

YOU MUST FOLLOW THESE STEPS IN EXACT ORDER:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: ANALYZE INPUT IMAGE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IF INPUT IMAGE IS PROVIDED:
Document EXACT product specifications:

COMPLETE PRODUCT DESCRIPTION:

Product type and specific model:

All colors (precise shades):

All materials and finishes:

Exact proportions and size:

ALL visible brand text/logos (exact wording, position, clarity):

All design features (buttons, screens, handles, components):

Unique identifying characteristics:

WRITE EXPLICIT ANALYSIS.

IF NO INPUT IMAGE: Use accurate standard features of stated product type.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: EXTRACT MARKETING SPECIFICATIONS FROM USER INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From "Marketing Image Details" provided by user, extract:

TEXT ELEMENTS:

Brand Name: "[exact text]" OR [none provided]

Headline Text: "[exact text, max 3-4 words]" OR [none provided]

Call-to-Action: "[exact text]" OR default to "SHOP NOW"

Footer Text: "[exact text]" OR [none]

PROMOTIONAL ELEMENTS:

Discount/Sale callout: "[e.g., 50% OFF, LIMITED TIME, NEW]" OR [none]

Badge/Banner needed: [YES/NO] - "[text if yes]"

SEASONAL/FESTIVE THEME:

Theme: [Christmas/New Year/Black Friday/Summer/Spring/Halloween/Valentine's/None]

Specific elements required: [e.g., "string lights, snowflakes, ornaments"]

COMPOSITION STYLE (select based on theme guidelines):
[ ] A - Hero Product (single large product, 60-70% of frame)
[ ] B - Multi-Instance (2-5 products at varying sizes/angles)
[ ] C - Feature Showcase (main product + detail callouts)
[ ] D - Lifestyle + Overlay (lifestyle scene with promotional graphics)

SELECTED STYLE: [Choose one based on user request]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: DEFINE VISUAL DESIGN ELEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maintain the same viewing angle/ camera angle as in the input product image if possible.

BACKGROUND DESIGN:
Select appropriate background:

Premium products → Deep navy/black/charcoal with subtle gradient OR elegant solid color

Tech products → Clean white/light gray with geometric elements OR gradient blue

Lifestyle products → Soft blurred environment OR warm gradient

Vibrant/Youth products → Bold solid colors OR energetic gradients

Eco products → Natural greens/earth tones OR organic textures

SELECTED BACKGROUND: [Specific color/style with hex code if applicable]

COLOR PALETTE:

Primary color: [specific color for background/dominant area]

Accent color: [for text/CTA elements - must contrast with background]

Supporting colors: [2-3 colors for additional elements]

DESIGN ELEMENTS TO INCLUDE:
[ ] Geometric shapes (circles/lines/triangles) - specify placement
[ ] Gradient overlay - specify direction and colors
[ ] Subtle texture - specify type (grain/fabric/concrete)
[ ] Light effects - specify type (glow/rays/spotlight)
[ ] Shadow drama - specify style

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: DEFINE TEXT PLACEMENT & TYPOGRAPHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRAND NAME (if provided):

Text: "[exact text from Step 2]"

Position: [Top left/Top center/Top right/Bottom center/Footer]

Typography: [Bold sans-serif/Modern bold/Elegant serif/Sleek uppercase]

Size: [Large/Medium - relative to composition]

Color: [Specific color ensuring contrast]

Effect: [None/Subtle shadow/Soft glow]

HEADLINE (if provided):

Text: "[exact text from Step 2]"

Position: [Upper third/Center left/Center right/Lower third]

Typography: [Bold impact font/Modern bold sans-serif/Clean strong font]

Size: Large, prominent

Color: [High contrast color]

Effect: [None/Shadow for depth]

CALL-TO-ACTION:

Text: "[exact text from Step 2]"

Style: [Rounded rectangle button/Pill-shaped badge/Minimal underlined text/Banner ribbon]

Position: [Bottom right/Bottom center/Lower third centered]

Button color: [Accent color from Step 3]

Text color: [Contrasting color for readability]

Size: [Moderate, clearly clickable appearance]

PROMOTIONAL BADGE/BANNER (if applicable):

Text: "[exact text from Step 2]"

Style: [Corner ribbon/Circular badge/Star burst/Rectangular banner]

Position: [Top right corner/Top left corner/Center burst]

Colors: [Urgent reds/yellows OR festive colors]

FOOTER (if provided):

Text: "[exact text from Step 2]"

Position: Bottom edge, centered or left-aligned

Size: Small, subtle

Color: Muted, non-intrusive

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5: DEFINE FESTIVE/SEASONAL OVERLAYS (if applicable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IF SEASONAL THEME SELECTED IN STEP 2:

CHRISTMAS:

Elements: Warm white string lights draped across top third, red and gold ornament accents in corners, subtle snowflakes overlay, pine branch elements framing edges

Colors: Traditional red, green, gold, white

Placement: Overlaid ON the composition, not obscuring product

NEW YEAR:

Elements: Gold and silver confetti burst, champagne gold accents, celebratory firework graphics, "2024/2025" year elements if relevant

Colors: Midnight blue, champagne gold, silver, black

Placement: Celebratory elements around product, not covering

BLACK FRIDAY/SALES:

Elements: Bold geometric sale badges, lightning bolt graphics, urgent color blocks

Colors: Black, red, yellow, white for high contrast

Placement: Corner badges, side banners

SUMMER:

Elements: Sun ray graphics, tropical leaf accents, bright color pops, beach texture hints

Colors: Bright yellows, oranges, turquoise, coral

Placement: Background elements, corner accents

SPRING:

Elements: Delicate floral corner pieces, soft botanical elements, pastel color accents

Colors: Soft pink, mint green, lavender, cream

Placement: Edge decorative elements

HALLOWEEN:

Elements: Autumn leaves, orange and purple color accents, subtle spooky-fun elements

Colors: Orange, purple, black, deep autumn tones

Placement: Scattered elements, color grade overlay

VALENTINE'S:

Elements: Heart shapes, rose petal accents, romantic color washes

Colors: Deep red, pink, rose gold, white

Placement: Corner accents, subtle background elements

DESCRIBE EXACT FESTIVE ELEMENTS: [Based on theme from Step 2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6: GENERATE FINAL PROMPT WITH STRICT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Marketing creative product advertisement image.

PRODUCT: [EXACT complete description from Step 1 - all colors, materials, finishes, dimensions, all visible brand text/logos with exact wording and positioning, all design features]. Product shown in [non-operational state/appropriate display state].

COMPOSITION STYLE: [Selected style from Step 2 - describe specific layout]
[IF Hero: Single large product positioned [location] occupying 60-70% of frame]
[IF Multi-Instance: [Number] instances of same product at varying scales - [describe specific arrangement]]
[IF Feature Showcase: Main product [position] with [number] detail callout elements showing [specific features]]
[IF Lifestyle + Overlay: Product in [specific environment] with marketing graphics overlaid]

BACKGROUND: [Specific background description from Step 3 with exact colors/hex codes], [any gradients with direction], [texture if applicable].

DESIGN ELEMENTS: [List specific geometric shapes, overlays, light effects from Step 3 with exact placement - e.g., "Three thin golden circles in bottom left, diagonal light ray from top right, subtle 15% concrete texture overlay"].

COLOR PALETTE: Primary [color], Accent [color], Supporting [colors].

TEXT ELEMENTS - EXACT PLACEMENT:

[IF BRAND NAME PROVIDED:]
Brand name text reading "[EXACT TEXT]" positioned at [exact position from Step 4], [typography style], [size], [color], [effects if any].

[IF HEADLINE PROVIDED:]
Headline text reading "[EXACT TEXT]" positioned at [exact position from Step 4], [typography style], large prominent size, [color], [effects if any].

Call-to-action element reading "[EXACT TEXT]" as [button/badge style from Step 4] positioned at [exact position], [button color] background with [text color] text, [size and shape details].

[IF PROMOTIONAL BADGE PROVIDED:]
[Badge style] displaying "[EXACT TEXT]" positioned at [exact position], [colors].

[IF FOOTER PROVIDED:]
Footer text "[EXACT TEXT]" at bottom edge, [alignment], small subtle size, [color].

[IF SEASONAL THEME SELECTED:]
FESTIVE OVERLAY: [Exact festive elements from Step 5 with specific placement - e.g., "Warm white string lights draped across top edge, small red and gold ornaments in top right and bottom left corners, subtle snowflake graphics scattered at 20% opacity, pine branch accent framing left edge"].

LIGHTING & MOOD: [Dramatic/Soft/Vibrant] lighting creating [specific mood - luxurious/energetic/fresh/premium], [lighting direction and quality].

TECHNICAL: High-resolution commercial advertising quality, photorealistic product rendering, professional graphic design composition, balanced visual hierarchy (Product → Brand → Headline → CTA), e-commerce marketing ready.

PRESERVE: Exact product appearance from input image with all logos, text, and design details maintained without alteration. Marketing elements enhance but never alter the product itself."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CHECKS BEFORE SUBMITTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Have I described EXACT product from input with all specific details?
□ Have I preserved ALL brand text/logos from the product exactly?
□ Have I included ALL text elements with EXACT wording provided by user?
□ Are text positions specifically defined (not vague)?
□ Are all colors specified (background, text, buttons, accents)?
□ If seasonal theme requested, are specific festive elements described with placement?
□ Is composition style clearly defined?
□ Is the prompt structured in the required format?

CRITICAL: Marketing graphics overlay the scene, but the product itself must remain exactly as shown in input image.

***NOTE: Generate the detailed product description from Step 1 and final prompt (Step 3) for the product imgage provided.***

"""