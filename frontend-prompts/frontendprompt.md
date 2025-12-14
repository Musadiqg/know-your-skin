### System / High-level instructions for the frontend AI

You are an expert React/Next.js frontend engineer. Your task is to create a production‑ready, modern Next.js web app (from scratch) that is a client for an existing skin‑analysis backend API running on a GCP VM.

The backend is already implemented and deployed; **you must not touch the backend**. Your job is to:

1. Scaffold a new Next.js project (with TypeScript) suitable for deployment on Vercel (free tier).
2. Build a polished UI that lets a user upload 1–3 skin photos, call the backend endpoints, and render the results in a clear, reassuring, and visually pleasing way.
3. Make it easy for the developer (the user) to deploy this frontend to Vercel and configure the API base URL via environment variables.

Follow all instructions in this document carefully. You should output concrete project code (files), not just pseudo‑code.

---

### Backend overview (what already exists)

The backend is a FastAPI app running on a GCE VM. It exposes three HTTP endpoints:

1. `GET /health`
2. `POST /analyze`
3. `POST /analyze_session`
4. `POST /deep_analysis`

For all examples below, assume the **API base URL** is:

- `http://34.9.129.107:8000`

In the final frontend code, you must **not hard‑code this IP**; instead, read it from an environment variable (see the “Frontend config & env vars” section).

#### 1. `GET /health`

- Simple health check.
- Response:

```json
{ "status": "ok" }
```

Use this only for a lightweight “Backend online” indicator in the UI (optional).

#### 2. `POST /analyze` – single image

- URL: `/analyze`
- Method: `POST`
- Content type: `multipart/form-data`
- Body:
  - `image`: file (JPG/PNG) – the user’s skin photo.
- Response: JSON with **two top‑level sections**: `cosmetic` and `concerns`.

Example response shape (fields you must handle):

```json
{
  "cosmetic": {
    "summary": "We see features that align with Fitzpatrick Type II (fair, usually burns, may tan lightly)...",
    "tone_section": {
      "fitzpatrick": {
        "label": "FST2",
        "label_mode": "single",
        "labels": ["FST2"],
        "title": "Fitzpatrick Type II (fair, usually burns, may tan lightly)",
        "overview": "This type of skin is fair and can burn with sun exposure...",
        "care_focus": "Daily SPF and gentle hydrators are key...",
        "probs": {
          "FST1": 0.02,
          "FST2": 0.94,
          "FST3": 0.02,
          "FST4": 0.01,
          "FST5": 0.0,
          "FST6": 0.0
        }
      },
      "monk_tone": {
        "label": 3,
        "group_name": "lighter tones",
        "education": "On lighter skin tones, redness and sunburn often show up quickly...",
        "probs": {
          "1": 0.00,
          "2": 0.01,
          "3": 0.67,
          "4": 0.31,
          "...": 0.0
        }
      }
    },
    "texture_section": {
      "items": [
        {
          "tag": "Texture_Bumpy",
          "title": "Uneven or bumpy texture",
          "body": "We see some raised or bumpy areas...",
          "prob": 0.72
        }
      ]
    },
    "disclaimer": "The information above describes cosmetic characteristics..."
  },
  "concerns": {
    "summary": "We used an AI-based cosmetic model to review the image you shared. In this photo we see strong patterns associated with breakouts and bumps...",
    "concern_sections": [
      {
        "tag": "Breakouts_Bumps",
        "title": "Breakouts and Bumps",
        "body": "We see strong patterns that can be seen with this type of skin pattern...",
        "prob": 0.99,
        "scin_labels": ["Acne", "Folliculitis", "Molluscum Contagiosum", "Prurigo nodularis", "Keratosis pilaris"]
      }
      // ...possibly more concerns
    ],
    "routine": {
      "concerns": [
        ["Breakouts_Bumps", 0.99]
      ],
      "steps": {
        "cleanser": [
          {
            "id": "salicylic_acid_cleanser",
            "name": "Salicylic Acid Cleanser",
            "step": "cleanser",
            "image_name": "salicylic_acid_cleanser.png",
            "why": "Salicylic Acid Cleanser combines salicylic acid with a hypochlorous base..."
          }
        ],
        "treatment": [
          {
            "id": "silymarin_c15_serum",
            "name": "Silymarin C15 Serum",
            "step": "treatment",
            "image_name": "silymarin_c15_serum.png",
            "why": "Silymarin C15 Serum pairs vitamin C with targeted actives..."
          }
        ],
        "moisturizer": [
          {
            "id": "daily_moisturizer",
            "name": "Daily Moisturizer",
            "step": "moisturizer",
            "image_name": "daily_moisturizer.png",
            "why": "...reason based on concerns..."
          }
        ],
        "sunscreen": [
          {
            "id": "facial_sunscreen_gel",
            "name": "Facial Sunscreen Gel",
            "step": "sunscreen",
            "image_name": null,
            "why": "Because consistent sun protection helps with nearly all skin goals..."
          }
        ]
      }
    },
    "disclaimer": "This experience is powered by an AI-based cosmetic skin analysis and is not a medical diagnosis..."
  }
}
```

