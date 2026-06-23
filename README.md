# RiceScan AI — Rice Leaf Disease Detector

A complete website that uploads a rice leaf photo and predicts the disease
(Bacterial Blight, Blast, Brown Spot, or Tungro) using your trained
MobileNetV2 model (99.9% accuracy).

## How it works

```
[ Your browser ]  --upload photo-->  [ Frontend website ]
                                            |
                                     sends image via API call
                                            v
                                   [ Backend API (FastAPI) ]
                                            |
                                   loads mobilenet_rice.h5
                                   runs prediction
                                            v
                                   returns disease + confidence
```

Two separate pieces, because Vercel/Netlify host static websites — they
cannot run a TensorFlow model. So:
- **Frontend** (`frontend/index.html`) → deploy on Vercel or Netlify
- **Backend** (`backend/main.py`) → deploy on Render (free tier supports Python + TensorFlow)

---

## STEP 1 — Export your trained model from the notebook

Your notebook (the one linked from Colab/Kaggle) trains three models and
`mobilenet_model` is the winner at 99.9% accuracy. You need to save it to a file.

1. Open your notebook (Kaggle or Colab).
2. Add a new cell **after** the MobileNetV2 training cell with:
   ```python
   mobilenet_model.save("mobilenet_rice.h5")
   ```
3. Download the resulting `mobilenet_rice.h5` file:
   - **Kaggle**: appears in the Output panel on the right after running the cell.
   - **Colab**: run `from google.colab import files; files.download("mobilenet_rice.h5")`
4. Full instructions are also in `backend/EXPORT_MODEL_FROM_NOTEBOOK.txt`.

---

## STEP 2 — Set up the project folder on your computer

You should have this structure (already created for you):

```
rice-disease-detector/
├── frontend/
│   └── index.html          <- the website
├── backend/
│   ├── main.py              <- API server
│   ├── requirements.txt
│   └── model/
│       └── mobilenet_rice.h5   <- PUT YOUR DOWNLOADED MODEL HERE
├── render.yaml
└── vercel.json
```

Copy your downloaded `mobilenet_rice.h5` into `backend/model/`.

---

## STEP 3 — Test the backend locally (recommended before deploying)

```bash
cd rice-disease-detector/backend
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Visit `http://localhost:8000` in your browser — you should see:
```json
{"status": "running", "message": "RiceScan AI API is live", "model_loaded": true}
```

If `model_loaded` is `false`, double check the `.h5` file is at
`backend/model/mobilenet_rice.h5`.

Test a prediction with curl:
```bash
curl -X POST http://localhost:8000/predict -F "file=@/path/to/leaf.jpg"
```

---

## STEP 4 — Push the project to GitHub

Both Render and Vercel deploy from a GitHub repo.

```bash
cd rice-disease-detector
git init
git add .
git commit -m "Rice leaf disease detector"
```

Create a new repo on https://github.com/new, then:
```bash
git remote add origin https://github.com/YOUR-USERNAME/rice-disease-detector.git
git branch -M main
git push -u origin main
```

**Important**: `.h5` model files can be large. If yours is over 100MB, GitHub
will reject the push. Use [Git LFS](https://git-lfs.github.com/) in that case:
```bash
git lfs install
git lfs track "*.h5"
git add .gitattributes
git add backend/model/mobilenet_rice.h5
git commit -m "Add model via LFS"
git push
```

---

## STEP 5 — Deploy the backend on Render

1. Go to https://render.com and sign up / log in (free, no card needed for free tier).
2. Click **New +** → **Web Service**.
3. Connect your GitHub account and select the `rice-disease-detector` repo.
4. Render should auto-detect `render.yaml` — if not, set manually:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Click **Create Web Service**. First build takes 3–5 minutes (TensorFlow is large).
6. Once live, copy your API URL — it looks like:
   ```
   https://ricescan-api.onrender.com
   ```
7. Test it: open that URL in a browser, confirm `model_loaded: true`.

**Note on the free tier**: Render's free instances sleep after 15 minutes of
inactivity and take ~30–60 seconds to wake on the next request. That's normal
— your first prediction after idle time will just be slower.

---

## STEP 6 — Connect frontend to backend

Open `frontend/index.html` is already built to ask for the API URL in the UI
itself — no code edit needed. But if you'd rather hardcode it so users don't
have to paste it:

Open `frontend/index.html`, find this line near the bottom:
```js
let apiBaseUrl = localStorage.getItem('ricescan_api_url') || '';
```
Replace `''` with your Render URL:
```js
let apiBaseUrl = localStorage.getItem('ricescan_api_url') || 'https://ricescan-api.onrender.com';
```

---

## STEP 7 — Deploy the frontend on Vercel

**Option A — Vercel website (easiest)**
1. Go to https://vercel.com and sign up / log in with GitHub.
2. Click **Add New** → **Project**.
3. Import your `rice-disease-detector` repo.
4. Vercel reads `vercel.json` automatically — output directory is `frontend`.
5. Click **Deploy**. Done in under a minute.
6. You'll get a live URL like `https://rice-disease-detector.vercel.app`.

**Option B — Vercel CLI**
```bash
npm install -g vercel
cd rice-disease-detector
vercel login
vercel --prod
```

### Or deploy on Netlify instead
1. Go to https://app.netlify.com → **Add new site** → **Import an existing project**.
2. Connect GitHub, pick your repo.
3. Set **Base directory**: `frontend`, **Publish directory**: `frontend`.
4. Deploy.

---

## STEP 8 — Update CORS on the backend (production hardening)

Right now `backend/main.py` allows requests from any website
(`allow_origins=["*"]`). Once your frontend is live, lock it down:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-actual-site.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Commit and push — Render auto-redeploys on every push to `main`.

---

## STEP 9 — Use your live website

1. Visit your Vercel/Netlify URL.
2. If you didn't hardcode the API URL in Step 6, paste your Render URL into
   the "Backend API setup" box at the top of the detector and click **Save**.
3. Upload a rice leaf photo.
4. Click **Analyze Disease**.
5. See the predicted disease, confidence score, description, and treatment.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Model not loaded" error | `.h5` file isn't in `backend/model/` on the deployed server — check it was committed/pushed (and uses Git LFS if large) |
| CORS error in browser console | Backend `allow_origins` doesn't include your frontend's domain |
| Prediction is slow first time | Normal — Render free tier sleeps after inactivity, takes ~30-60s to wake |
| Wrong predictions / random results | Class order mismatch — confirm `CLASS_NAMES` in `main.py` matches the alphabetical folder order Keras used: `Bacterialblight, Blast, Brownspot, Tungro` |
| Build fails on Render (TensorFlow too big) | Already using `tensorflow-cpu` in requirements.txt to keep image smaller; if it still fails, consider Render's paid tier or switch to a smaller model export (TFLite) |

---

## Optional upgrade: convert to TFLite for faster, lighter deployment

If Render's free tier struggles with full TensorFlow, convert your model to
TensorFlow Lite (much smaller, faster) — add this to your notebook:

```python
converter = tf.lite.TFLiteConverter.from_keras_model(mobilenet_model)
tflite_model = converter.convert()
with open("mobilenet_rice.tflite", "wb") as f:
    f.write(tflite_model)
```

Then swap `tensorflow-cpu` for `tflite-runtime` in `requirements.txt` and
update `main.py` to use the TFLite interpreter API instead of
`tf.keras.models.load_model`. Ask me if you want this version built out.
