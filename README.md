# Circuit Lab

**An interactive series RLC circuit simulator that shows the same circuit two ways at once — as a physical thing that rings and settles, and as the linear-algebra system that predicts it — with a built-in AI tutor, Jarvis, grounded in whatever you're looking at right now.**

Built for a Computer Science IA exploring the connection between linear algebra and electrical engineering. One HTML file, zero build step, real math solved live in the browser on every slider movement.

🔗 **Live circuit:** [`main.html`](main.html) — open it directly in any browser, no server required.
🤖 **Jarvis (optional):** a small local backend that adds an AI tutor drawer — see [`tutor-backend/`](tutor-backend/).

---

## What it does

Circuit Lab simulates a series **R-L-C** circuit — a resistor, inductor, and capacitor in a loop — and lets you flip between two ways of looking at it:

- **DC step response (transient):** flip the switch and watch the capacitor voltage and loop current evolve from the moment power is applied, exactly as governed by the circuit's differential equation.
- **AC steady state:** drive the same circuit with a sine wave and watch current and voltage settle into a steady phase relationship, governed by complex impedance instead.

Everything on the page — every trace, eigenvalue, matrix entry, and phasor — is computed live from whatever `R`, `L`, `C`, and `f` you currently have set. Nothing is precomputed or looked up from a table.

### Features

- **Live schematic** — an SVG resistor/inductor/capacitor/source loop that redraws its labels as you move the sliders, with a distinct DC (battery + switch) and AC (sine source) variant.
- **Oscilloscope panel** — canvas-rendered $v_C(t)$ and $i(t)$ traces with real labelled time/amplitude axes, gridlines, and a colour-swatched legend that stays legible even where the trace passes directly under it.
- **Phase-plane panel**, which changes meaning with the mode:
  - *DC mode* — plots the two eigenvalues $\lambda_1, \lambda_2$ of the system on the complex plane, labelled, so it's visually obvious whether they're real (no ringing) or a complex-conjugate pair (ringing).
  - *AC mode* — an annotated, rotating **phasor diagram**: $V$, $I$, $V_R$, $V_L$, and $V_C$ are drawn as individually labelled vectors, sized so $V_R + V_L + V_C$ visibly reconstructs $V$, exactly as Kirchhoff's voltage law demands.
- **Live frequency response (Bode) plot** — $|Z(f)|$ and $\angle Z(f)$ against a log frequency axis, with a moving marker locked to the drive frequency (or the natural frequency in DC mode) so resonance is something you *see* happen, not just a number.
- **System matrix panel** — the literal $2\times2$ state matrix

$$
A = \begin{bmatrix} -R/L & -1/L \\ 1/C & 0 \end{bmatrix}
$$

  rendered with real numbers plugged in, right next to the eigenvalues it produces, plus the damping ratio $\zeta$ and quality factor $Q$ — so the linear algebra and the physics are never more than one glance apart.
- **Precise, huge-range controls** — every parameter (R, L, C, drive frequency) has both a logarithmically-scaled slider (so a single drag sweeps orders of magnitude smoothly) and an editable number field for exact values.
- **Light/dark theme**, matching the OS by default, with a contrast pass on all explanatory text.
- **Jarvis**, an AI tutor scoped entirely to this circuit (see below).

---

## The math and science

### 1. The circuit is a linear system

Kirchhoff's voltage law around a series RLC loop gives a second-order ODE in the capacitor voltage. Written as a first-order system in the state vector $x = [i, \, v_C]^\top$ (loop current, capacitor voltage), it becomes:

$$
\frac{dx}{dt} = Ax, \qquad A = \begin{bmatrix} -R/L & -1/L \\ 1/C & 0 \end{bmatrix}
$$

This is the same $A$ the app renders live. Its **eigenvalues** are the whole story for the DC step response:

$$
\lambda_{1,2} = -\alpha \pm \sqrt{\alpha^2 - \omega_0^2}, \qquad \alpha = \frac{R}{2L}, \qquad \omega_0 = \frac{1}{\sqrt{LC}}
$$

- If $\alpha > \omega_0$ (real, distinct roots): **overdamped** — settles with no ringing.
- If $\alpha = \omega_0$ (repeated root): **critically damped** — fastest possible settle with no overshoot.
- If $\alpha < \omega_0$ (complex-conjugate pair): **underdamped** — rings at the damped frequency $\omega_d = \sqrt{\omega_0^2 - \alpha^2}$ while decaying as $e^{-\alpha t}$.

Two dimensionless numbers describe *how* underdamped a circuit is, and the app shows both:

$$
\zeta = \frac{\alpha}{\omega_0} \quad \text{(damping ratio)}, \qquad Q = \frac{1}{R}\sqrt{\frac{L}{C}} = \frac{1}{2\zeta} \quad \text{(quality factor)}
$$