#### 3. `POST /analyze_session` – multiple images

- URL: `/analyze_session`
- Method: `POST`
- Content type: `multipart/form-data`
- Body:
  - `images`: one or more image files (same field name repeated), JPG/PNG.
- Response: **same overall structure as `/analyze`** (`cosmetic` + `concerns` + routine), but aggregated across the provided images.

Your frontend logic:

- If the user has uploaded:
  - 1 image → call `/analyze`.
  - 2 or 3 images → call `/analyze_session`.
- The UI should treat the returned JSON the same way: decorative copy, tone breakdown, concern sections, routine steps.

#### 4. `POST /deep_analysis` – detailed conditions

- URL: `/deep_analysis`
- Method: `POST`
- Content type: `multipart/form-data`
- Body:
  - `image`: file (JPG/PNG) – usually one of the images already used above.
  - optional query parameter: `threshold` (float), e.g. `?threshold=0.5`.
- Response: condition‑level probabilities. Approximate structure:

```json
{
  "conditions": {
    "Eczema": {
      "prob": 0.72,
      "active": true,
      "metrics": {
        "precision": 0.59,
        "recall": 0.55,
        "f1": 0.57,
        "support": 473
      },
      "reliability": {
        "level": "high",
        "text": "On a dermatology validation set, this label showed relatively strong performance..."
      }
    },
    "Acne": {
      "prob": 0.65,
      "active": true,
      "metrics": { "...": "..." },
      "reliability": { "...": "..." }
    }
    // ...many other condition keys
  }
}
```

The exact condition list comes from SCIN condition labels (e.g., “Psoriasis”, “Tinea Versicolor”, etc.). You don’t need to know all names in advance; your UI should iterate over keys.

---

### Concern tags & product recommendations (how to handle all cases)

The backend uses **six high‑level concern tags** for cosmetic concerns. You do NOT need to hard‑code logic per tag, but you should know what they represent so the UI labels and grouping feel natural.

The six tags (from `CONCERN_TAGS`) are:

- `Dry_Sensitive` → “Dry or Sensitive Skin Tendencies”
- `Breakouts_Bumps` → “Breakouts and Bumps”
- `Itchy_Hives` → “Itch, Hives, or Bite-like Areas”
- `Red_Scaly_Patches` → “Red or Scaly Patches”
- `Pigment_Tone_Issues` → “Pigment and Tone Irregularities”
- `Possible_Infection` → “Patterns Sometimes Seen in Infections”

In the `/analyze` and `/analyze_session` responses:

- `concerns.concern_sections` contains user‑facing titles and body text for each active concern tag, so you should rely on those fields and NOT try to infer titles from the raw tag names.
- `concerns.routine.steps` is already the result of a rules‑based recommendation system that maps concern tags to products. Each product includes:
  - `id`, `name`, `step` (cleanser / treatment / moisturizer / sunscreen),
  - optional `image_name`,
  - and a human‑friendly `why` explaining why it was chosen.

Your UI should therefore:

- Treat `concern_sections` as a **dynamic list**:
  - Render cards for however many items are present (0, 1, 2, or more) without breaking.
  - Use the provided `title` and `body` directly, and show `prob` as a qualitative confidence (e.g. “moderate”, “clear”, “strong”).
- Treat `routine.steps` as **fully data‑driven**:
  - Iterate over the keys of `steps` (e.g. `cleanser`, `treatment`, `moisturizer`, `sunscreen`).
  - For each step, iterate over the array of products for that step.
  - Do NOT assume there is exactly one product per step; the layout must handle 0, 1, or multiple products gracefully (e.g., stacked cards or a horizontal list).
