# Intellectual Property Portfolio Strategist

A multi-agent AI system built with CrewAI for comprehensive IP strategy analysis.

LIVE AT: https://ip-portfolio-strategist-3.onrender.com/

## Features

- **5 Specialized AI Agents**:
  - Patent Landscape Analyzer
  - Trademark Conflict Detector
  - IP Valuation Estimator
  - Filing Strategy Optimizer
  - Competitor IP Monitor

- **Modern Web Interface**: Clean, professional design with real-time chat
- **Production Ready**: Deployable to Render.com with proper configuration
- **OpenAI Integration**: Powered by GPT-4 for sophisticated analysis

## Deployment

### Render.com Deployment

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
5. Deploy!

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Windows (Prerequisites & Troubleshooting)

If you see an error like "Microsoft Visual C++ 14.0 or greater is required" when installing dependencies, it's because some Python packages (for example `hnswlib` used by some vector DB backends) require compiling C extensions on Windows.

Options to resolve:

- Install Microsoft C++ Build Tools (recommended):

   1. Download/Install from the official page: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   2. Or install via winget (Windows 10/11):

   ```powershell
   winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget
   ```

   Make sure to select the "C++ build tools" workload during installation.

- Alternative: Use conda (avoids compiling extensions)

   ```bash
   conda create -n ip python=3.11 -y
   conda activate ip
   conda install -c conda-forge hnswlib -y
   pip install -r requirements.txt
   ```

After installing the build tools or the conda package, re-open your shell and re-run:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