### 2. The same circuit, driven steadily, is a complex-number problem

Under a sinusoidal drive at angular frequency $\omega = 2\pi f$, each component becomes a complex **impedance**:

$$
Z_R = R, \qquad Z_L = j\omega L, \qquad Z_C = \frac{1}{j\omega C}, \qquad Z = Z_R + Z_L + Z_C
$$

Current is $I = V/Z$ (a phasor — complex amplitude and phase), and each component's voltage is $V_R = IZ_R$, $V_L = IZ_L$, $V_C = IZ_C$. By KVL these voltage phasors sum vectorially back to $V$ — which is exactly what the phasor diagram draws.

### 3. Where the two views meet

Both views agree on one special frequency, the **resonant/natural frequency**:

$$
\omega_0 = \frac{1}{\sqrt{LC}}
$$

At this frequency the inductive and capacitive reactances cancel, $Z$ is purely resistive, and current and voltage fall into phase — the point the Bode plot's marker is built to highlight, and the same $\omega_0$ that sits inside the DC-mode eigenvalues.

---

## Jarvis — the AI tutor

Jarvis is a slide-over chat drawer, scoped entirely to this circuit — it won't discuss anything outside RLC circuits, damping, resonance, impedance, eigenvalues, or the matrix behind them.

**Jarvis is not a custom-trained or fine-tuned model.** It's a general-purpose LLM (`openai/gpt-oss-120b`, served via [Groq](https://groq.com)'s fast inference API) wrapped in three layers that give it its "expertise":

1. **A fixed persona + scope**, set entirely by a system prompt ([`tutor-backend/prompts.py`](tutor-backend/prompts.py)) — this is what keeps Jarvis a circuit tutor instead of a general chatbot.
2. **Live context grounding** — every single message sends Jarvis the *exact* current state of your circuit (mode, R/L/C/f, regime, eigenvalues, the matrix $A$, quality factor $Q$) as structured JSON, so its explanations are about the circuit actually on your screen, not a generic textbook example.
3. **A two-layer safety pipeline** ([`tutor-backend/circuit_breaker.py`](tutor-backend/circuit_breaker.py), adapted from the same pattern used in a sister project, [duckpath's AdvisorPath](https://github.com/aliabbaka/duckpath/tree/advisorpath-integration)):
   - **Input screening** blocks prompt-injection attempts, unsafe requests, and anything with no plausible connection to the circuit lab, before it ever reaches the model.
   - **Output validation** parses anything Jarvis proposes to change on the live circuit, clamps every value to the sliders' real physical ranges, and drops anything malformed — so the model can never push the page into an invalid state.

**Jarvis can show, not just tell.** If a live demonstration would help ("what does critical damping look like?"), Jarvis ends its reply with a small structured action; once validated server-side, the front end smoothly animates R/L/C/f to that regime on screen, with a one-click "reset my values" to restore whatever you had before.

Replies stream token-by-token and render Markdown; any LaTeX-ish math Jarvis writes ($\frac{}{}$, $\sqrt{}$, `^{}`, `_{}`, $\Omega$, $\times$, …) is converted client-side into real symbols and superscript/subscript text — no external math renderer, and nothing that can silently fail to load.

---

## Tech stack

| Layer | Tech |
|---|---|
| Circuit simulator | Vanilla HTML5, CSS3 (custom properties, `prefers-color-scheme` dark mode), JavaScript (Canvas API for the scope/plane/Bode plots, inline SVG for the schematic) |
| Jarvis backend | Python, Flask, Flask-CORS, streamed HTTP responses |
| AI | [Groq](https://groq.com) API (`groq` Python SDK), `openai/gpt-oss-120b` |
| Config | `python-dotenv` |

No build step, no framework, no bundler — `main.html` runs by itself in any modern browser.

---

## Running it

### Just the simulator

Open [`main.html`](main.html) directly in a browser. That's it — every visualization, all the math, and the sliders work with no backend at all.

### With Jarvis

```bash
cd tutor-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add a Groq API key from https://console.groq.com
python3 app.py
```

The backend listens on `http://localhost:5001`; `main.html`'s "Ask Jarvis" button already points there. See [`tutor-backend/README.md`](tutor-backend/README.md) for details on the API contract and the safety pipeline.

---

## Project structure

```
main.html               the entire simulator — markup, styles, and all simulation/render logic
tutor-backend/
  app.py                Flask app, the /api/tutor/chat streaming endpoint
  agents.py             Groq client wrapper (lazy client, streaming completion)
  prompts.py            Jarvis's system prompt, built fresh per-request from live circuit state
  circuit_breaker.py    input screening + output validation (the safety layer)
  requirements.txt
```

---

## Credits

Built by [Ali Abbaka](https://github.com/aliabbaka) — [LinkedIn](https://www.linkedin.com/in/aliabbaka/) 