- Never assume a fixed set of concern tags in the frontend. Instead:
  - Use whatever comes back in `concern_sections` and `routine.steps`.
  - If a future backend version adds a new tag, your UI should still work by rendering the provided `title` and `body` for that concern.

If you want to show a small “tag” or chip for each concern near products, you may:

- Use `routine.concerns` (list of `[tag, probability]`) to know which high‑level tags are most active.
- Map raw tags to display labels via a simple mapping like:

```ts
const CONCERN_DISPLAY_LABELS: Record<string, string> = {
  Dry_Sensitive: "Dry or Sensitive",
  Breakouts_Bumps: "Breakouts / Bumps",
  Itchy_Hives: "Itch / Hives",
  Red_Scaly_Patches: "Red or Scaly",
  Pigment_Tone_Issues: "Pigment / Tone",
  Possible_Infection: "Possible Infection",
};
```

…but always fall back to `tag` itself if a key is missing to avoid crashes.

In summary:

- **Do not hard‑code specific concern tags into layout logic.**
- **Drive all concern and product UI from the JSON you receive** (`concern_sections`, `routine.concerns`, `routine.steps`), so the UI remains stable even if the underlying model or concern mappings evolve.

---

### Frontend requirements and UX flow

You are building a **single‑page experience** (using Next.js) that lets a non‑technical user:

1. Upload up to **3 images** of their skin.
2. Click a main button “Analyse my Skin” that:
   - Calls `/analyze` if 1 image is provided.
   - Calls `/analyze_session` if 2–3 images are provided.
3. See a **well‑structured results page** with sections in this order:
   1. Cosmetic overview (summary, tone explanation).
   2. Fitzpatrick type details.
   3. Monk skin tone details.
   4. Texture section (if any).
   5. Concern overview and sections.
   6. Recommended routine (steps and products).
   7. Disclaimers (cosmetic + concern).
4. Optionally click a secondary “Deep Analysis” button that:
   - Sends the **first uploaded image** (or a selected one) to `/deep_analysis`.
   - Displays a separate panel with condition‑level probabilities and reliability text.

Additional UX expectations:

- Show **loading spinners / skeletons** while calling the backend.
- Show **friendly error messages** on network/API errors.
- Make it visually clear when analysis is running vs. finished.
- Make it easy to **reset** and upload new photos.

---

### Visual design and components

You have freedom in look & feel, but follow these guidelines:

- **Overall style**:
  - Soft, calming color palette (e.g., light creams, soft blues/greens, subtle lavender).
  - Rounded corners, subtle shadows, plenty of whitespace.
  - Typography that feels approachable and clean (e.g., Inter, system sans‑serif).

- **Layout**:
  - A centered layout with a max‑width container (e.g., 960–1200px).
  - Responsive design: works well on mobile and desktop.
  - Sticky or visible header with app name (e.g., “Know Your Skin”).

