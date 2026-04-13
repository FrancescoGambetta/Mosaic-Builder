# 🚀 GitHub Setup Instructions

Step-by-step guide to publish your Mosaic Builder project on GitHub.

## 📋 Prerequisites

1. **GitHub Account**: Create one at [github.com](https://github.com) if you don't have one
2. **Git Installed**: Download from [git-scm.com](https://git-scm.com/)

Check if Git is installed:
```bash
git --version
```

## 🔧 Step 1: Configure Git (First Time Only)

Set your name and email:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 📦 Step 2: Create Repository on GitHub

1. Go to [github.com](https://github.com)
2. Click the **"+"** button in the top-right corner
3. Select **"New repository"**
4. Fill in:
   - **Repository name**: `mosaic-builder` (or your preferred name)
   - **Description**: "Automatic image stitching tool with EXIF-based ordering"
   - **Public** ✅ (check this)
   - **DO NOT** check "Add a README file" (we already have one)
   - **DO NOT** check "Add .gitignore" (we already have one)
   - **License**: Choose "MIT License" or skip (we already have one)
5. Click **"Create repository"**

## 💻 Step 3: Initialize Local Repository

Open terminal/command prompt in your project folder and run:

```bash
# Navigate to your project folder
cd /path/to/mosaic-builder

# Initialize Git repository
git init

# Add all files to staging
git add .

# Create first commit
git commit -m "Initial commit: Mosaic Builder v1.0"
```

## 🔗 Step 4: Link to GitHub

GitHub will show you commands after creating the repo. Use these:

```bash
# Link to your GitHub repository (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/mosaic-builder.git

# Push your code to GitHub
git branch -M main
git push -u origin main
```

**Replace** `YOUR_USERNAME` with your actual GitHub username!

## ✅ Step 5: Verify

1. Go to `https://github.com/YOUR_USERNAME/mosaic-builder`
2. You should see all your files:
   - ✅ Mosaic_builder.py
   - ✅ README.md
   - ✅ requirements.txt
   - ✅ LICENSE
   - ✅ .gitignore

## 🎨 Step 6: Customize (Optional)

### Edit README
Replace `[Your Name]` in LICENSE file:
```bash
# Edit LICENSE file and replace [Your Name] with your actual name
```

Replace `yourusername` in README.md:
```bash
# Edit README.md
# Change: https://github.com/yourusername/mosaic-builder.git
# To: https://github.com/YOUR_ACTUAL_USERNAME/mosaic-builder.git
```

Commit changes:
```bash
git add LICENSE README.md
git commit -m "Update author information"
git push
```

### Add Topics (Tags)
On GitHub repository page:
1. Click ⚙️ (gear icon) next to "About"
2. Add topics: `python`, `opencv`, `panorama`, `image-stitching`, `computer-vision`
3. Click "Save changes"

## 📸 Step 7: Add Example Images (Optional)

Create example images to show in README:

```bash
# Create examples folder
mkdir examples

# Add example images showing before/after
# Then update .gitignore to allow example images
```

Update README.md with screenshots:
```markdown
## 🖼️ Examples

### Before
![Input Images](examples/input_preview.jpg)

### After
![Mosaic Result](examples/output_mosaic.png)
```

## 🔄 Future Updates

When you make changes:

```bash
# Check what changed
git status

# Add changed files
git add .

# Commit with descriptive message
git commit -m "Add feature: custom output resolution"

# Push to GitHub
git push
```

## 🌟 Make it Popular

1. **Add a description**: On GitHub, add a short description under repository name
2. **Add topics**: Tag with relevant keywords
3. **Star your own repo**: Why not? 😄
4. **Share**: Share on social media, Reddit (r/Python, r/opencv), etc.

## 🆘 Troubleshooting

### "Permission denied"
Use SSH or Personal Access Token:
```bash
# Generate token at: https://github.com/settings/tokens
# Then use:
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/mosaic-builder.git
```

### "Already exists"
If repository already exists locally:
```bash
# Remove old remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR_USERNAME/mosaic-builder.git
```

## 🎉 Done!

Your project is now live on GitHub! 🚀

Share the link: `https://github.com/YOUR_USERNAME/mosaic-builder`

---

Need help? Open an issue on GitHub or check [GitHub Docs](https://docs.github.com/)
