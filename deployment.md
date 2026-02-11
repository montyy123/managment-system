# 🚀 NexGen Deployment Guide (Railway / Runway)

This guide provides step-by-step instructions on how to take your **NexGen Event Management System** from your local machine to the cloud using **Railway.app** (often referred to for its "Runway" speed and ease of deployment).

---

## 🛠️ Step 1: Preparation

Ensure the following files are in your root directory (we have already created these for you):
1.  **`app.py`**: Your main application logic.
2.  **`requirements.txt`**: List of Python dependencies (Flask, SQLAlchemy, Gunicorn).
3.  **`Procfile`**: Tells the cloud server how to start your app (`web: gunicorn app:app`).
4.  **`static/` & `templates/`**: Your frontend assets and cinematic UI.

---

## ☁️ Step 2: Deploying to Railway (Recommended)

Railway is the most robust and "low-code" platform for Flask deployment.

### 1. **Initialize Git**
Your project must be a Git repository.
```bash
git init
git add .
git commit -m "Initial NexGen Cluster"
```

### 2. **Connect to GitHub**
1. Create a new repository on [GitHub](https://github.com/new).
2. Push your code:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```

### 3. **Launch on Railway**
1. Go to [Railway.app](https://railway.app) and log in with GitHub.
2. Click **+ New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Railway will automatically detect the **Procfile** and **requirements.txt** and start the build process.

---

## 🔐 Step 3: Environment Variables

Once deployed, you should secure your application:
1. Go to the **Variables** tab on your Railway project.
2. Add a new variable:
   - **Key**: `SECRET_KEY`
   - **Value**: `a-very-long-and-secure-random-string` (This overrides the default in `app.py`).

---

## 📊 Step 4: Database Persistence

By default, the system uses `sqlite:///event_system.db`. 
- **Note**: On most cloud platforms, SQLite files are reset when the app restarts.
- **Solution**: For a permanent database, you can spin up a **PostgreSQL** instance on Railway with one click and update your `SQLALCHEMY_DATABASE_URI` in the environment variables.

---

## 🌟 Verification

After the build is complete (usually takes 1-2 minutes):
1. Click the provided **Railway URL** (e.g., `nexgen-sys-production.up.railway.app`).
2. Verify the **Secure Access** login screen appears.
3. Test a member provisioning to ensure the database is operational.

---

**NexGen v1.0** - Cloud Optimized & Ready for Scale.