- **Key components** (you should create reusable React components for these):

  1. **ImageUploader**:
     - Allows drag‑and‑drop or “Choose files” click.
     - Accepts up to 3 images.
     - Shows small thumbnails for each selected image and ability to remove one.
     - Shows count like “2 of 3 images selected”.

  2. **PrimaryActionBar**:
     - Contains:
       - Primary button: **“Analyse my Skin”** (disabled if no images).
       - Secondary button: **“Deep analysis”** (disabled until **at least one** image has been analyzed or at least one uploaded).
     - Shows a small note about privacy / no diagnosis.

  3. **ResultsLayout**:
     - Appears after a successful `/analyze` or `/analyze_session`.
     - Contains sub‑sections in this order:

       - **Cosmetic overview card**:
         - Uses `cosmetic.summary` text as a paragraph or short hero blurb.

       - **Tone section**:
         - Use `cosmetic.tone_section.fitzpatrick`:
           - Display the title, e.g., “Fitzpatrick Type II (fair, usually burns, may tan lightly)”.
           - Show overview and care focus as paragraphs.
         - Use `cosmetic.tone_section.monk_tone`:
           - Show something like “Your overall tone group: lighter tones”.
           - Render `education` as a friendly paragraph.
         - Optional: show a simple bar chart or list of probability values from `probs` (you can use plain divs, no need for chart libraries).

       - **Texture section**:
         - Use `cosmetic.texture_section.items` (if present).
         - For each item, render:
           - Title.
           - Body text.
           - A subtle “confidence” indicator (e.g., 0–1 mapped to low/medium/high, or a simple percentage).

       - **Concern sections**:
         - Use `concerns.summary` as an intro paragraph.
         - For each `concern_sections` item:
           - Card with:
             - Title (e.g., “Breakouts and Bumps”).
             - Body text (the explanation and care advice).
             - Probability (e.g., as a pill: “High confidence”).
             - List of `scin_labels` mapped to chips like “Underlying labels: Acne, Folliculitis, ...” (optional, can be shown in a tooltip or collapsible).

       - **Routine section**:
         - Use `concerns.routine.steps`.
         - Group by step: “Cleanser”, “Treatment”, “Moisturizer”, “Sunscreen”.
         - For each step:
           - Show product name.
           - Show `why` text as explanation.
           - If `image_name` exists, show a placeholder card where an image could go (do not assume images are actually hosted).
         - Keep the routine visually distinct (e.g., separate card with step headings).

       - **Disclaimers**:
         - Show `cosmetic.disclaimer` and `concerns.disclaimer` in a well‑styled alert / info box at the bottom.

  4. **DeepAnalysisPanel**:
     - When the user clicks “Deep analysis”:
       - Call `/deep_analysis` with the first uploaded image (or the currently selected one).
       - Show a loading indicator.
       - On success:
         - Display a list of conditions from `conditions` in the response.
         - For each condition:
           - Name (e.g., “Eczema”).
           - Probability (e.g., percentage or 0–1 with text like “low”, “medium”, “high”).
           - `reliability.level` (badge: high / medium / low / unknown).
           - `reliability.text` as small explanatory copy.
         - Consider sorting conditions by probability descending and showing only the top N (e.g., 5–10) by default, with a “Show more” toggle.

  5. **State & Feedback**:
     - Loading indicators for:
       - Main analysis (`/analyze` or `/analyze_session`).
       - Deep analysis (`/deep_analysis`).
     - Error handling:
       - Show a friendly error card if fetch fails (network error, 500, etc.).
       - Include a “Try again” button.

---

### Frontend technology choices & project setup

You should:

1. Use **Next.js 14+** (App Router) with **TypeScript**.
2. Use a modern styling approach:
   - Prefer Tailwind CSS or CSS Modules + a simple design system of your own.
   - If you choose Tailwind, set it up properly (postcss, config, etc.).
3. Use **fetch** (or `axios`) on the client side to call the backend.
   - For file uploads, use `FormData` and `fetch` with `multipart/form-data`.
4. Keep the app mostly **client‑side** rendered (since it deals with user image uploads).

#### Project initialization (what you should generate)

Assume Node.js is installed. You should generate commands like:

```bash
npx create-next-app@latest know-your-skin-frontend \
  --typescript \
  --eslint \
  --src-dir \
  --app \
  --use-npm \
  --import-alias "@/*"
```

Then, if you choose Tailwind CSS:

```bash
cd know-your-skin-frontend
npx tailwindcss init -p
```

Configure `tailwind.config.js` for the `app` directory and set a base color palette (soft pastel colors).

Create a main page at `app/page.tsx` that contains the entire flow described above.

You may define additional components under `app/components/` or `src/components/` (depending on how you configure the project) such as:

- `components/ImageUploader.tsx`
- `components/AnalysisResults.tsx`
- `components/DeepAnalysisPanel.tsx`
- `components/RoutineSection.tsx`
- `components/LoadingOverlay.tsx`
- `components/ErrorAlert.tsx`

Use TypeScript types/interfaces for the API responses, e.g.:

