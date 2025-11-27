
AIR MINDMAP

Hand-gesture driven: create, connect, and organize thoughts in a real-time gesture-driven mind map.

A gesture-driven, real-time mind-map generator using webcam input and MediaPipe Hands.

Features:
- Live webcam feed with hand tracking (MediaPipe Hands).
- Gesture vocabulary (point, circle, two-hand stretch, pinch, tap).
- Real-time creation, connection, expansion, collapse and selection of nodes.
- Visual feedback: fingertip neon indicator, trails, animations.
- Demo mode to simulate gestures.
- Save/load mindmap JSON and export snapshot PNG.

Author: TUBA KHAN

Quick start:
Getting started (after forking)
1. Fork the repository on GitHub and clone it locally:

```bash
git clone https://github.com/<your-username>/Tuba_Khan_MindMap.git
cd Tuba_Khan_MindMap
```

2. Create and activate a Python virtual environment (PowerShell example):

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

3. Install required packages:

```powershell
pip install -r requirements.txt
```

4. Run the app (PowerShell):

```powershell
python .\main.py
```

Notes:
- If your webcam is not the default device, edit `config.yaml` and set `camera_index`.
- Use the right-hand panel or the on-screen instructions for gesture shortcuts.

Owner & Creator
- @tubakhxn (Tuba Khan)

License
- This project is released under the MIT License. See the `LICENSE` file for full terms.

See also: `run_instructions.txt` for platform-specific tips and troubleshooting.