```ts
interface FitzpatrickSection {
  label: string;
  label_mode: "single" | "range" | "unknown";
  labels: string[];
  title: string;
  overview: string;
  care_focus: string;
  probs: Record<string, number>;
}

interface MonkToneSection {
  label: number;
  group_name: string;
  education: string;
  probs: Record<string, number>;
}

interface CosmeticResponse {
  summary: string;
  tone_section: {
    fitzpatrick?: FitzpatrickSection;
    monk_tone?: MonkToneSection;
  };
  texture_section?: {
    items?: {
      tag: string;
      title: string;
      body: string;
      prob: number;
    }[];
  };
  disclaimer: string;
}

interface ConcernSection {
  tag: string;
  title: string;
  body: string;
  prob: number;
  scin_labels?: string[];
}

interface RoutineStepItem {
  id: string;
  name: string;
  step: string;
  image_name: string | null;
  why: string;
}

interface Routine {
  concerns: [string, number][];
  steps: Record<string, RoutineStepItem[]>;
}

interface ConcernsResponse {
  summary: string;
  concern_sections: ConcernSection[];
  routine: Routine;
  disclaimer: string;
}

interface AnalyzeResponse {
  cosmetic: CosmeticResponse;
  concerns: ConcernsResponse;
}

interface ConditionMetrics {
  precision?: number;
  recall?: number;
  f1?: number;
  support?: number;
}

interface ConditionReliability {
  level: "high" | "medium" | "low" | "unknown";
  text: string;
}

interface ConditionEntry {
  prob: number;
  active: boolean;
  metrics?: ConditionMetrics;
  reliability?: ConditionReliability;
}

interface DeepAnalysisResponse {
  conditions: Record<string, ConditionEntry>;
}
```

Use these interfaces to strongly type your components and API Hooks.

---

### Frontend configuration & environment variables

You must support configuration of the backend base URL via env vars, so that:

- Locally, the developer can set the VM IP (or use an SSH tunnel).
- On Vercel, they can set a more secure/clean URL (e.g. behind a load balancer).

Implement the following:

1. In the frontend code, read the base URL from:
   - `process.env.NEXT_PUBLIC_API_BASE_URL`
2. Provide a small helper, e.g.:

```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
```

3. Use that to construct fetch URLs:

```ts
await fetch(`${API_BASE_URL}/analyze`, { ... });
```

4. In documentation (README and comments), specify:
   - For local dev (direct VM call):
     - `NEXT_PUBLIC_API_BASE_URL=http://34.9.129.107:8000`
   - For SSH tunnel:
     - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

---

### Vercel deployment instructions (what you should output)

You must include clear instructions for the user to deploy this project to Vercel, for free. Assume they have a GitHub account and Vercel account.

The instructions should be something like:

1. Push the Next.js frontend repo to GitHub (e.g., `know-your-skin-frontend`).
2. Go to [Vercel](https://vercel.com), import the GitHub project.
3. During setup:
   - Framework: “Next.js”
   - Root directory: (default, if L1 of repo).
   - Environment variable:
     - `NEXT_PUBLIC_API_BASE_URL` → `http://34.9.129.107:8000` (or your load balancer URL).
4. Click “Deploy”.
5. After deployment:
   - Visit the Vercel URL (e.g., `https://know-your-skin-frontend.vercel.app`).
   - Upload 1–3 images and verify `/analyze` and `/analyze_session` work end‑to‑end.
   - Click “Deep analysis” and confirm `/deep_analysis` results appear.

Also include instructions for local dev:

```bash
cd know-your-skin-frontend
npm install

echo "NEXT_PUBLIC_API_BASE_URL=http://34.9.129.107:8000" > .env.local

npm run dev
```

Then open `http://localhost:3000` in the browser.

---

### Summary of your tasks

1. **Scaffold a new Next.js 14+ + TypeScript project** (App Router).
2. **Set up styling** (e.g. Tailwind) with a soft, skin‑care‑friendly palette.
3. **Implement the full UI flow**:
   - Image upload (1–3 images).
   - “Analyse my Skin” (calls `/analyze` or `/analyze_session`).
   - “Deep analysis” (calls `/deep_analysis`).
   - Display results in the specific sequence:
     1. Cosmetic overview.
     2. Fitzpatrick.
     3. Monk tone.
     4. Texture.
     5. Concerns.
     6. Routine.
     7. Disclaimers.
4. **Handle loading, errors, and reset** gracefully.
5. **Configure API base URL via `NEXT_PUBLIC_API_BASE_URL`**.
6. **Document Vercel deployment steps** and local dev commands clearly.

Generate all necessary files and code so that the user can:

1. Create the project with your given commands.
2. Copy your file contents into the new repo.
3. Run `npm run dev` locally.
4. Deploy to Vercel and immediately start using the app against the live backend.


